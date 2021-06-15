import os
import sys

import requests
from flask import Flask, request
# Required for sending telemetry to Honeycomb
# Required instrumentation packages
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                            ConsoleSpanExporter,
                                            SimpleSpanProcessor)

# Configure exporter to send to Honeycomb
otlp_exporter = OTLPSpanExporter(
    endpoint=os.environ["HONEYCOMB_API_HOST"],
    insecure=True,
    headers=(
        ("x-honeycomb-team", os.environ['HONEYCOMB_API_KEY']),
        ("x-honeycomb-dataset", os.environ['HONEYCOMB_DATASET'])
    ),
)


# Configure trace handler object
trace.set_tracer_provider(TracerProvider(
    resource=Resource({"service.name": "fibonacci"})))
# tell trace handler to print to stdout
trace.get_tracer_provider().add_span_processor(
    SimpleSpanProcessor(ConsoleSpanExporter()))
# tell trace handler to send using OTLP exporter
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))


# This is the actual app
app = Flask(__name__)


# Tell auto-instrumentation to instrument this app
FlaskInstrumentor().instrument_app(app)
# Build Flask requests into traces
RequestsInstrumentor().instrument()


@app.route("/")
def root():
    sys.stdout.write('\n')
    return "Visit http://localhost:5000/fib?i=1"


@app.route("/fib")
@app.route("/fib_internal")
def fib():
    value = int(request.args.get('i'))
    current_span = trace.get_current_span()
    current_span.set_attribute("request", value)
    result = 0
    if value == 1 or value == 0:
        result = 0
    elif value == 2:
        result = 1
    else:
        minus_one_payload = {'i': value - 1}
        minus_two_payload = {'i': value - 2}
        current_span.set_attribute("payload_value_one", value-1)
        resp_one = requests.get(
            'http://127.0.0.1:5000/fib_internal', minus_one_payload)
        current_span.set_attribute("payload_value_two", value-2)
        resp_two = requests.get(
            'http://127.0.0.1:5000/fib_internal', minus_two_payload)
        result = int(resp_one.content) + int(resp_two.content)
    sys.stdout.write('\n')
    return str(result)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
