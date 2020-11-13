# Quick launch Amazon Neptune and graph-app-kit

[Amazon Neptune](https://aws.amazon.com/neptune/) is a:

> ... &quot;fast, reliable, fully managed graph database service that makes it easy to build and run applications that work with highly connected datasets&quot;

Amazon Neptune supports both property graph queries with [Apache Gremlin/Tinkerpop](https://tinkerpop.apache.org/) queries, and RDF graphs with SPAQL queries. By using `graph-app-kit` with Amazon Neptune, you can visually explore graph database data and share point-and-click dashboard tools. 

This guides walks through quick launch scripts for Neptune and Neptune-aware `graph-app-kit`. Alternatively, you may follow the [manual `graph-app-kit` Amazon Neptune setup guide](neptune-manual.md). By using the quick launcher, you get out-of-the-box integration with Neptune, and extensions like built-in GPU Graphistry, Jupyter notebooks and web authoring, and public+private dashboards.

## 1. Setup Amazon Neptune with identity graph demo data

Launch using a button at the bottom of the [identity graph sample cloud formation templates tutorial](https://aws.amazon.com/blogs/database/building-a-customer-identity-graph-with-amazon-neptune/):


1. Click the `Launch Stack` button for your region:
  * The recommended full `graph-app-kit` quick launcher requires a GPU instance:
     * ... So ensure Neptune is in a region where you have `g4dn`/`p3`/`p4` GPU quota [or request it](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html)
  * The minimal `graph-app-kit` quick launcher can run without a GPU, but also does not come with Jupyter, public/private dashboards, etc.
2. Check the acknowledgement boxes in the `Capabilities` section
3. Click `Create Stack` (5-20min)
  *  OUTPUT: The root `Identity-Graph-Sample` item's `Output` tab will show values used to configure the next steps:

      * `VPC`: ID `vpc-abc`
      * `PublicSubnet1`: ID `subnet-abc`
      * `DBClusterReadEndpoint`: URL `abc.cluster-ro-xyz.zzz.neptune.amazonaws.com`

----

**Manage:**

* **Neptune UI**: AWS console -> `Services` -> `Neptune` -> `Databases`

* **Stack**: At any time, inspect the template's generated AWS resources and `delete` them:
	*  `AWS Console` -> `Services` -> `CloudFormation` -> `Stacks` 

* **Resize ($)**: Upon completed launch, resize Neptune to a cheaper instance: 
  * Got to the above Neptune UI -> `Databases` -> **Modify** the **Writer**
  * Change *DB instance class* to *db.r4.large* -> `Continue` -> check **Apply immediately** -> `Modify DB Instance`

## 2. Launch graph-app-kit configured for Amazon Neptune

The quick launch template launchs a single GPU EC2 instance in your Neptune VPC. You will be able to log into the instance and start making views for Neptune data. It automatically connects to both the Neptune demo database and to your production instance. It contains Graphistry, Streamlit for public and team-only use, and RAPIDS.ai-ready Jupyter notebooks.


1. **Launch the template using the following parameters:**

  * Form `Details` config:
      1. Set stack name to anything, such as `graph-app-kit-a`
      1. Set `VPC` to the `VPC` ID value ("`vpc-...`") from `1. Setup Amazon Neptune`
      1. Set `Subnet` to the `PublicSubnet1` subnet ID value ("`subnet-...`") from `1. Setup Amazon Neptune`
      1. Set `GraphAppKitKeyPair` to any where you have the SSH private.key
  * Form `Options` config:
      * *Recommended*: Add tag `name` => `graph-app-kit-a`

2. **Go to your `graph-app-kit` instance**

  * Click the `Resources` tab and follow the link to the EC2 instance AWS console page after it gets generated

  * Click on the instance to find its public IP address

  * *Optional*: From a commandline, SSH in to your GPU instance and watch the initialization logs for errors:

```bash
ssh -i /my/private.key ubuntu@the.instance.public.ip
tail -f /var/log/cloud-init-output.log -n 1000
```

## 4. Graph!


### Login

* Upon launch completion, you will have a full suite of graph tools located at **http://[the.public.ip.address]**

* Login using credentials **`admin`** / ***`i-theInstanceID`*** 

### Minimal

If using the minimal launcher, you will only have url **http://[the.public.ip.address]/public/dash** and can edit views via SSH (`ubuntu@[the.public.ip]:/home/ubuntu/graph-app-kit`)

### URLs

* **Graphistry: GPU-accelerated visual analytics + account login**
  * **http://[the.public.ip.address]**
  * Login as `admin` / `your-aws-instance-id`
  * Installed at `/home/ubuntu/graphistry`
  * You can change your admin password using the web UI
* **Streamlit: Public dashboards**
  * **http://[the.public.ip.address]/public/dash**
  * Installed at `/home/ubuntu/graph-app-kit/public/graph-app-kit`
  * Run as `src/docker $ docker-compose -p pub run -d --name streamlit-pub streamlit`
* **Streamlit: Private dashboards**
  * **http://[the.public.ip.address]/private/dash**
  * Installed at `/home/ubuntu/graph-app-kit/private/graph-app-kit`
  * Run as `src/docker $ docker-compose -p priv run -d --name streamlit-priv streamlit`
* **Jupyter: Data science notebooks + Streamlit dashboard live-editing**
  * **http://[the.public.ip.address]/notebook**
  * Live-edit `graph-app-kit` view folders `notebook/graph-app-kit/[public,private]/views`


To start exploring graphs:

* Go to your Streamlit homepage using the link from the launch section you followed
* Select `GREMLIN: SIMPLE SAMPLE` from the dropdown to load a random sample of nodes from whatever Neptune database is connected
* Continue to the instructions for [creating custom views](views.md) and [adding common extensions](extend.md) like TLS, public/private dashboards, and more

For more advanced configuration options, see the [manual Amazone Neptune setup guide](neptune-manual.md).
