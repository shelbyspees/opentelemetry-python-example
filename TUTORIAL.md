# Fibonacci + Refinery

This repo is for playing around with [Refinery](https://docs.honeycomb.io/manage-data-volume/refinery/), Honeycomb's trace-aware sampling proxy.
It contains a Flask app that recursively calls itself to solve for Fibonacci values.
You can send telemetry data generated from the app through Refinery for sampling and then off to Honeycomb to observe.

## Run Refinery locally

### Requirements

You’ll need a [free Honeycomb account](http://honeycomb.io/signup), access to clone this repository, and the ability to run [Docker](https://www.docker.com/get-started) in your local environment.

_Note: Refinery support is included with [Honeycomb’s Enterprise tier](https://www.honeycomb.io/try-honeycomb-enterprise-for-free/). If you’re already working with our Customer Success team or Sales team, be sure to contact them for help setting up Refinery and defining rules based on your organization’s needs._

### Clone and run the application

Clone the repository and checkout the `refinery` branch:

```shell
git clone git@github.com:shelbyspees/opentelemetry-python-example.git fibonacci
cd fibonacci
git checkout refinery
```

Run the application using Docker compose, passing in your API key as an environment variable:

```shell
HONEYCOMB_API_KEY=abc123 docker-compose up
```

You should see output from both Refinery and the Flask app:

```console
. . .
refinery_1  | time="2021-03-09T03:00:43Z" level=info msg="Listening on 0.0.0.0:8080" router_iop=incoming
refinery_1  | time="2021-03-09T03:00:43Z" level=info msg="Listening on 0.0.0.0:8081" router_iop=peer
app_1       |  * Serving Flask app "server" (lazy loading)
app_1       |  * Environment: production
app_1       |    WARNING: This is a development server. Do not use it in a production deployment.
app_1       |    Use a production WSGI server instead.
app_1       |  * Debug mode: on
app_1       |  * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
app_1       |  * Restarting with stat
app_1       |  * Debugger is active!
app_1       |  * Debugger PIN: 844-753-887
```

Note that we're not sending our data through Refinery quite yet, the Refinery service is merely running alongside the Flask app.

Now you can `curl` the app (or navigate to it in your browser) to make sure it's running:

```console
$ curl localhost:5000
Visit http://localhost:5000/fib?i=1                                             
```

Hit the `/fib` API endpoint with a parameter (you may need to wrap the url in quotes in some terminals):

```console
$ curl localhost:5000/fib?i=1
0
```

Let's make sure the data arrived in Honeycomb.
Go to your new `fibonacci` dataset in the UI and under **Slowest traces** select **Run Query**:

![Fibonacci dataset in Honeycomb with suggested query highlighted](https://p-81Fa8J.b1.n0.cdn.getcloudapp.com/items/6quQppPz/b41886a8-1b3f-44b8-b112-b871adbbbc50.jpg?v=fa15d09445539eef1f889462543eebf5)

Once in the query results, select the Traces tab. Look for one with the `/fib` endpoint.

![List of traces from the flask app](https://p-81Fa8J.b1.n0.cdn.getcloudapp.com/items/d5uwkkDZ/560bc8e4-400d-4096-80ed-8a4e1c9d518d.jpg?v=7b68886da45aaaf6c01f51dfd23410c7)

For a nice meaty trace, try giving `i` a larger value like 10. Be careful of exponential growth with these input values!

```console
$ curl localhost:5000/fib?i=10
34
```

![Trace visualization of Fibonacci call with i set to 10](https://p-81Fa8J.b1.n0.cdn.getcloudapp.com/items/OAug11bd/7f1a6a2c-994b-4ac3-a0e1-3d4ca605cf8d.jpg)

Looks like it's working! Now let's try using Refinery.

## Update configuration to send to Refinery

We normally configure [OpenTelemetry](https://docs.honeycomb.io/getting-data-in/opentelemetry) to send data directly to `api.honeycomb.io`, Honeycomb’s event ingest API.
In order to use Refinery, you need to update the `api_host` parameter in the application’s Honeycomb configuration to point to Refinery instead.
Refinery will then make its sampling decisions and send data along to Honeycomb using the API key and dataset name in the events sent from your application.

### Restart Docker app with Refinery endpoint

This example app is set up to accept an environment variable for `HONEYCOMB_API_HOST`.
Stop the Docker app and restart it, passing in Refinery as the API host (in this case, port `8080` on the `refinery` service):

```shell
HONEYCOMB_API_KEY=abc123 HONEYCOMB_API_HOST=http://refinery:8080 docker-compose up
```

Hit an API endpoint again to ensure that data arrives in Honeycomb:

```console
$ curl localhost:5000/fib?i=2
1
```

Okay, now that that’s working, let’s configure sampling.

## Configure sampling rules

All sampling approaches with Refinery are trace-aware, which means you don’t have to worry about the common sampling pitfalls described in [last year’s HoneyByte](https://www.honeycomb.io/blog/honeybyte-get-a-taste-for-sampling/) on sampling with Beelines.

Deterministic sampling is the same sampling method that's available in the Beelines.
It’s the simplest and broadest form of sampling because it applies a single sample rate to all of your traffic.
The difference with Refinery is that it's much easier to set up when you have distributed tracing across multiple services.

Here’s `rules.toml` using the deterministic sampler:

```toml
# refinery/rules.toml
Sampler = "DeterministicSampler"
SampleRate = 5  # send 1 in every 5 traces
```

### DryRun Mode

For teams already sending production traffic to Honeycomb, you will probably want to test your sampling rules without the risk of accidentally dropping events you care about. For this, Refinery offers DryRun mode.

DryRun mode sends all your traffic while marking events that would have been kept or dropped based on the rules you’ve set in Refinery. You can then query in Honeycomb to see which events were marked to be dropped to make sure it aligns with your goals, both in terms of overall volume and for decisions around individual events.

For this example app, Refinery already has `DryRun` set to `true`.

Hit the `/fib` endpoint a few more times with some small values for `i` and look for this in the output:

```console
refinery_1  | time="2021-03-09T04:15:46Z" level=info msg="Trace would have been dropped, but dry run mode is enabled" dataset=fibonacci trace_id=10975145a077324e3a40c68e2b891409
```

Going back to the Honeycomb UI, **GROUP BY** `refinery_kept` and rerun your query.
Go to the **Results** tab to see which traces would have been kept or not.

## Look at ingest volume in Usage Mode

The `Sample Rate` field on events is hidden in the UI by default.
Behind the scenes, Honeycomb uses your sample rate when calculating values such as `COUNT`, `AVG`, etc.
In production environments with realistic workloads, you shouldn’t see a noticeable change in your data once sampling is turned on for real.

So how can you tell whether Refinery is actually sampling your data?
You need to be in [Usage Mode](https://docs.honeycomb.io/manage-data-volume/usage-center/) to see any sample rate attached to events.

(The shortcut for entering Usage Mode is to insert `/usage/` after your dataset name in the URL. It should look like this: `https://ui.honeycomb.io/{yourteam}/datasets/fibonacci/usage/`. But I'll share the proper way to get there as well.)

To enter Usage Mode, go to your Team Settings by selecting your user account in the left-hand sidebar, and then selecting **Team Settings** in the pop-up menu.

image alt: Honeycomb left-hand sidebar with user account pop-up menu

On the **Team Settings** page, select the **Usage** tab, and then scroll down to the **Per-dataset Breakdown** section.
Then select the **Usage Mode** button for the dataset you’re sending your application traffic to. This will take you to the query builder for that dataset.
Select the suggested query: Average and spread of sample rates over the past two hours.

![Suggested query for viewing data in Usage Mode](https://p-81Fa8J.b1.n0.cdn.getcloudapp.com/items/bLug2L6g/848c0584-5398-4802-8246-2e26ee86abd5.jpg?v=3e291a76164e919d9c78e3fc554c38f4)

This suggested query gives us a couple different graphs to analyze:

- `HEATMAP(Sample Rate)`
- `AVG(Sample Rate)`
- `COUNT` (unweighted)

![Query results showing the average and spread of sample rates over the past two hours](https://p-81Fa8J.b1.n0.cdn.getcloudapp.com/items/Z4u6B4xw/f8b6d8ba-a435-41a7-b483-dc094a0b5f9e.jpg?v=039e4fff4c917c6ba11b7f395b14c929)

You can even use Usage Mode combined with the DryRun option to see what the sample rates _would be_ if you were sampling for real.
Add `refinery_kept` back into the **GROUP BY** field to see the breakdown.

![Average sample rate in DryRun mode](https://p-81Fa8J.b1.n0.cdn.getcloudapp.com/items/6quQpnQA/35aafe11-0c83-48b3-8bdd-1acc13c03d49.jpg?v=9d5007bc78987351f12901dbff3442b1)

## More sampling rules

Refinery comes with a handy [`rules_complete.toml`](https://github.com/honeycombio/refinery/blob/main/rules_complete.toml) file that explains all the configuration options and gives examples.
Let’s explore a few sampling methods that Refinery offers.

### Rules-based sampling

A good place to start when you're new to tail-based sampling is using rules-based sampling, which allows you to specify a sample rate based on a particular value for a field in your events.
This enables you to down-sample your uninteresting traffic like `HTTP 200`s and keep interesting traffic like any `5xx` errors.
For the uninteresting traffic, you can configure the rules-based sampler to send 1 in every 1000 of your `HTTP 200` responses.
Since your `HTTP 200`s are all nearly identical, the 1 that gets sent to Honeycomb will stand in to represent its 999 dropped counterparts.
A sample rate of `1000` is a reasonable number for uninteresting traffic on high-volume services.

```toml
# refinery/rules.toml
Sampler = "RulesBasedSampler"

[[rule]]
  name = "500 errors"
  SampleRate = 1 # send 1 in 1 (100%) of these traces
  [[rule.condition]]
    field = "http.status_code"
    operator = ">="
    value = 500

[[rule]]
  name = "downsample 200 responses"
  SampleRate = 1000 # send 1 in 1000 of these traces
  [[rule.condition]]
    field = "http.status_code"
    operator = "="
    value = 200

[[rule]]
  SampleRate = 50 # send 1 in 50 of all other traces
```

### Exponential moving average

**This is the recommended sampling method for most teams.** The `EMADynamicSampler` allows you to set a target sample rate and then pass in specific fields as keys to sample on.
The exponential moving average implementation does a little bit of math to smooth out the curve based on how frequently the values in your designated fields have appeared over a recent time period.
This helps avoid the spiky changes in event volume when you have a burst of traffic or a sudden scale-up event, which is the downside of vanilla dynamic sampling.

```toml
# refinery/rules.toml
[my-dataset]
  Sampler = "EMADynamicSampler"
  GoalSampleRate = 10
  FieldList = ["http.method","http.status_code"]
  AdjustmentInterval = 15
  Weight = 0.5
```

In this example, we’ve configured the sampler to use the `http.method` and `http.status_code` fields for making decisions.
Based on the values of those fields, the sampler will adjust how many similar events it drops.
So for each combination of values of `http.method` and `http.status_code`, the sampler will keep track of how many events have those values:

- `GET` and `200`
- `GET` and `500`
- `POST` and `200`
- `POST` and `500`
- etc.

While tracking this, Refinery will aim to send 1 in every 10 traces with that combination of values.
So the two fields together, `http.method` and `http.status_code`, act as a combined key to make sampling decisions on.

To better understand how this works, you can configure Refinery to add a field to your events to track the fields (combined key) that the sampler used to make its decision for that trace:

```toml
   # . . .(continued from above)
   # Keep track of what key the sampler is using to make decisions
   AddSampleRateKeyToTrace = true
   AddSampleRateKeyToTraceField = "meta.refinery.dynsampler_key"
```
