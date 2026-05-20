#!/bin/bash
# Setup Ollama LLM on GPU

set -e

echo "🤖 RaptorCare Ollama LLM Setup"
echo "=============================="

# Detect GPU
echo "Detecting GPU..."

if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected"
    GPU_TYPE="nvidia"
    GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
    echo "   Found $GPU_COUNT GPU(s)"

    # For LXC passthrough, check devices
    ls -la /dev/nvidia* 2>/dev/null && echo "   GPU devices accessible in LXC" || echo "   ⚠️  GPU devices may not be accessible"
else
    echo "❌ No NVIDIA GPU detected"
    exit 1
fi

# Install Ollama
echo ""
echo "📦 Installing Ollama..."

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
fi

if [ "$OS" == "ubuntu" ] || [ "$OS" == "debian" ]; then
    curl -fsSL https://ollama.ai/install.sh | sh
else
    echo "Please install Ollama manually from https://ollama.ai"
    exit 1
fi

# Download model
echo ""
echo "🤖 Downloading neural-chat model (small, optimized for edge)"
echo "This may take a few minutes..."

ollama pull neural-chat

# Alternative models (uncomment as needed)
# ollama pull mistral  # Faster, good for edge
# ollama pull llama2   # Better quality, larger

# Test LLM
echo ""
echo "Testing LLM..."
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"neural-chat","prompt":"Test"}' \
  -o /dev/null -s && echo "✅ LLM is working" || echo "❌ LLM test failed"

echo ""
echo "✅ Ollama setup complete!"
echo ""
echo "Configuration:"
echo "  Model: neural-chat"
echo "  Base URL: http://localhost:11434"
echo "  GPU: $GPU_TYPE"
echo ""
echo "To start Ollama:"
echo "  ollama serve"
echo ""
echo "To test in Python:"
echo "  python3 -c 'from server.llm import get_llm; llm = get_llm(); print(llm.check_connection())'"
