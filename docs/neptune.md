# Amazon Neptune setup and graph-app-kit configuration

[Amazon Neptune](https://aws.amazon.com/neptune/) is a &quot;fast, reliable, fully managed graph database service that makes it easy to build and run applications that work with highly connected datasetsa&quot;. It supports both property graph queries with [Apache Gremlin/Tinkerpop](https://tinkerpop.apache.org/) queries, and RDF graphs with SPAQL queries.

## 1. Setup Amazon Neptune

There are several steps that you need to take to ensure that your Neptune database can be connected to by your `graph-app-kit` instance:

- You must have or create an Amazon Neptune cluster. If you need assistance in setting up a cluster we suggest looking at [Getting Started with Neptune](https://docs.aws.amazon.com/neptune/latest/userguide/get-started.html). 

- Amazon Neptune clusters are hosted in a private VPC so the server hosting `graph-app-kit` must be [granted access to the VPC](https://docs.aws.amazon.com/neptune/latest/userguide/security-vpc.html).

- If using IAM authorization on your Amazon Neptune cluster the sample code provided will need to be updated to support using SigV4 signing of requests. We recommend using [this tool](https://github.com/awslabs/amazon-neptune-tools/tree/master/neptune-python-utils) to simplify the process.

### Demo quick launch: Customer identity graph database

Quick launch the customer identity graph database using the [identity graph sample cloud formation templates](https://aws.amazon.com/blogs/database/building-a-customer-identity-graph-with-amazon-neptune/). 

Ater the stack launches (5-20min), the root `Identity-Graph-Sample` item's `Output` tab will show values used to configure the next steps.

Later, you can use the `delete` button here to delete the stack.

## 2. Configure graph-app-kit for Amazon Neptune

If you do not have a `graph-app-kit` server, follow the main instructions to [get going](readme.md#get-going).

SSH into your `graph-app-kit` instance and set the following required environment variable configurations in your [src/docker/.env](src/docker/.env) file:

```bash
NEPTUNE_READER_PROTOCOL=wss
NEPTUNE_READER_HOST=<Insert Neptune DBClusterReadEndpoint>
NEPTUNE_READER_PORT=8182
```

For additional template options, see [src/envs/neptune.env](src/envs/neptune.env).

Reset and restart your `graph-app-kit` container: 

```bash
cd src/docker
docker-compose down -v
docker-compose up -d
```

## Local Developement

As Amazon Neptune runs in a private VPC, it exposes no internet-accessible API endpoints, so local development requires additional steps.

To connect to Amazon Neptune from a local computer, you can:
* Setup an SSH tunnel for your internet connections
* Configure a load balancer to expose the Neptune endpoint
* Choose another way to configure secure access to a private VPC in AWS.
Check the [Getting Started with Neptune](https://docs.aws.amazon.com/neptune/latest/userguide/get-started.html) page for the current best recommended practices.
