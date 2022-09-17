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

from datetime import datetime
import docker
from prometheus_client import start_http_server, Counter
import os
import platform

APP_NAME = "Docker events prometheus exporter"
EVENTS = Counter('docker_events_container',
                 'Docker events Container',
                 ['status', 'docker_hostname', 'image', 'container_id', 'container_name'])
PROMETHEUS_EXPORT_PORT = int(os.getenv('PROMETHEUS_EXPORT_PORT', '9000'))
DOCKER_HOSTNAME = os.getenv('DOCKER_HOSTNAME', platform.node())


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
                EVENTS.labels(
                    **{
                        'status': event['status'],
                        'docker_hostname': DOCKER_HOSTNAME,
                        'image': event['from'],
                        'container_id': event['Actor']['ID'],
                        'container_name': event['Actor']['Attributes']['name']
                    }).inc()
    finally:
        client.close()


if __name__ == '__main__':
    print_timed(f'Start prometheus client on port {PROMETHEUS_EXPORT_PORT}')
    start_http_server(PROMETHEUS_EXPORT_PORT, addr='0.0.0.0')
    try:
        print_timed('Watch docker events')
        watch_events()
    except docker.errors.APIError:
        pass
