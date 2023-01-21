#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Clustree <https://www.clustree.com> (Original Code for Kubernetes)
# Copyright 2022 NeuroForge GmbH & Co. KG <https://neuroforge.de>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime, timedelta
import docker
from prometheus_client import start_http_server, Counter
import os
import platform
import traceback
from time import sleep

APP_NAME = "Docker events prometheus exporter"
EVENTS = Counter('docker_events_container',
                 'Docker events Container',
                 [
                    'status',
                    'docker_hostname',
                    'image',
                    'container_id',
                    'container_attributes_name',
                    'container_attributes_exitcode',
                    'container_attributes_com_docker_stack_namespace',
                    'container_attributes_com_docker_swarm_node_id',
                    'container_attributes_com_docker_swarm_service_id',
                    'container_attributes_com_docker_swarm_service_name',
                    'container_attributes_com_docker_swarm_task',
                    'container_attributes_com_docker_swarm_task_id',
                    'container_attributes_com_docker_swarm_task_name',
                ])
PROMETHEUS_EXPORT_PORT = int(os.getenv('PROMETHEUS_EXPORT_PORT', '9000'))
DOCKER_HOSTNAME = os.getenv('DOCKER_HOSTNAME', platform.node())

RETRY_BACKOFF = int(os.getenv('RETRY_BACKOFF', '10'))
MAX_RETRIES_IN_ROW = int(os.getenv('MAX_RETRIES_IN_ROW', '10'))


def print_timed(msg):
    to_print = '{} [{}]: {}'.format(
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'docker_events',
        msg)
    print(to_print)


def watch_events():
    client = docker.DockerClient()
    try:
        for event in client.events(decode=True):
            if event['Type'] == 'container':
                # TODO: make it configurable which states to not export
                if event['status'].startswith(('exec_start', 'exec_create', 'exec_detach')):
                    # ignore exec_start, exec_create and exec_detach, these dont seem helpful
                    continue

                attributes = event['Actor']['Attributes']
                EVENTS.labels(
                    **{
                        'status': event['status'].strip(),
                        'docker_hostname': DOCKER_HOSTNAME,
                        'image': event.get('from', ''),
                        'container_id': event.get('Actor', {}).get('ID', ''),
                        'container_attributes_name': attributes.get('name', ''),
                        'container_attributes_exitcode': attributes.get('exitCode', ''),
                        'container_attributes_com_docker_stack_namespace': attributes.get('com.docker.stack.namespace', ''),
                        'container_attributes_com_docker_swarm_node_id': attributes.get('com.docker.swarm.node.id', ''),
                        'container_attributes_com_docker_swarm_service_id': attributes.get('com.docker.swarm.service.id', ''),
                        'container_attributes_com_docker_swarm_service_name': attributes.get('com.docker.swarm.service.name', ''),
                        'container_attributes_com_docker_swarm_task': attributes.get('com.docker.swarm.task', ''),
                        'container_attributes_com_docker_swarm_task_id': attributes.get('com.docker.swarm.task.id', ''),
                        'container_attributes_com_docker_swarm_task_name': attributes.get('com.docker.swarm.task.name', ''),
                    }).inc()
    finally:
        client.close()


if __name__ == '__main__':
    print_timed(f'Start prometheus client on port {PROMETHEUS_EXPORT_PORT}')
    start_http_server(PROMETHEUS_EXPORT_PORT, addr='0.0.0.0')
    while True:
        try:
            print_timed('Watch docker events')
            watch_events()
        except docker.errors.APIError:
            now = datetime.now()

            traceback.print_exc()

            last_failure = last_failure
            if last_failure < (now - timedelta.seconds(RETRY_BACKOFF * 10)):
                print_timed("detected docker APIError, but last error was a bit back, resetting failure count.")
                # last failure was a while back, reset
                failure_count = 0

            failure_count += 1
            if failure_count > MAX_RETRIES_IN_ROW:
                print_timed(f"failed {failure_count} in a row. exiting...")
                exit(1)

            last_failure = now
            print_timed(f"waiting {RETRY_BACKOFF} until next cycle")
            sleep(RETRY_BACKOFF)
