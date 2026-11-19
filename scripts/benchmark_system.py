"""
Production Benchmark & Stress Test Script for CattlePrint.
Measures 1:N Identification Throughput, Mean Latency, P95, and P99.
"""

import time
import asyncio
import io
import cv2
import numpy as np
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.database import init_db
from ml_engine.datasets.downloader import generate_synthetic_muzzle_sample


async def run_benchmark(num_requests: int = 25):
    print(f"Starting CattlePrint Biometric Benchmark ({num_requests} sequential 1:N requests)...")
    await init_db()

    # Pre-generate synthetic image buffer
    img = generate_synthetic_muzzle_sample(cattle_id=1, session=0, size=(250, 250))
    _, enc = cv2.imencode(".jpg", img)
    img_bytes = enc.tobytes()

    transport = ASGITransport(app=app)
    latencies = []

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Warmup
        await client.post(
            "/api/v1/biometrics/identify",
            files={"file": ("warmup.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        )

        total_start = time.time()
        for i in range(num_requests):
            req_start = time.time()
            res = await client.post(
                "/api/v1/biometrics/identify",
                files={"file": (f"probe_{i}.jpg", io.BytesIO(img_bytes), "image/jpeg")},
            )
            elapsed = (time.time() - req_start) * 1000.0
            latencies.append(elapsed)
            assert res.status_code == 200

        total_elapsed = time.time() - total_start

    latencies = np.array(latencies)
    print("\n" + "=" * 55)
    print("🚀 CATTLEPRINT BIOMETRIC LATENCY BENCHMARK REPORT")
    print("=" * 55)
    print(f"Total Requests Processed : {num_requests}")
    print(f"Total Time Taken         : {total_elapsed:.2f} s")
    print(f"Throughput (RPS)         : {num_requests / total_elapsed:.2f} requests/sec")
    print(f"Mean Inference Latency   : {np.mean(latencies):.2f} ms")
    print(f"Median Latency (P50)     : {np.median(latencies):.2f} ms")
    print(f"95th Percentile (P95)    : {np.percentile(latencies, 95):.2f} ms")
    print(f"99th Percentile (P99)    : {np.percentile(latencies, 99):.2f} ms")
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(run_benchmark(num_requests=25))
