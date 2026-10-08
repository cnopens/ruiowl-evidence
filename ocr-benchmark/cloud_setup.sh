#!/bin/bash
# OCReS 云上部署脚本 — 在 Vast.ai / RunPod 等云 GPU 上使用
# 用法: bash cloud_setup.sh
#
# 前置条件:
#   1. 将 ocr_benchmark.py 和 test_images/ 上传到实例
#   2. 运行本脚本

set -e

echo "========================================"
echo " OCReS 云 GPU 环境部署"
echo "========================================"
echo ""

START_TIME=$(date +%s)

# ── 0. 系统更新 ──
echo "[1/5] 系统更新..."
apt-get update -qq && apt-get install -y -qq git wget 2>/dev/null || true

# ── 1. 安装 Python 依赖 ──
echo "[2/5] 安装 Python 依赖..."

# CUDA 版 PyTorch
pip install --quiet torch torchvision --index-url https://download.pytorch.org/whl/cu124 2>/dev/null || \
pip install --quiet torch torchvision

# MPS Unlimited-OCR 依赖
pip install --quiet transformers accelerate sentencepiece protobuf Pillow

# PaddleOCR 依赖
pip install --quiet paddlepaddle-gpu paddleocr

echo "  依赖安装完成"

# ── 2. 验证环境 ──
echo "[3/5] 验证环境..."
python3 -c "
import torch
if torch.cuda.is_available():
    print(f'  ✅ CUDA: {torch.cuda.get_device_name(0)}')
    print(f'  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
else:
    print('  ⚠️  CUDA 不可用')
"

# ── 3. 运行测试 ──
echo "[4/5] 运行 MPS Unlimited-OCR 测试..."
python3 ocr_benchmark.py \
    --engine mps \
    --backend auto \
    --test-dir ./test_images/ \
    --output ./results_mps_cloud.json

echo ""
echo "[5/5] 运行 PaddleOCR 测试..."
python3 ocr_benchmark.py \
    --engine paddle \
    --backend auto \
    --test-dir ./test_images/ \
    --output ./results_paddle_cloud.json

# ── 完成 ──
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "========================================"
echo " ✅ 全部测试完成！耗时: ${DURATION}s"
echo "========================================"
echo ""
echo "输出文件:"
echo "  MPS    → ./results_mps_cloud.json"
echo "  Paddle → ./results_paddle_cloud.json"
echo ""
echo "下载到本地:  scp ubuntu@<实例IP>:~/results_*.json ./"
