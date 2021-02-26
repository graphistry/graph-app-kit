# Quick launch TigerGraph and graph-app-kit
This guide walks through setting up a TigerGraph database to configure with `graph-app-kit`.

## Setup

### 1. Setup TigerGraph

Create a free TigerGraph Cloud account, launch the prebuilt solution, and run the sample data loader and sampler query loader. 

1. Create a [TG Cloud](https://tgcloud.io/) account 
2. Click **Create Solution** and choose the **Fraud and Money Laundering Detection** starter kit.
3. Click through the options and launch, which takes ~5 minutes
4. Open [GraphStudio](https://www.tigergraph.com/graphstudio/): `My Solutions` -> `Applications` -> `Graph Studio`, using credentials `tigergraph` / `password_you_set_during_launch`
5. In the top-left dropdown, flip from `Global View` to `Anti Fraud`
6. Click the left menu's **Load Data** option and hit the *play button* (`Start/Resume loading`) to load the sample data into the graph
7. Click the left menu's **Write Queriess** option and hit the *up button* (`Installl all queries`) to compile the sample queries
8. Generate a secret token: Top-right `Admin` button -> `User Management` -> new alias `mysecret` -> hit `[ + ]` and copy the generated secret

See also the demo video from an older version of TG Cloud: 

[ <img src="https://raw.githubusercontent.com/akash-kaul/static_media/main/Screen%20Shot%202021-01-18%20at%203.20.04%20PM.png" width=300/>](https://www.youtube.com/watch?v=JARd9ULRP_I)


### 2. Quick-launch graph-app-kit

One-click launch a [full graph-app-kit install](setup.md) or manually setup a [local minimal version](set-manual.md) 

* [AWS quick launch](setup.md): Instance with preloaded Docker setup of Jupyter notebooks, public+private StreamLit dashboards, Graphistry/RAPIDS GPU visual analysis

* [Local version](set-manual.md): Local Docker container with StreamLit and libraries, guides for adding API keys and common configurations

### 3. OPTIONAL: Store TigerGraph credentials in graph-app-kit

1. Go to your install's command line. If a quick-launched cloud instance, do so by SSH'ing and going to either your public server (`graph-app-kit/public/`) or private server (`graph-app-kit/private/`)

2. Store your TigerGraph credentials in `src/envs/tigergraph.env`:

```bash
TIGERGRAPH_HOST=https://myinstance.i.tgcloud.io
TIGERGRAPH_USERNAME=tigergraph
TIGERGRAPH_PASSWORD=mypassword
TIGERGRAPH_GRAPHNAME=AntiFraud
TIGERGRAPH_SECRET=mysecret
```

3. Restart your Streamlit container with the new creds: `cd src/docker && sudo docker-compose up -d --force-recreate`

## Explore

1. Go to the Streamlit website based on how you launched graph-app-kit: `/public/dash` / `/private/dash` (quick launched) or `localhost:8501/` (manual)

The generic `INTRO: SIMPLE PIPELINE` dashboard should have loaded

2. Switch to `TIGERGRAPH: FRAUD FILTER CIRCLE`

If you had not stored TigerGraph credentials, input them in the left sidebar menu

