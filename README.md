# Observability Dataset Sandbox

This repository spins up a small microservice environment that emits OpenTelemetry traces and includes intentionally faulty behaviors to simulate incidents.

## Architecture

- **orders-service** (Flask) receives order requests and calls inventory.
- **inventory-service** (Flask) returns inventory status and reserve responses.
- **OpenTelemetry Collector** accepts OTLP traces and forwards them to Jaeger.
- **Jaeger** provides the UI to explore traces.

## Prerequisites

- Docker + Docker Compose

## Run the stack

```bash
docker compose up --build
```

Once running:

- Orders service: http://localhost:5000/health
- Inventory service: http://localhost:5001/health
- Jaeger UI: http://localhost:16686

## Generate traffic

```bash
python scripts/generate_load.py
```

The script sends a mix of healthy and intentionally degraded requests to generate traces and error spans.

## Incident scenarios

You can trigger specific failure modes by passing query parameters to the orders endpoint:

| Scenario | Example | Effect |
| --- | --- | --- |
| Slow orders | `POST /orders?slow=1` | Adds latency in orders-service. |
| Slow inventory | `POST /orders?inventory_slow=1` | Adds latency in inventory lookup. |
| Flaky inventory | `POST /orders?inventory_flake=1` | Random 504s from inventory. |
| Reserve failure | `POST /orders?reserve_fail=1` | Inventory reserve endpoint returns 500. |
| Crash in orders | `POST /orders?bug=1` | Raises a runtime error in orders-service. |

These are designed to surface in traces and the Jaeger UI.

## Notes

- OTLP endpoint is configured via `OTEL_EXPORTER_OTLP_ENDPOINT` in docker-compose.
- Trace export is configured in code for clarity; auto-instrumentation can be added later if needed.
