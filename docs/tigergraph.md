# Quick launch TigerGraph and graph-app-kit
This guide walks through setting up a TigerGraph database to configure with `graph-app-kit`.

## Setup TigerGraph
Head over to [TG Cloud](https://tgcloud.io/) and create an account

## Setup your graph

### Covid Graph
1. Click **create solution** and choose the **Covid-19 Analysis** starter kit.
2. Follow the steps shown to finish creating your solution.
3. Wait for the graph to be created (takes ~5 minutes).
4. Launch your graph in [GraphStudio](https://www.tigergraph.com/graphstudio/).
5. Select your graph from the top dropdown.
6. Head over to **Load Data** and hit the *play button* to load the data into the graph.

### Fraud Graph
1. Click **create solution** and choose the **Fraud and Money Laundering Detection** starter kit.
2. Follow the steps shown to finish creating your solution.
3. Wait for the graph to be created (takes ~5 minutes).
4. Launch your graph in [GraphStudio](https://www.tigergraph.com/graphstudio/).
5. Select your graph from the top dropdown.
6. Head over to **Load Data** and hit the *play button* to load the data into the graph.
7. Click **Write Queries** and hit the *plus* sign to add a new query. This query should be written as follows:
    ```
    CREATE QUERY totalTransaction(Vertex<User> Source) FOR GRAPH AntiFraud {  
        start = {Source};
    
        transfer = SELECT tgt
            FROM start:s -(User_Transfer_Transaction:e) - :tgt;
    
        receive = select tgt
            FROM start:s -(User_Recieve_Transaction:e) -:tgt;

        PRINT transfer, receive;
    }
    ```
8. Install all queries

### Pokemon Graph