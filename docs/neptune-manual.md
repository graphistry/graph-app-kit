# Amazon Neptune and graph-app-kit manual setup

For quick launch and an introduction, see the [main graph-app-kit Neptune docs](neptune.md).

By using `graph-app-kit` with Amazon Neptune, you can visually explore graph database data and share point-and-click dashboard tools. This guides walks through manually launching Neptune, `graph-app-kit`, and connecting them. Alternatively, the [CloudFormation templates](neptune.md) enable quick launching preconfigured versions of both.

## 1. Manually setup Amazon Neptune

Ensure your Amazon Neptune database instance can be connected to by your `graph-app-kit` instance:

- You must have or create an Amazon Neptune cluster. See the official [Getting Started with Neptune docs](https://docs.aws.amazon.com/neptune/latest/userguide/get-started.html).

- Amazon Neptune clusters are hosted in a private VPC so the server hosting `graph-app-kit` must be [granted access to the VPC](https://docs.aws.amazon.com/neptune/latest/userguide/security-vpc.html). We *strongly* recommend hosting the `graph-app-kit` instance in a public subnet within the Neptune database's VPC. 

- If using IAM authorization on your Amazon Neptune cluster the sample code provided will need to be updated to support using SigV4 signing of requests. We recommend using [this tool](https://github.com/awslabs/amazon-neptune-tools/tree/master/neptune-python-utils) to simplify the process.

## 2. Manually launch and configure graph-app-kit for Amazon Neptune


Create an AWS EC2 `graph-app-kit` instance using the usual [graph-app-kit first launch step](setup-manual.md), with the following launch settings:

  1. Set `Network` to the `VPC` ID value ("`vpc-...`") from `1. Setup Amazon Neptune` (unless performing an alternative like manual VPC peering)
  2. Set `Subnet` to the `PublicSubnet1` subnet ID value ("`subnet-...`") from `1. Setup Amazon Neptune`
      * `Auto-assign Public IP` should default to `Use subnet setting (Enable)`

Continue through the [graph-app-kit steps to download and build](setup-manual.md).


SSH into your `graph-app-kit` instance and set the following required environment variable configurations in your [src/docker/.env](src/docker/.env) file:

```bash
NEPTUNE_READER_PROTOCOL=wss
NEPTUNE_READER_HOST=<Insert Neptune DBClusterReadEndpoint like abc.xyz.mno.neptune.amazonaws.com>
NEPTUNE_READER_PORT=8182
```

For additional Neptune template options, see [src/envs/neptune.env](src/envs/neptune.env).

Reset and restart your `graph-app-kit` container: 

```bash
cd src/docker
sudo docker-compose down -v
sudo docker-compose up -d
```

Watch logs with `sudo docker-compose logs -f -t --tail=1`

Access your Streamlit instance at http://the.public.ip.address:8501

## 4. Graph!

* Go to your Streamlit homepage using the link from the launch section you followed
* Select `GREMLIN: SIMPLE SAMPLE` from the dropdown to load a random sample of nodes from whatever Neptune database is connected
* Continue to the instructions for [creating custom views](views.md) and [adding common extensions](extend.md) like TLS, public/private dashboards, and more


## Advanced Neptune Configuration

### Run in an AWS VPC outside of the Neptune VPC 

Follow AWS and Neptune VPC Peering instructions for mapping subnets across the VPCs.

### Run outside of AWS and local developement

You can run Streamlit from outside of AWS. The challenge is that Amazon Neptune runs in a private VPC, meaning it exposes no internet-accessible API endpoints.

Options to connect to Amazon Neptune from a local computer include:

* Setup an SSH tunnel for your internet connections

* Configure a load balancer to expose the Neptune endpoint

* Choose another way to configure secure access to a private VPC in AWS.
Check the [Getting Started with Neptune](https://docs.aws.amazon.com/neptune/latest/userguide/get-started.html) page for the current best recommended practices.
