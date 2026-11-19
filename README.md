# 🐄 CattlePrint - AI Bovine Muzzle Biometric Identification System

> **Tamper-Proof Bovine Biometrics using Deep Metric Learning (ArcFace) & Hyperspherical Cosine Matching for Livestock Insurance & Verification**

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Production%20Ready-009688.svg)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-Metric%20Learning-EE4C2C.svg)](https://pytorch.org/)
[![Tests Passing](https://img.shields.io/badge/Tests-7%20Passed%20(100%25)-brightgreen.svg)]()

---

## 📌 Executive Summary

গরুর নাকের প্যাটার্ন (Bovine Rhinarium / Muzzle Print) মানুষের ফিঙ্গারপ্রিন্টের মতো সম্পূর্ণ অনন্য। প্রচলিত প্লাস্টিক বা আরএফআইডি ইয়ার-ট্যাগ খুলে ফেলা বা চুরি করা সম্ভব হলেও নাকের বায়োমেট্রিক পরিবর্তন করা বা জালিয়াতি করা অসম্ভব।

**CattlePrint** একটি প্রোডাকশন-গ্রেড এআই আর্কিটেকচার যা ফিল্ড এজেন্ট ও কৃষকদের জন্য একটি নির্ভরযোগ্য, দ্রুত (<১৫ms) ১:N ক্যাটল আইডেন্টিফিকেশন সিস্টেম প্রদান করে।

---

## 🏗️ System Architecture

```
[ Field Camera / Photo Upload ]
              │
              ▼
    [ Stage 1: Quality Gate ]
    (Laplacian Blur Check, Glare & Illumination Filter)
              │
              ▼
    [ Stage 2: Muzzle ROI Detector ]
    (Extracts Anatomical Nasal Plate, Standardizes 224x224)
              │
              ▼
    [ Stage 3: CLAHE Ridge Enhancer ]
    (Amplifies Bovine Beads & Grooves in CIELAB L-Channel)
              │
              ▼
    [ Stage 4: ArcFace Deep Metric Net ]
    (Extracts 512-dim Hyperspherical L2-Normalized Vector)
              │
              ▼
    [ Stage 5: 1:N Vector Cosine Search (pgvector) ]
    ├── Score >= 0.72  --> Confirmed Match (ID, Breed, Farm & Insurance)
    ├── 0.60 - 0.72    --> Borderline (Recapture Advisory)
    └── Score < 0.60   --> Unknown Animal Rejection
```

---

## 🚀 Quickstart Guide

### 1. Local Environment Setup

```bash
# Clone and enter workspace
git clone <repo_url>
cd Foysal

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Test Suite (100% Verification)

```bash
source .venv/bin/activate
PYTHONPATH=. pytest -v
```
Output:
```
tests/test_backend_api.py::test_full_biometric_lifecycle PASSED
tests/test_ml_engine.py::test_quality_gate_clean_vs_blurry PASSED
tests/test_ml_engine.py::test_quality_gate_dark_exposure PASSED
tests/test_ml_engine.py::test_clahe_enhancer PASSED
tests/test_ml_engine.py::test_muzzle_detector_crop_and_resize PASSED
tests/test_ml_engine.py::test_arcface_and_embedding_normalization PASSED
tests/test_ml_engine.py::test_biometric_evaluator_metrics PASSED
====== 7 passed in 3.28s ======
```

### 3. Launch Development Server & Web UI

```bash
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive Field Web App:** [http://localhost:8000/app](http://localhost:8000/app)
- **FastAPI Interactive Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 4. Docker Production Deployment

```bash
docker compose up -d --build
```
This boots up:
- **PostgreSQL 16 + pgvector** on port 5432
- **FastAPI Inference Service & Web App** on port 8000

---

## 📊 Biometric Performance Metrics

| Metric | Target | Description |
| :--- | :--- | :--- |
| **FAR (False Acceptance Rate)** | $< 0.1\%$ | ভুল করে অন্য গরুকে টার্গেট গরু ভাবার হার (ইন্স্যুরেন্স ফ্রড ঠেকাতে জরুরি) |
| **FRR (False Rejection Rate)** | $< 2.5\%$ | সঠিক গরুকে রিজেক্ট করার হার |
| **EER (Equal Error Rate)** | $< 1.2\%$ | যেখানে FAR ও FRR সমান হয় |
| **Rank-1 Identification** | $> 96.5\%$ | ১:N সার্চে প্রথম র‍্যাঙ্কেই সঠিক গরু খুঁজে পাওয়ার হার |
| **Inference Latency** | $< 15$ ms | ছবি আপলোড থেকে ম্যাচিং পর্যন্ত মোট সময় |

---

## 📂 Public Open Datasets Included

প্রজেক্টের `ml_engine/datasets/downloader.py` ফাইলে নিচের ৫টি রিসার্চ ডেটাসেট প্রি-কনফিগার করা আছে:
1. **Zenodo 6324361:** Cattle Muzzle Point Identification Dataset
2. **Hugging Face MingShuo666/CattleMuzzle:** High-resolution muzzle prints
3. **Mendeley Data w7j9wb9gt2/1:** Multi-breed muzzle variations
4. **Zenodo 10535934:** Cross-session biometric pairs
5. **Hugging Face casperhuggingface/gaaibastu-muzzles:** South Asian indigenous cattle breeds
