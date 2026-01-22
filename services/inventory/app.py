import os
import random
import time

from flask import Flask, jsonify, request
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

SERVICE_NAME = "inventory-service"


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


@app.get("/inventory/<item_id>")
def inventory(item_id: str):
    slow = request.args.get("slow") == "1"
    flake = request.args.get("flake") == "1"
    with tracer.start_as_current_span("inventory.lookup"):
        if slow:
            time.sleep(float(os.getenv("INVENTORY_SLOW_SECONDS", "1.5")))
        if flake and random.random() < float(os.getenv("INVENTORY_FLAKE_RATE", "0.3")):
            return jsonify({"error": "database timeout"}), 504
        quantity = random.randint(0, 20)
        return jsonify({"item_id": item_id, "quantity": quantity}), 200


@app.get("/reserve/<item_id>")
def reserve(item_id: str):
    with tracer.start_as_current_span("inventory.reserve"):
        if request.args.get("fail") == "1":
            return jsonify({"error": "reserve failed"}), 500
        return jsonify({"item_id": item_id, "reserved": True}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
