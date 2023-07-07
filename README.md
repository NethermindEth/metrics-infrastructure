# [Nethermind Metrics Docs](https://docs.nethermind.io/nethermind/ethereum-client/metrics/setting-up-local-metrics-infrastracture)

## Requirements

* Nethermind `v1.19.0` or later.
* Docker with Docker Compose plugin installed. ([Installation Guide](https://docs.docker.com/desktop/))

## Quick Guide

1. Clone this repository and change into the project folder.
2. Open [Grafana config file](grafana/config.ini) and edit admin username and password for additional security.
3. Execute `docker compose up -d`.
4. Configure and launch Nethermind client with the following flag `--Metrics.PushGatewayUrl=http://localhost:9091` or use the environment variable `NETHERMIND_METRICSCONFIG_PUSHGATEWAYURL` set to `http://localhost:9091`.
5. Open your local [Grafana](http://localhost:3000) on your browser and login with your configured username and password.

### Additional

For additional protection be sure to block external access to Prometheus(`9090`) and Prometheus pushgateways(`9091`) by using a firewall.
