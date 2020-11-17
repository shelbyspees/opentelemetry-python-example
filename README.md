# OpenTelemetry Example -- Python

This Fibonacci example demonstrates how to use OpenTelemetry to generate traces.

## Environment setup

```console
$ python3 -m pip install -r requirements.txt
```

## Instrument with OpenTelemetry

We're using the OpenTelemetry core trace functionality along with [Flask autoinstrumentation](https://github.com/open-telemetry/opentelemetry-python-contrib/tree/master/instrumentation/opentelemetry-instrumentation-flask).

## Send to Honeycomb

The app already has the [Honeycomb exporter](https://github.com/honeycombio/opentelemetry-exporter-python) set up so that you just need to include your Honeycomb API key when you start the server.

## Run the app

Once you've set up your development environment you can run the app, replacing the fake API key with your own:

```console
$ HONEYCOMB_API_KEY=abc123 python3 server.py
```

[Go to the Honeycomb UI](https://ui.honeycomb.io/home) and watch your data arrive!

## Troubleshooting

Make sure your API key has permission to create datasets.

For other questions, please ask the Honeycomb team in Slack.
