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

Get your API key via https://ui.honeycomb.io/account after signing up for Honeycomb.


## Make a request

Now that the app is running, you should be able to make a request:

```console
$ curl localhost:5000
```

You should get the response:
```
Visit http://localhost:5000/fib?i=1
```

You can update the value of `i` to see what the Fibonacci return values are.

[Go to the Honeycomb UI](https://ui.honeycomb.io/home) and watch your data arrive!

## Troubleshooting

If you don't see data coming in, make sure your API key has permission to create datasets. You can check your API key permissions at https://ui.honeycomb.io/account.

For other questions, please ask the Honeycomb team in Slack.
