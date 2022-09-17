# Docker engine events exporter (Docker Engine/Swarm)

*Docker engine events exporter* expose docker API events ([oom, start, …](https://docs.docker.com/engine/reference/commandline/events/#object-types)) to prometheus metrics.

This is a fork of [sbadia/docker-events-exporter](https://github.com/sbadia/docker-events-exporter) with a focus on usage in a Docker/Docker Swarm environment without Kubernetes.

## Prometheus alerts ?

Then you can imagine to configure prometheus alerts based on thoses metrics,
for example about OOM events…

```
groups:
- name: host_health
  - alert: oom
    expr: rate(docker_events{event="oom",kubernetes_namespace="inf"}[1m]) > 0
    labels:
      routing: slackonly
    annotations:
      link: '{{ $labels.event }} - {{ $labels.env }} - {{ $labels.pod }}'
```
