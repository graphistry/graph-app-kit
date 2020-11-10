# Setup graph-app-kit

## 1. Launch and setup a server for Docker

Launch a Linux server with Docker, docker-compose, and optionally, with a [RAPIDS.ai](https://www.rapids.ai)-compatible GPU with the Nvidia docker runtime on by default.

To quick launch a ready server, launch a [Graphistry marketplace instance](https://www.graphistry.com/get-started). They are preconfigured instances in AWS and Azure ready for GPU-aware docker-compose and with a built-in Graphistry GPU visualization server, account system, team Jupyter notebooks, ready RAPIDS.ai environment, and resiliency layers.

## 2. Download graph-app-kit

```bash
git clone https://github.com/graphistry/graph-app-kit.git
```

## 3. Build

```bash
cd src/docker
sudo docker-compose build
```

## 4. Set your Graphistry visualization credentials

Get a Graphistry account:

* Graphistry Hub (free): [Create a free Graphistry Hub account](https://hub.graphistry.com/) using the username/password option, which you will use for API access

* Alternatively, [launch a private Graphistry server](https://www.graphistry.com/get-started), login, and note the username/password for the account

Edit `src/docker/.env` with:

```bash
GRAPHISTRY_USERNAME=your_username
GRAPHISTRY_PASSWORD=your_password
### OPTIONAL: Private server config
#GRAPHISTRY_PROTOCOL=http
#GRAPHISTRY_SERVER=your.private-server.net
```

## 5. Start & stop

`cd src/docker` and then:

* Start: `sudo docker-compose up -d`
* Use: Go to `http://localhost:8501/dashboard` (or whatever the public IP)
* Stop: `sudo docker-compose down -v`

## Graph!

You are now ready to [add custom views](views.md) and [add integrations](extend.md).