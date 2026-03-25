# WATER: Workflow Allocation and Task Execution Router

WATER is a constraint-aware orchestration system that automatically allocates and executes containerized workloads across heterogeneous compute nodes (e.g., local developer machines, edge devices, and cloud virtual machines).

## System Architecture

The WATER architecture is composed of several modular Python components that evaluate hardware constraints, rank target nodes, and dispatch work via Prefect.

- **main.py**: The command-line entry point that parses workflow requests and initiates the allocation and deployment cycle.
- **models.py**: Defines strictly typed data structures using Pydantic, including `WATERWorkflow` (workload constraints and telemetry) and `ComputeNode` (hardware capabilities and network identification).
- **registry.py**: Maintains the dynamic or statically mapped inventory of available compute nodes within the cluster.
- **allocator.py**: Applies a multi-pass filtering and scoring algorithm. It evaluates hard constraints (e.g., RAM minimums, GPU requirements, HIPAA data residency restrictions) and ranks eligible nodes based on available resources and edge-preference weights.
- **prefect_translator.py**: Translates the allocator's logical placement into executable Prefect deployments, dispatching the Docker container execution to the designated worker node.
- **audit.py**: A local SQLite-based logging system (`audit.db`) that records immutable lifecycle events of every workflow (Submission, Allocation, Execution, and Completion states).

## Distributed Execution Model

WATER utilizes a Hub-and-Spoke distributed execution model powered by Prefect, bypassing the need for manual SSH tunneling or scp transfers.

1. **Central Server**: A central Prefect server tracks workflow states and manages deployment queues.
2. **Worker Nodes**: Compute nodes (such as laptops or GCP instances) run a lightweight Python daemon (`worker_node.py`) that polls the central server for workloads assigned specifically to their Node ID.
3. **Execution**: Upon receiving a workload payload, the worker node pulls the designated Docker image and executes the containerized task natively on its host hardware.

*Note: In this distributed architecture, data must either be baked directly into the Docker image, accessible via a shared network file system (NFS), or pulled dynamically from cloud object storage (S3/GCS) by the container payload.*

## Installation and Setup

### Prerequisites
- Python 3.10+
- Docker Engine installed and accessible on all intended worker nodes
- Prefect 3.0+

### Environment Initialization

Clone the repository and install the minimal orchestration dependencies:

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### Cluster Bootstrapping

1. **Initialize the Orchestrator** 
   Start the Prefect server on your primary control machine:
   ```bash
   prefect server start --host 0.0.0.0
   ```

2. **Initialize Worker Nodes**
   On every machine joining the cluster, export the central server's API address and launch the worker listener, providing a unique Node ID that has been allocated in `registry.py`:
   ```bash
   export PREFECT_API_URL="http://<SERVER_IP>:4200/api"
   python lan_distributed/worker_node.py --node-id laptop-edge-2
   ```

## Workload Submission

Workloads are defined declaratively via YAML configuration files.

```yaml
name: logistic_regression_iris
execution:
  docker_image: ayushranjan/water-iris-infer:latest
  entrypoint: python /app/train.py
  timeout_minutes: 30
resources:
  requires_gpu: false
  min_ram_gb: 4
data:
  input_path: /mnt/shared_network_drive/iris_data
  sensitivity: restricted
  must_stay_local: false
placement:
  target_node_id: laptop-edge-2
```

To submit the workflow to the cluster:

```bash
export PREFECT_API_URL="http://127.0.0.1:4200/api"
python lan_distributed/main.py --workflow my_workflow_config.yaml
```

The allocator will parse the request, verify that `laptop-edge-2` meets the 4GB RAM requirement, and push the workload to the Prefect deployment queue. The remote worker matching that Node ID will instantly pull the configuration and execute the Docker payload.
