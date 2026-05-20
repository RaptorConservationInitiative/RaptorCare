# GPU Management Documentation

## 🎮 Dual GPU Setup (T600 / GTX 1650)

RaptorCare now supports dual GPU management with intelligent task allocation:

### GPU Allocation Strategy

| GPU 0 | GPU 1 | Fallback |
|-------|-------|----------|
| **LLM** (Ollama) | **Neural Networks** | GPU 0 if GPU 1 unavailable |
| Inference only | Image analysis, Pattern recognition, Data processing | Uses least loaded GPU |

### Systemd Auto-Startup

Both services run automatically on boot:

```bash
# Check status
sudo systemctl status raptorcare
sudo systemctl status ollama

# View logs
journalctl -u raptorcare -f
journalctl -u ollama -f

# Restart services
sudo systemctl restart raptorcare
sudo systemctl restart ollama


Environment Variables

Ollama with Dual GPU Support:

CUDA_VISIBLE_DEVICES=0,1    # Both GPUs visible
OLLAMA_NUM_PARALLEL=2        # Allow parallel requests
OLLAMA_MODELS=/var/lib/ollama/models


GPU Status Monitoring

# Check GPU usage
nvidia-smi

# Check GPU memory per process
nvidia-smi pmon

# Watch GPU usage in real-time
watch -n 1 nvidia-smi


Manual FastAPI Start (Development)

cd /opt/raptorcare
source venv/bin/activate
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload


Manual Ollama Start (Development)

# Set GPUs to use
export CUDA_VISIBLE_DEVICES=0,1

# Start Ollama
ollama serve

GPU Task Examples

Python Code:
from server.gpu import GPUPool

# Allocate GPU for LLM task
gpu_id = GPUPool.allocate_gpu_for_task(GPUPool.GPUType.LLM)
# → Uses GPU 0

# Allocate GPU for neural network task
gpu_id = GPUPool.allocate_gpu_for_task(GPUPool.GPUType.NEURAL_NET)
# → Uses GPU 1 (or GPU 0 if GPU 1 unavailable)

# Allocate GPU for analysis (uses least loaded)
gpu_id = GPUPool.allocate_gpu_for_task(GPUPool.GPUType.ANALYSIS)

# Check GPU memory usage
usage = GPUPool.get_gpu_memory_usage(0)
print(f"GPU 0: {usage['utilization_percent']}% utilized")

Installation

    Setup Systemd Services:
    bash

    sudo bash scripts/setup_systemd.sh

    Start Services:
    bash

    sudo systemctl start raptorcare
    sudo systemctl start ollama

    Enable Auto-Start:
    bash

    sudo systemctl enable raptorcare
    sudo systemctl enable ollama

    Verify Running:
    bash

    sudo systemctl status raptorcare
    sudo systemctl status ollama

    Monitor Logs:
    bash

    journalctl -u raptorcare -f
    journalctl -u ollama -f

Troubleshooting
Services not starting?
bash

# Check service logs
journalctl -u raptorcare -n 50 --no-pager
journalctl -u ollama -n 50 --no-pager

GPU not detected?
bash

# Check NVIDIA drivers
nvidia-smi

# Verify CUDA
python -c "import torch; print(torch.cuda.is_available())"

Port already in use?
bash

# Change port in raptorcare.service
sudo nano /etc/systemd/system/raptorcare.service
# Change: --port 8000 to another port
# Then reload
sudo systemctl daemon-reload
sudo systemctl restart raptorcare

Check resource usage
bash

# FastAPI process
ps aux | grep uvicorn

# Ollama process
ps aux | grep ollama

# GPU processes
lsof | grep GPU




