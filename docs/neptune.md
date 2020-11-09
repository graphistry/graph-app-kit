# Amazon Neptune Setup and Configuration

Amazon Neptune is a managed cloud-based graph database that supports Gremlin/Tinkerpop and RDF graphs.

To use `graph-app-kit` with Amazon Neptune, there are several steps that you need to take to ensure that Streamlit will be able to connect to the graph database:

- You must have or create an Amazon Neptune cluster. If you need assistance in setting up a cluster we suggest looking at [Getting Started with Neptune](https://docs.aws.amazon.com/neptune/latest/userguide/get-started.html)

- Amazon Neptune clusters are hosted in a private VPC so the server hosting Graph App Kit must be granted access to the VPC.

- If using IAM authorization on your Amazon Neptune cluster the sample code provided will need to be updated to support using SigV4 signing of requests. We recommend using [this tool](https://github.com/awslabs/amazon-neptune-tools/tree/master/neptune-python-utils) to simplify the process.

## Configuration

To configure Graph App Kit to connect to Neptune the following fields need to be completed in the `.env` file:

```
NEPTUNE_READER_PROTOCOL=wss
NEPTUNE_READER_HOST=<Insert Cluster Read Endpoint>
NEPTUNE_READER_PORT=8182
```

## Local Developement

Since Amazon Neptune runs in a private VPC meaning that there is no publically accessible endpoint. In order to connect to Amazon Neptune from a local computer you will need to tunnel via SSH, configure a load balancer to expose the endpoint, or choose one of the other variety of ways to configure secure access to a private VPC in AWS. Check the [Getting Started with Neptune](https://docs.aws.amazon.com/neptune/latest/userguide/get-started.html)
page for the current best recommended practices.
