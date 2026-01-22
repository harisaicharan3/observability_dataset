import os
import time

import requests
from flask import Flask, jsonify, request
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

SERVICE_NAME = "orders-service"
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory:5001")


def configure_tracing() -> None:
    resource = Resource.create({"service.name": SERVICE_NAME})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter()
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


configure_tracing()

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()
tracer = trace.get_tracer(__name__)


@app.get("/health")
def health() -> tuple[dict, int]:
    return {"status": "ok"}, 200


@app.post("/orders")
def create_order():
    payload = request.get_json(silent=True) or {}
    item_id = payload.get("item_id", "sku-123")
    with tracer.start_as_current_span("orders.create"):
        slow_down = request.args.get("slow") == "1"
        if slow_down:
            time.sleep(float(os.getenv("ORDERS_SLOW_SECONDS", "1.2")))

        inventory_params = {}
        if request.args.get("inventory_slow") == "1":
            inventory_params["slow"] = "1"
        if request.args.get("inventory_flake") == "1":
            inventory_params["flake"] = "1"
        inventory_response = requests.get(
            f"{INVENTORY_URL}/inventory/{item_id}", params=inventory_params, timeout=2
        )
        if inventory_response.status_code != 200:
            return (
                jsonify({"error": "inventory unavailable"}),
                503,
            )

        reserve_response = requests.get(
            f"{INVENTORY_URL}/reserve/{item_id}",
            params={"fail": "1" if request.args.get("reserve_fail") == "1" else "0"},
            timeout=2,
        )
        if reserve_response.status_code != 200:
            return jsonify({"error": "reserve failed"}), 500

        if request.args.get("bug") == "1":
            raise RuntimeError("Null pointer during checkout")

        return jsonify({"order_id": "ord-456", "item_id": item_id}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
