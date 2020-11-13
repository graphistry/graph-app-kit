# Setup graph-app-kit

The below provides quick launchers for AWS-based deployments. See [manual setup](setup-manual.md) for alternative instructions.

## 1. Launch graph-app-kit

**Option 1 - Full (Recommended):**

  * GPU instance
  * Web-based live editing
  * Included: Graphistry, public + private Streamlit dashboards, Jupyter notebooks, RAPIDS.ai Python GPU ecosystem

  [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=region#/stacks/new?stackName=graph_app_kit_full&templateURL=https://graph-app-kit-repo-public.s3.us-east-2.amazonaws.com/templates/latest/core/graphistry.yml)
  
  If AWS reports `Please select another region`, use the `Select a Region` dropdown in the top right menu.

  **Note: GPU Instances**: The compatible GPU instance familes are g4, p3, p4

**Option 2 - Minimal:**

  * CPU instance
  * Author views from your terminal
  * Included: Public Streamlit dashboards linked against a remote Graphistry account
  * Not included: Local Graphistry, private dashboards, Jupyter, RAPIDS.ai

  Get a free or self-managed [Graphistry server account](https://www.graphistry.com/get-started) with username+pass then [launch a minimal stack](https://console.aws.amazon.com/cloudformation/home?region=region#/stacks/new?stackName=graph_app_kit_full&templateURL=https://graph-app-kit-repo-public.s3.us-east-2.amazonaws.com/templates/latest/core/graphistry.yml)
  
  If AWS reports `Please select another region`, use the `Select a Region` dropdown in the top right menu.

----

1. **Launch configuration: Details parameters**

  1. Set stack name to anything, such as `graph-app-kit-a`
  1. Set `VPC` to one that is web-accessible
  1. Set `Subnet` to a web-accessible subnet in the VPC ("`subnet-...`")
  1. Set `GraphAppKitKeyPair` to any where you have the SSH private.key

  If using the minimal template, fill in details for your Graphistry account

2. ***(Optional):*** **Monitor instance launch for progress and errors**

  * Click the `Resources` tab and follow the link to the EC2 instance AWS console page after it gets generated

  * Click on the instance to find its public IP address
  
  * Login and watch:

  ```bash
  ssh -i /my/private.key ubuntu@the.instance.public.ip 
  ### ssh -i /my/private.key ec2-user@the.instance.public.ip for Minimal launcher

  tail -f /var/log/cloud-init-output.log -n 1000
  ```

## 3. Graph!

Go to your public Streamlit dashboard and start exploring: http://[the.public.ip.address]/public/dash

### Login

* Upon launch completion, you will have a full suite of graph tools located at **http://[the.public.ip.address]**

* Web login using credentials **`admin`** / ***`i-theInstanceID`*** 

* SSH using the instructions from step 2

* ***Note***: The minimal launcher has no web admin portal, just SSH and Streamlit

### URLs for full stack 

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

### URLs for minimal stack 

* **Streamlit: Public dashboards**
  * **http://[the.public.ip.address]/public/dash**
  * Installed at `/home/ubuntu/graph-app-kit/public/graph-app-kit`
  * Run as `src/docker $ docker-compose up -d streamlit`

## 4. Next steps

Continue to the instructions for [creating custom views](views.md) and [adding common extensions](extend.md) like TLS, public/private dashboards, and more