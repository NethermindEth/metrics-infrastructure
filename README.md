# [Nethermind Metrics Docs](https://docs.nethermind.io/nethermind/ethereum-client/metrics/setting-up-local-metrics-infrastracture)

A self-hosted, local monitoring stack for a Nethermind node. A single
[Grafana Alloy](https://grafana.com/docs/alloy/latest/) agent collects both
**metrics** and **logs** from your node and ships them to a local backend:

- **Alloy** scrapes the node's Prometheus metrics endpoint and reads its
  container logs.
- **Prometheus** stores the metrics.
- **Loki** stores the logs.
- **Grafana** visualizes both.

## Requirements

* Nethermind `v1.26.0` or later.
* Docker with Docker Compose plugin installed. ([Installation Guide](https://docs.docker.com/desktop/))

## Quick Guide

1. Clone this repository and move into the project folder.
2. (Optional) Open the [Grafana config file](grafana/config.ini) and edit the
   admin username and password for additional security.
3. Configure Nethermind to **expose** a metrics endpoint (this replaces the old
   PushGateway setup). Launch it with the flags:

   ```
   --Metrics.Enabled=true --Metrics.ExposePort=8008
   ```

   or the equivalent environment variables:

   ```
   NETHERMIND_METRICSCONFIG_ENABLED=true
   NETHERMIND_METRICSCONFIG_EXPOSEPORT=8008
   ```

4. Create your environment file and set your node's container name:

   ```
   cp env.example .env
   ```

   Edit `.env` and set `EXECUTION_CONTAINER_NAME` to the name of your Nethermind
   container (and `NETHERMIND_METRICS_ADDRESS` if your node is not reachable at
   the default `host.docker.internal:8008`). See
   [Node runtime scenarios](#node-runtime-scenarios) below.
5. Execute `docker compose up -d`.
6. Open your local [Grafana](http://localhost:3000) in your browser and log in
   with your configured username and password. Metrics appear on the Nethermind
   dashboard; logs are available under **Explore → Loki**.

## Node runtime scenarios

Alloy needs two things from your node: a reachable **metrics endpoint** and a
source of **logs**. The defaults target the most common case; adjust `.env` (and,
for logs from a non-Docker node, `alloy/config.alloy`) as needed.

### A. Node runs as a Docker container on the same host (default)

No changes needed beyond `EXECUTION_CONTAINER_NAME`:

- **Metrics**: Alloy scrapes `host.docker.internal:8008` (the exposed metrics
  port on the host).
- **Logs**: Alloy discovers the container through the mounted Docker socket and
  reads its stdout.

### B. Node runs as a bare process / systemd service on the same host

- **Metrics**: still work via `host.docker.internal:8008` — no change.
- **Logs**: the Docker socket won't find a non-Docker process. In
  `alloy/config.alloy`, comment out the `discovery.docker` and
  `loki.source.docker` blocks and enable the commented `local.file_match` /
  `loki.source.file` blocks at the bottom of the file, then set
  `NETHERMIND_LOG_PATH` to your node's log file(s).

### C. Node runs on a remote / different host

- **Metrics**: set `NETHERMIND_METRICS_ADDRESS=<node-ip>:8008` in `.env`. Make
  sure that port is reachable and firewalled appropriately.
- **Logs**: Docker-socket log collection does not work across hosts. Either run
  Alloy on the node itself for logs, or accept a metrics-only setup.

## Exposing services to other interfaces

By default all services are exposed only on the `localhost` (`127.0.0.1`)
interface. To expose them on another interface, edit `.env` and set the desired
interface per service (use `0.0.0.0` for all interfaces):

- `NETHERMIND_PROMETHEUS_HOST` — Prometheus interface.
- `NETHERMIND_GRAFANA_HOST` — Grafana interface.
- `NETHERMIND_LOKI_HOST` — Loki interface.
- `NETHERMIND_ALLOY_HOST` — Alloy UI interface.

Then run `docker compose up -d` again.

In case any of these interfaces are exposed to the internet (ie. using
`0.0.0.0`) be sure to restrict access to the services by using a firewall.
