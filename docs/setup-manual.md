# Setup graph-app-kit

For quick launchers, see the [AWS quick launch setup guide](setup.md).

## 1. Launch and setup a server for Docker + extensions

**Manual: Launch a Linux server and install, configure dependencies**

* Open ports: 22, 80, 443, 8501 for all users (`0.0.0.0/0`) or for specific admin and user IPs

* Ubuntu 18.04 LTS is the most common choice for containerized GPU computing

* Install docker-ce and docker-compose

* Optional:
   * GPU: If you have a [RAPIDS.ai](https://www.rapids.ai)-compatible GPU (see below), install the Nvidia docker runtime and set it as the default for Docker daemons

   * Extensions: Install Jupyter, a reverse proxy (ex: Caddy), and an authentication system

**Note: GPU Instances**: Cloud providers generally require you to request GPU capacity quota for your account, which may take 1 day. [RAPIDS.ai-compatible GPU instance types](https://github.com/graphistry/graphistry-cli/blob/master/hardware-software.md#cloud) include:

* AWS: g4, p3, p4
* Azure: NC6s_v2+, ND+, NCasT4

## 2. Download graph-app-kit

```bash
git clone https://github.com/graphistry/graph-app-kit.git
```

## 3. Build

```bash
cd graph-app-kit/src/docker
sudo docker-compose build
```

## 4. Set your Graphistry visualization credentials

Get a public or private Graphistry account:

* Graphistry Hub (public, free): [Create a free Graphistry Hub account](https://hub.graphistry.com/) using the username/password option, which you will use for API access. Visualizations will default to pointing to the public Graphistry Hub GPU servers.

* Alternatively, [launch a private Graphistry server](https://www.graphistry.com/get-started), login, and use the username/password/URL for your configurtion.

Edit `src/docker/.env` with:

```bash
GRAPHISTRY_USERNAME=your_username
GRAPHISTRY_PASSWORD=your_password
### OPTIONAL: Add if a private/local Graphistry server
#GRAPHISTRY_PROTOCOL=http or https
#GRAPHISTRY_SERVER=your.private-server.net
```

## 5. Start & stop

`cd src/docker` and then:

* Start: `sudo docker-compose up -d`
* Use: Go to `http://localhost:8501/dashboard` (or whatever the public IP)
* Stop: `sudo docker-compose down -v`

## Graph!

You are now ready to [add custom views](views.md) and [add integrations](extend.md).