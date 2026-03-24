# WATER (Workflow Allocation and Task Execution Router)

WATER is a prototype system that automatically allocates and orchestrates containerized machine learning workloads across heterogeneous compute nodes, such as local edge devices (laptops) and remote cloud virtual machines (GCP).

## 🚀 Features

- **Constraint-Aware Allocation**: Workloads specify hardware requirements (RAM, GPU) and data sensitivity limits (e.g., HIPAA-restricted data stays local).
- **Multi-Node Execution**: Run Docker containers either locally or over SSH on remote VMs.
- **Workflow Orchestration**: Powered by [Prefect](https://www.prefect.io/) for robust execution, retry logic, and monitoring.
- **Auto Data Sync**: Seamlessly syncs local input data to remote execution nodes via `rsync`/`scp` before container execution.
- **Auditing**: Records all lifecycle events (submitted, allocated, executed, completed/failed) in a local SQLite database (`audit.db`).

## 📁 Project Structure

- `main.py`: CLI entrypoint for parsing workflows and initiating allocation.
- `models.py`: Pydantic models defining `WATERWorkflow` and `ComputeNode`.
- `registry.py`: Defines the available compute nodes (mocked, but pulls GCP settings from environment).
- `allocator.py`: Logic to score and select the best eligible node based on workflow constraints.
- `prefect_translator.py`: Prefect tasks and flows that handle Docker execution and remote synchronization.
- `workflow_loader.py`: Parses YAML workflow definitions.
- `examples/`, `example2/`, `example3/`, `example4/`: Sample workloads and training scripts (e.g., OpenCV inference, scikit-learn models).
- `*.yaml`: Example workflow definitions.

## 🛠️ Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd water_prototype
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python3 -m venv env
   source env/bin/activate
   pip install -r requirements.txt
   ```

## 💻 Usage

### 1. Local Execution (Laptop)

You can run workflows that are restricted to local execution (e.g., `workflow_laptop.yaml`).

```bash
python main.py --workflow workflow_laptop.yaml
```

### 2. Remote Execution (GCP)

To execute a workload on a remote GCP VM, you must configure the SSH connection parameters via environment variables before running the workflow:

```bash
export WATER_GCP_HOST="YOUR_GCP_VM_IP"               # Replace with actual IP
export WATER_GCP_USER="ubuntu"                       # Or your specific user
export WATER_GCP_KEY_PATH="~/.ssh/gcp-water.pem"     # Path to your private key

python main.py --workflow workflow_gcp.yaml
```

*Note: For GCP execution, WATER will automatically attempt to transfer required `input_path` data to the VM using `rsync` (falling back to `scp` if needed) if `sync_input_to_remote` is `true` in the configuration.*

## 📄 Creating a New Workflow

Workflows are defined in YAML. Create a file like `my_workflow.yaml`:

```yaml
name: my_custom_workflow
execution:
  docker_image: python:3.10-slim
  entrypoint: pip install -q pandas && python /data/input/script.py
  timeout_minutes: 30
resources:
  requires_gpu: false
  min_ram_gb: 4
data:
  input_path: /path/to/local/data
  sensitivity: restricted
  must_stay_local: false     # Set to true for HIPAA/sensitive data
placement:
  target_node_id: gcp-edge   # Target specific node 'laptop-edge' or 'gcp-edge'
transfer:
  sync_input_to_remote: true
  remote_input_path: /path/to/remote/destination
```
