# Docker engine events exporter (Docker Engine/Swarm)

![](https://img.shields.io/docker/pulls/neuroforgede/docker-engine-events-exporter.svg)

*Docker engine events exporter* expose docker API events ([oom, start, …](https://docs.docker.com/engine/reference/commandline/events/#object-types)) to prometheus metrics.

This is a fork of [sbadia/docker-events-exporter](https://github.com/sbadia/docker-events-exporter) with a focus on usage in a Docker/Docker Swarm environment without Kubernetes.

Proudly made by [NeuroForge](https://neuroforge.de/) in Bayreuth, Germany.

## Use in a Docker Swarm deployment

Deploy:

```yaml
version: "3.8"

services:
  docker-engine-events-exporter:
    image: neuroforgede/docker-engine-events-exporter:0.1
    networks:
      - net
    environment:
      - DOCKER_HOSTNAME={{.Node.Hostname}}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    deploy:
      mode: global
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
```

prometheus.yml

```yaml
# ...
scrape_configs:
  - job_name: 'docker-engine-events-exporter'
    dns_sd_configs:
    - names:
      - 'tasks.docker-engine-events-exporter'
      type: 'A'
      port: 9000
```

A monitoring solution based on the original swarmprom that includes this can be found at our [Swarmsible repo](https://github.com/neuroforgede/swarmsible/tree/master/environments/test/test-swarm/stacks/02_monitoring)

## Prometheus alerts ?

Then you can imagine to configure prometheus alerts based on thoses metrics,
for example about containers with bad exit codes:

```yaml
  - alert: Container (Swarm) died/is dying with exit code other than 0
    expr: count by (container_attributes_com_docker_swarm_service_name, container_attributes_exitcode, status) (
          (
              docker_events_container_total{status=~"die|.*oom.*|.*kill.*", container_attributes_exitcode != "0", container_attributes_exitcode != "" } 
              unless 
              docker_events_container_total{status=~"die|.*oom.*|.*kill.*", container_attributes_exitcode != "0", container_attributes_exitcode != "" }
              offset 10m
          ) OR (
              increase(docker_events_container_total{status=~"die|.*oom.*|.*kill.*", container_attributes_exitcode != "0", container_attributes_exitcode != "" }[10m]) > 0
          )
      )
    annotations:
      summary: "Bad Exit code \"{{ $labels.container_attributes_exitcode }}\" for status \"{{ $labels.status }}\" for service \"{{ $labels.container_attributes_com_docker_swarm_service_name }}\""
```
