# Amazon Neptune Setup and Configuration

Amazon Neptune is a managed cloud-based graph database that supports Gremlin/Tinkerpop and RDF graphs.


## Manual setup

To use `graph-app-kit` with Amazon Neptune, there are several steps that you need to take to ensure that Streamlit will be able to connect to the graph database:

- You must have or create an Amazon Neptune cluster. If you need assistance in setting up a cluster we suggest looking at [Getting Started with Neptune](https://docs.aws.amazon.com/neptune/latest/userguide/get-started.html). 

- Amazon Neptune clusters are hosted in a private VPC so the server hosting `graph-app-kit` must be [granted access to the VPC](https://docs.aws.amazon.com/neptune/latest/userguide/security-vpc.html).

- If using IAM authorization on your Amazon Neptune cluster the sample code provided will need to be updated to support using SigV4 signing of requests. We recommend using [this tool](https://github.com/awslabs/amazon-neptune-tools/tree/master/neptune-python-utils) to simplify the process.

## Demo quick launch: Customer identity graph database

Quick launch the customer identity graph database using the [identity graph sample cloud formation templates](https://aws.amazon.com/blogs/database/building-a-customer-identity-graph-with-amazon-neptune/).

## Configuration

Set the following required environment variable configurations in your [src/docker/.env](src/docker/.env) file:

```
NEPTUNE_READER_PROTOCOL=wss
NEPTUNE_READER_HOST=<Insert Cluster Read Endpoint>
NEPTUNE_READER_PORT=8182
```

For templates, see [src/envs/neptune.env](src/envs/neptune.env).

Reset and restart your container: `docker-compose down -v && docker-compose up -d`.

## Local Developement

As Amazon Neptune runs in a private VPC, it exposes no internet-accessible API endpoints, so local development requires additional steps.

To connect to Amazon Neptune from a local computer, you can:
* Setup an SSH tunnel for your internet connections
* Configure a load balancer to expose the Neptune endpoint
* Choose another way to configure secure access to a private VPC in AWS.
Check the [Getting Started with Neptune](https://docs.aws.amazon.com/neptune/latest/userguide/get-started.html) page for the current best recommended practices.
