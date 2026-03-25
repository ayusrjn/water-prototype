# WATER (LAN Distributed Prefect Server Architecture)

This folder contains a refactored version of the WATER prototype where **SSH has been completely removed**. Instead of the orchestrator laptop SSHing directly into machines, it leverages a central **Prefect Server** and distributed **Prefect Workers**.

## 🚀 Architecture
- **Coordinator**: Decides which node a workload should run on using `allocator.py`.
- **Prefect Server**: Central control plane holding the queue of workloads.
- **Worker Node** (`worker_node.py`): Lightweight proxy running on edge nodes that constantly polls the central Prefect server for work assigned specifically to it.

## 🛠️ Step-by-Step Setup

### 1. Start the Prefect Server 
*(Run on ANY machine that will act as the orchestrator/brain)*
```bash
prefect server start --host 0.0.0.0
```

### 2. Connect Your Edge Nodes
*(Run on the actual execution machines - e.g. laptop, GCP VM, Raspberry Pi)*

Make sure the worker machines can talk to the Prefect Server, and then boot up a worker identifying itself by an ID in the layout:
```bash
export PREFECT_API_URL="http://<SERVER_IP>:4200/api"

# For the laptop:
python lan_distributed/worker_node.py --node-id laptop-edge

# For the GCP instance:
python lan_distributed/worker_node.py --node-id gcp-edge
```
These machines will now sit idle, polling the central server for `laptop-edge_deployment` and `gcp-edge_deployment` workloads.

### 3. Submit Workloads
*(Run on the Orchestrator)*

```bash
export PREFECT_API_URL="http://127.0.0.1:4200/api"

python lan_distributed/main.py --workflow lan_distributed/workflow_rf_iris_gcp.yaml
```

`main.py` parses the YAML, scores the rules, and decides "Ah, this should run on `gcp-edge`". It then commands Prefect to trigger a `run_deployment` specifically targeting the `gcp-edge_deployment`. 

The GCP worker script picks up the pulse, pulls the exact container image, executes it locally via `docker`, and sends the execution logs seamlessly back to the Prefect Server!

## ⚠️ Data Note
Because this architecture moves away from 1-to-1 SSH SCP syncing, it operates under the assumption that the Local and Remote environments share an NFS drive, Object Storage (S3/GCS), or an identical underlying directory structure where data resides. 
