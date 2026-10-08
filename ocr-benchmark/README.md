# OCReS 基准测试工具

## 一句话

**同一套代码，`--backend` 切换本地/云端。**

## 文件结构

```
ocr-benchmark/
├── ocr_benchmark.py    # 主脚本（唯一入口）
├── cloud_setup.sh      # Vast.ai 云上一键部署脚本
├── test_images/        # 测试图片目录（你放图进来）
└── README.md           # 本文件
```

## 本地运行（M5/M4）

```bash
cd ocr-benchmark/

# MPS Unlimited-OCR（Mac 本地）
python3 ocr_benchmark.py --engine mps --backend auto --test-dir ./test_images/

# PaddleOCR（Mac 本地）
python3 ocr_benchmark.py --engine paddle --backend auto --test-dir ./test_images/
```

## 云上运行（Vast.ai / RunPod）

**第一步：** 把脚本和测试图上传到云实例
```bash
scp ocr_benchmark.py ubuntu@<实例IP>:~/
scp -r test_images/ ubuntu@<实例IP>:~/test_images/
```

**第二步：** SSH 到实例，跑部署脚本
```bash
ssh ubuntu@<实例IP>
bash cloud_setup.sh
```

**第三步：** 下载结果回本地
```bash
scp ubuntu@<实例IP>:~/results_mps_cloud.json ./
scp ubuntu@<实例IP>:~/results_paddle_cloud.json ./
```

## 自定义运行

```bash
# 只测 MPS，输出到自定义文件
python3 ocr_benchmark.py \
    --engine mps \
    --backend auto \
    --test-dir ./my_test_images/ \
    --output ./my_results.json

# 环境检测，不跑实际测试
python3 ocr_benchmark.py --engine mps --dry-run
```

## `--backend` 参数说明

| 参数值 | 行为 |
|--------|------|
| `auto` | CUDA > MPS > CPU 自动选择 |
| `cuda` | 强制 CUDA（云上 N 卡） |
| `mps` | 强制 MPS（Mac Apple Silicon） |
| `cpu` | 强制 CPU（debug/验证用） |

## 输出 JSON 格式

```json
{
  "engine": "mps",
  "backend": "cuda",
  "device_info": { "device_name": "NVIDIA RTX 4090", ... },
  "timestamp": "2026-07-25T14:30:00",
  "results": [
    {
      "image": "simple_en.png",
      "category": "simple_en",
      "time_seconds": 1.23,
      "peak_vram_gb": 2.5,
      "output_text": "...",
      "has_structure": false
    }
  ],
  "summary": {
    "avg_time_per_image_seconds": 1.23,
    "peak_vram_gb": 8.0,
    "deploy_time_minutes": 2.5
  }
}
```

## OCReS 评分对应

JSON 输出可直接映射到 E 维度评分：

| E 子项 | 权重 | JSON 字段 |
|--------|:----:|----------|
| 单页处理速度 | 60% | `summary.avg_time_per_image_seconds` |
| 资源占用 | 25% | `summary.peak_vram_gb` |
| 部署/启动时间 | 15% | `summary.deploy_time_minutes` |
| cost_note | 参考 | `device_info.device_name` + GPU 时价 |
