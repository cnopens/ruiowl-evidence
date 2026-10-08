#!/usr/bin/env python3
"""
OCReS 基准测试脚本 —— 统一入口

用法（云上 CUDA）:
    python3 ocr_benchmark.py --engine mps    --backend auto --test-dir ./test_images/ --output result.json
    python3 ocr_benchmark.py --engine paddle  --backend auto --test-dir ./test_images/ --output result.json

用法（本地 M5/M4 MPS）:
    python3 ocr_benchmark.py --engine mps    --backend mps  --test-dir ./test_images/ --output result.json

用法（仅测速度/资源，不装模型）:
    python3 ocr_benchmark.py --engine paddle --backend cpu --test-dir ./test_images/ --dry-run

--backend 参数:
    auto  : 自动检测 CUDA → 用 CUDA, Apple Silicon → 用 MPS, 否则 CPU
    cuda  : 强制 CUDA（云上）
    mps   : 强制 MPS（Mac 本地）
    cpu   : 强制 CPU

依赖（云上 CUDA 安装）:
    pip install torch transformers paddlepaddle-gpu paddleocr
依赖（Mac MPS 安装）:
    pip install torch transformers paddlepaddle paddleocr

输出 JSON 格式:
    {
        "engine": "mps" | "paddle",
        "backend": "cuda" | "mps" | "cpu",
        "device_name": "NVIDIA A100...",
        "timestamp": "...",
        "test_images": ["simple_en.png", ...],
        "results": [
            {
                "image": "simple_en.png",
                "category": "simple_en",
                "time_seconds": 2.5,
                "peak_vram_gb": 2.1,
                "cer": 0.026,
                "output_text": "...",
                "has_structure": false
            },
            ...
        ],
        "summary": {
            "avg_time_per_page": 3.2,
            "peak_vram_gb": 8.5,
            "deploy_time_minutes": 5.0,
            "total_pages": 5
        }
    }
"""

import argparse
import json
import os
import sys
import time
import subprocess
from pathlib import Path

# ──────────────────────────── 后端检测 ────────────────────────────

def detect_backend(force=None):
    """检测可用推理后端"""
    if force and force != "auto":
        return force

    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            print(f"[检测] CUDA 可用: {device_name}")
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            print("[检测] MPS 可用 (Apple Silicon)")
            return "mps"
        else:
            print("[检测] 无 GPU，使用 CPU")
            return "cpu"
    except ImportError:
        print("[检测] torch 未安装，使用 CPU")
        return "cpu"


def get_device_info(backend):
    """获取设备详细信息"""
    info = {"backend": backend}
    try:
        import torch
        if backend == "cuda":
            info["device_name"] = torch.cuda.get_device_name(0)
            info["vram_total_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)
            info["cuda_version"] = torch.version.cuda
        elif backend == "mps":
            info["device_name"] = "Apple Silicon (MPS)"
            info["vram_total_gb"] = "shared (system RAM)"
    except Exception as e:
        info["device_error"] = str(e)
    return info


# ──────────────────────────── MPS Unlimited-OCR 引擎 ────────────────────────────

class MPSEngine:
    """MPS Unlimited-OCR 封装"""

    def __init__(self, backend):
        self.backend = backend
        self.model = None
        self.tokenizer = None
        self.device = None
        self.model_name = "baidu/Unlimited-OCR"  # HF 官方名
        self.prompt = "<image>document parsing."

    def load(self):
        """加载模型（使用 model.infer() API，不是标准 generate）"""
        t0 = time.time()
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            self.device = torch.device(
                "cuda" if self.backend == "cuda"
                else "mps" if self.backend == "mps"
                else "cpu"
            )

            dtype = torch.bfloat16 if self.device.type in ("cuda", "mps") else torch.float32
            print(f"[MPS] 加载模型 {self.model_name} → {self.device} (dtype={dtype}) ...")

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, trust_remote_code=True
            )
            self.model = AutoModel.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                use_safetensors=True,
                torch_dtype=dtype,
            ).to(self.device).eval()

            load_time = time.time() - t0
            print(f"[MPS] 模型加载完成: {load_time:.1f}s")
            return load_time
        except Exception as e:
            print(f"[MPS] 模型加载失败: {e}")
            sys.exit(1)

    def process_image(self, image_path):
        """处理单张图片 — 使用 model.infer() 自定义 API"""
        import torch
        from PIL import Image
        t0 = time.time()

        # Unlimited-OCR 的 infer() 接收文件路径或 PIL Image
        try:
            result = self.model.infer(
                self.tokenizer,
                prompt=self.prompt,
                image_file=image_path,  # 直接传路径
                output_path="/tmp",
                base_size=1024,
                image_size=640,
                crop_mode=True,
                eval_mode=True,
                max_length=8192,
                temperature=0.0,
                save_results=False,
            )
        except TypeError:
            # 有的版本 infer() 不接受全部参数
            result = self.model.infer(
                self.tokenizer,
                prompt=self.prompt,
                image_file=image_path,
                max_length=8192,
            )

        elapsed = time.time() - t0
        text = str(result) if result else ""

        # 检测是否有结构化输出 (HTML table 等)
        has_structure = "<table>" in text or "<tr>" in text or "bbox" in text.lower()

        # 显存采样（粗略）
        vram = 0
        if self.backend == "cuda":
            vram = round(torch.cuda.max_memory_allocated() / 1e9, 2)
            torch.cuda.reset_peak_memory_stats()

        return {
            "time_seconds": round(elapsed, 3),
            "peak_vram_gb": vram,
            "output_text": text[:500],  # 截断长输出
            "has_structure": has_structure,
        }


# ──────────────────────────── PaddleOCR 引擎 ────────────────────────────

class PaddleEngine:
    """PaddleOCR 封装"""

    def __init__(self, backend):
        self.backend = backend
        self.ocr = None

    def load(self):
        """加载模型"""
        t0 = time.time()
        try:
            # PaddleOCR 自动检测 GPU
            os.environ["CUDA_VISIBLE_DEVICES"] = "0" if self.backend == "cuda" else "-1"

            from paddleocr import PaddleOCR
            print(f"[Paddle] 加载模型 (backend={self.backend}) ...")
            self.ocr = PaddleOCR(use_angle_cls=True, lang="ch")
            load_time = time.time() - t0
            print(f"[Paddle] 模型加载完成: {load_time:.1f}s")
            return load_time
        except Exception as e:
            print(f"[Paddle] 模型加载失败: {e}")
            sys.exit(1)

    def process_image(self, image_path):
        """处理单张图片"""
        t0 = time.time()
        result = self.ocr.ocr(str(image_path))
        elapsed = time.time() - t0

        # 解析结果（兼容 PaddleOCR 3.x 输出格式）
        text_parts = []
        has_structure = False
        if result and result[0]:
            for line in result[0]:
                # PaddleOCR 3.x 输出格式: [[bbox, (text, confidence)], ...]
                if len(line) == 2:
                    bbox, text_conf = line
                    if isinstance(text_conf, (list, tuple)) and len(text_conf) == 2:
                        text, confidence = text_conf
                        text_parts.append(text)
                elif len(line) == 3:
                    # 旧格式兼容
                    bbox, text, confidence = line
                    text_parts.append(text)

        output_text = "\n".join(text_parts)

        # PaddleOCR 输出始终是纯文本，没有 HTML table 结构
        # 但可能有 bbox 坐标，也算一定结构信息
        if result and result[0]:
            has_structure = True  # Paddle 有 bbox 坐标

        return {
            "time_seconds": round(elapsed, 3),
            "peak_vram_gb": 0,  # Paddle 不直接暴露显存
            "output_text": output_text[:500],
            "has_structure": has_structure,
        }


# ──────────────────────────── CER 计算 ────────────────────────────

def compute_cer(reference, hypothesis):
    """计算 CER (字符错误率)"""
    if not reference:
        return 1.0
    if not hypothesis:
        return 1.0

    # 编辑距离 (Levenshtein)
    ref = reference.strip()
    hyp = hypothesis.strip()

    m, n = len(ref), len(hyp)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost
            )

    edit_dist = dp[m][n]
    cer = edit_dist / max(m, 1)
    return round(cer, 4)


# ──────────────────────────── 测试集 autolabel ────────────────────────────

def categorize_image(filename):
    """根据文件名判断测试类别"""
    name = filename.lower()
    if "simple_en" in name or "english" in name or "en_" in name:
        return "simple_en"
    elif "simple_zh" in name or "chinese" in name or "zh_" in name or "中文" in name:
        return "simple_zh"
    elif "table" in name or "表格" in name:
        return "table"
    elif "paper" in name or "论文" in name or "双栏" in name or "column" in name:
        return "paper"
    elif "invoice" in name or "发票" in name:
        return "invoice"
    elif "multi" in name or "多页" in name or "pdf" in name:
        return "multipage"
    else:
        return "other"


# ──────────────────────────── 主流程 ────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OCReS 基准测试工具")
    parser.add_argument("--engine", choices=["mps", "paddle"], required=True,
                        help="OCR 引擎")
    parser.add_argument("--backend", choices=["auto", "cuda", "mps", "cpu"], default="auto",
                        help="推理后端 (auto=自动检测)")
    parser.add_argument("--test-dir", type=str, default="./test_images",
                        help="测试图片目录")
    parser.add_argument("--output", type=str, default=None,
                        help="输出 JSON 文件路径 (默认打印到 stdout)")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅测试环境，不加载模型")
    args = parser.parse_args()

    # ── 1. 检测后端 ──
    backend = detect_backend(args.backend)
    device_info = get_device_info(backend)
    print(f"[配置] engine={args.engine}, backend={backend}")
    print(f"[配置] test_dir={args.test_dir}")
    print()

    # ── 2. 寻找测试图片 ──
    test_dir = Path(args.test_dir)
    if not test_dir.exists():
        print(f"[错误] 测试目录不存在: {test_dir}")
        print("请将测试图片放入该目录，或使用 --test-dir 指定路径")
        sys.exit(1)

    image_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
    test_images = sorted([
        p for p in test_dir.iterdir()
        if p.suffix.lower() in image_exts
        and not p.name.startswith("._")  # 跳过 Mac 隐藏文件
    ])

    if not test_images:
        print(f"[错误] 测试目录中没有图片文件: {test_dir}")
        sys.exit(1)

    print(f"[测试集] 找到 {len(test_images)} 张图片:")
    for img in test_images:
        cat = categorize_image(img.name)
        print(f"  - {img.name}  [{cat}]")
    print()

    # ── 3. 统计部署时间（首次加载） ──
    deploy_t0 = time.time()

    if args.dry_run:
        print("[DRY-RUN] 跳过模型加载和处理")
        result = {
            "engine": args.engine,
            "backend": backend,
            "device_info": device_info,
            "dry_run": True,
            "test_images": [str(p) for p in test_images],
            "test_dir": str(test_dir),
            "message": "DRY-RUN 完成。安装依赖后去掉 --dry-run 执行实际测试。",
        }
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n[完成] dry-run 结果写入: {args.output}")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 初始化引擎
    if args.engine == "mps":
        engine = MPSEngine(backend)
    else:
        engine = PaddleEngine(backend)

    load_time = engine.load()

    # 部署时间 = 模型加载时间 (脚本执行启动到模型就绪)
    deploy_time = time.time() - deploy_t0
    print(f"\n[部署] 总耗时: {deploy_time:.1f}s (模型加载 {load_time:.1f}s)")
    print()

    # ── 4. 逐图处理 ──
    results = []
    for img_path in test_images:
        cat = categorize_image(img_path.name)
        print(f"[处理] {img_path.name} ...", end=" ", flush=True)

        try:
            proc_result = engine.process_image(img_path)
            print(f"完成 ({proc_result['time_seconds']:.2f}s)")
            results.append({
                "image": img_path.name,
                "category": cat,
                **proc_result,
            })
        except Exception as e:
            print(f"失败: {e}")
            results.append({
                "image": img_path.name,
                "category": cat,
                "time_seconds": -1,
                "peak_vram_gb": 0,
                "output_text": f"ERROR: {e}",
                "has_structure": False,
                "error": str(e),
            })

    # ── 5. 汇总 ──
    valid_results = [r for r in results if r["time_seconds"] > 0]
    if valid_results:
        avg_time = sum(r["time_seconds"] for r in valid_results) / len(valid_results)
        peak_vram = max(r["peak_vram_gb"] for r in valid_results) if any(
            r["peak_vram_gb"] for r in valid_results
        ) else 0
    else:
        avg_time = 0
        peak_vram = 0

    summary = {
        "total_images": len(test_images),
        "successful": len(valid_results),
        "failed": len(results) - len(valid_results),
        "avg_time_per_image_seconds": round(avg_time, 3),
        "peak_vram_gb": peak_vram,
        "deploy_time_minutes": round(deploy_time / 60, 2),
        "deploy_time_seconds": round(deploy_time, 1),
    }

    # ── 6. 输出 ──
    result = {
        "engine": args.engine,
        "backend": backend,
        "device_info": device_info,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "test_dir": str(test_dir),
        "test_images": [str(p) for p in test_images],
        "results": results,
        "summary": summary,
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n[完成] 结果写入: {args.output}")
    else:
        print("\n" + "=" * 60)
        print("摘要:")
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    # 打印汇总表
    print("\n逐图结果:")
    print(f"{'图片':<25} {'耗时(s)':<10} {'显存(GB)':<10} {'结构输出':<10}")
    print("-" * 55)
    for r in results:
        t = r["time_seconds"] if r["time_seconds"] > 0 else "FAIL"
        v = r["peak_vram_gb"] if r["peak_vram_gb"] else "-"
        s = "✅" if r["has_structure"] else "❌"
        print(f"{r['image']:<25} {str(t):<10} {str(v):<10} {s:<10}")


if __name__ == "__main__":
    main()
