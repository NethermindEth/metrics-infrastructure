# [Nethermind Metrics Docs](https://docs.nethermind.io/nethermind/ethereum-client/metrics/setting-up-local-metrics-infrastracture)

## Requirements

* Nethermind `v1.26.0` or later.
* Docker with Docker Compose plugin installed. ([Installation Guide](https://docs.docker.com/desktop/))

## Quick Guide

1. Clone this repository and move into the project folder.
2. Open [Grafana config file](grafana/config.ini) and edit admin username and password for additional security.
3. Execute `docker compose up -d`.
4. Configure and launch Nethermind client with the following flag `--Metrics.PushGatewayUrl=http://localhost:9091` or use the environment variable `NETHERMIND_METRICSCONFIG_PUSHGATEWAYURL` set to `http://localhost:9091`.
5. Open your local [Grafana](http://localhost:3000) on your browser and login with your configured username and password.

### Additional

By default the monitoring services are only exposed to the `localhost`(`127.0.0.1`) interface. To expose these services to another interfaces follow these steps:

1. Create a copy of the `env.example` file named `.env`.
2. Edit the `.env` file and set the desired interface to be used for each service. Use `0.0.0.0` for all interfaces.
   * Change `NETHERMIND_PROMETHEUS_HOST` to update Prometheus interface.
   * Change `NETHERMIND_PUSHGATEWAY_HOST` to update Prometheus Pushgateway interface.
   * Change `NETHERMIND_GRAFANA_HOST` to update Grafana interface.
3. Execute `docker compose up -d`.

In case any of these interfaces are exposed to the internet(ie. using `0.0.0.0`) be sure to restrict access to the services by using a firewall.
