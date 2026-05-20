"""
GPU Pool Manager for Dual GPU Optimization
Manages GPU allocation between LLM and Neural Networks
"""

import torch
import psutil
from enum import Enum
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class GPUType(Enum):
    """GPU task types"""
    LLM = "llm"                    # Reserved for Ollama LLM on GPU 0
    NEURAL_NET = "neural_net"      # Image analysis, pattern recognition on GPU 1
    ANALYSIS = "analysis"          # Sensor data, general analysis (auto-select)


@dataclass
class GPUInfo:
    """GPU information"""
    device_id: int
    name: str
    total_memory: float
    used_memory: float
    utilization: float

    @property
    def free_memory(self) -> float:
        return self.total_memory - self.used_memory

    @property
    def available_percentage(self) -> float:
        return (self.free_memory / self.total_memory) * 100


class GPUPool:
    """
    Intelligent GPU Pool Manager
    - GPU 0 (T600/GTX 1650): LLM (Ollama) - RESERVED
    - GPU 1 (T600/GTX 1650): Neural Networks (Image, Sensors)
    - Automatic fallback if GPU 1 overloaded
    """

    # GPU Configuration
    GPU_COUNT = 2
    GPU_LLM = 0           # T600 or GTX 1650
    GPU_NEURAL = 1        # T600 or GTX 1650

    # Memory thresholds
    GPU_MEMORY_THRESHOLD = 0.85  # 85% = fallback to other GPU

    @classmethod
    def is_available(cls) -> bool:
        """Check if CUDA GPUs are available"""
        return torch.cuda.is_available()

    @classmethod
    def get_gpu_count(cls) -> int:
        """Get number of GPUs"""
        if torch.cuda.is_available():
            return torch.cuda.device_count()
        return 0

    @classmethod
    def get_gpu_info(cls, gpu_id: int) -> Optional[GPUInfo]:
        """Get detailed GPU information"""
        if not torch.cuda.is_available() or gpu_id >= cls.get_gpu_count():
            return None

        try:
            props = torch.cuda.get_device_properties(gpu_id)

            # Memory info
            total_memory = props.total_memory / (1024 ** 3)  # Convert to GB

            # Current usage
            current_memory = torch.cuda.memory_allocated(gpu_id) / (1024 ** 3)

            # Utilization (rough estimate)
            utilization = (current_memory / total_memory) * 100

            return GPUInfo(
                device_id=gpu_id,
                name=torch.cuda.get_device_name(gpu_id),
                total_memory=total_memory,
                used_memory=current_memory,
                utilization=utilization
            )
        except Exception as e:
            logger.error(f"Error getting GPU {gpu_id} info: {e}")
            return None

    @classmethod
    def select_best_gpu(cls, task_type: GPUType) -> int:
        """
        Select best GPU for task type

        Args:
            task_type: Type of task (LLM, NEURAL_NET, ANALYSIS)

        Returns:
            GPU device ID (0 or 1)
        """
        if not cls.is_available():
            logger.warning("No GPUs available, using CPU")
            return -1  # CPU

        # LLM tasks always use GPU 0
        if task_type == GPUType.LLM:
            return cls.GPU_LLM

        # Neural Network tasks prefer GPU 1, fallback to GPU 0 if overloaded
        if task_type == GPUType.NEURAL_NET:
            gpu_1_info = cls.get_gpu_info(cls.GPU_NEURAL)

            if gpu_1_info and gpu_1_info.available_percentage > (100 - cls.GPU_MEMORY_THRESHOLD * 100):
                logger.warning(
                    f"GPU {cls.GPU_NEURAL} at {gpu_1_info.utilization:.1f}% utilization, "
                    f"falling back to GPU {cls.GPU_LLM}"
                )
                return cls.GPU_LLM

            return cls.GPU_NEURAL

        # Analysis tasks use GPU with lowest load
        if task_type == GPUType.ANALYSIS:
            gpu_0_info = cls.get_gpu_info(cls.GPU_LLM)
            gpu_1_info = cls.get_gpu_info(cls.GPU_NEURAL)

            if not gpu_0_info or not gpu_1_info:
                return cls.GPU_LLM

            # Select GPU with lower utilization
            if gpu_0_info.utilization <= gpu_1_info.utilization:
                return cls.GPU_LLM
            else:
                return cls.GPU_NEURAL

        return cls.GPU_LLM

    @classmethod
    def print_gpu_status(cls) -> None:
        """Print GPU status"""
        if not cls.is_available():
            print("❌ No GPUs available")
            return

        print("\n" + "="*60)
        print("🎮 GPU STATUS")
        print("="*60)

        for i in range(cls.get_gpu_count()):
            info = cls.get_gpu_info(i)
            if info:
                role = "🤖 LLM (Ollama)" if i == cls.GPU_LLM else "🧠 Neural Networks"
                print(f"\nGPU {i} ({role})")
                print(f"  Name: {info.name}")
                print(f"  Total Memory: {info.total_memory:.2f} GB")
                print(f"  Used Memory: {info.used_memory:.2f} GB")
                print(f"  Free Memory: {info.free_memory:.2f} GB")
                print(f"  Utilization: {info.utilization:.1f}%")

        print("\n" + "="*60 + "\n")

    @classmethod
    def get_memory_summary(cls) -> dict:
        """Get GPU memory summary"""
        summary = {
            "gpu_count": cls.get_gpu_count(),
            "gpus": []
        }

        for i in range(cls.get_gpu_count()):
            info = cls.get_gpu_info(i)
            if info:
                summary["gpus"].append({
                    "device_id": i,
                    "name": info.name,
                    "total_memory_gb": round(info.total_memory, 2),
                    "used_memory_gb": round(info.used_memory, 2),
                    "free_memory_gb": round(info.free_memory, 2),
                    "utilization_percent": round(info.utilization, 1)
                })

        return summary

    @classmethod
    def set_device(cls, gpu_id: int) -> None:
        """Set CUDA device"""
        if cls.is_available() and gpu_id >= 0:
            torch.cuda.set_device(gpu_id)
            logger.info(f"CUDA device set to GPU {gpu_id}: {torch.cuda.get_device_name(gpu_id)}")


# Example usage
if __name__ == "__main__":
    print("🦅 RaptorCare GPU Pool Manager")

    # Print status
    GPUPool.print_gpu_status()

    # Get summary
    summary = GPUPool.get_memory_summary()
    print(f"GPU Summary: {summary}")

    # Select best GPU for tasks
    llm_gpu = GPUPool.select_best_gpu(GPUType.LLM)
    print(f"✅ LLM Task → GPU {llm_gpu}")

    nn_gpu = GPUPool.select_best_gpu(GPUType.NEURAL_NET)
    print(f"✅ Neural Network Task → GPU {nn_gpu}")

    analysis_gpu = GPUPool.select_best_gpu(GPUType.ANALYSIS)
    print(f"✅ Analysis Task → GPU {analysis_gpu}")
