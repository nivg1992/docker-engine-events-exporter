# Docker engine events exporter (Docker Engine/Swarm)

*Docker engine events exporter* expose docker API events ([oom, start, …](https://docs.docker.com/engine/reference/commandline/events/#object-types)) to prometheus metrics.

This is a fork of [sbadia/docker-events-exporter](https://github.com/sbadia/docker-events-exporter) with a focus on usage in a Docker/Docker Swarm environment without Kubernetes.

## Prometheus alerts ?

Then you can imagine to configure prometheus alerts based on thoses metrics,
for example about OOM events…

```
groups:
- name: host_health
  - alert: Container (Swarm) died/is dying with exit code other than 0
    expr: max by (status, container_attributes_com_docker_swarm_service_name, container_attributes_exitcode) (max_over_time(docker_events_container_total{status=~"die|.*oom.*|.*kill.*", container_attributes_exitcode != "0", container_attributes_exitcode != "" }[15m])) > 0
    annotations:
      summary: "Bad Exit code \"{{ $labels.container_attributes_exitcode }}\" for status \"{{ $labels.status }}\" for service \"{{ $labels.container_attributes_com_docker_swarm_service_name }}\""
```
