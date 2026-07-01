#!/usr/bin/env python3
"""Benchmark FastAPI /predict latency for resume metrics."""

from __future__ import annotations

import argparse
import statistics
import time

import httpx

SAMPLE = {
    "instances": [
        {
            "fixed_acidity": 7.4,
            "volatile_acidity": 0.7,
            "citric_acid": 0.0,
            "residual_sugar": 1.9,
            "chlorides": 0.076,
            "free_sulfur_dioxide": 11.0,
            "total_sulfur_dioxide": 34.0,
            "density": 0.9978,
            "pH": 3.51,
            "sulphates": 0.56,
            "alcohol": 9.4,
            "wine_type": 0,
        }
    ]
}


def benchmark(base_url: str, n_requests: int = 200) -> dict:
  latencies_ms: list[float] = []
  with httpx.Client(base_url=base_url, timeout=10.0) as client:
    client.get("/health").raise_for_status()
    start = time.perf_counter()
    for _ in range(n_requests):
      t0 = time.perf_counter()
      response = client.post("/predict", json=SAMPLE)
      response.raise_for_status()
      latencies_ms.append((time.perf_counter() - t0) * 1000)
    elapsed = time.perf_counter() - start

  latencies_ms.sort()
  p95_idx = int(0.95 * len(latencies_ms)) - 1
  return {
      "requests": n_requests,
      "throughput_rps": round(n_requests / elapsed, 1),
      "latency_ms_mean": round(statistics.mean(latencies_ms), 2),
      "latency_ms_p50": round(latencies_ms[len(latencies_ms) // 2], 2),
      "latency_ms_p95": round(latencies_ms[p95_idx], 2),
      "latency_ms_max": round(max(latencies_ms), 2),
  }


def main() -> None:
  parser = argparse.ArgumentParser(description="Benchmark inference API")
  parser.add_argument("--url", default="http://127.0.0.1:8000")
  parser.add_argument("-n", "--requests", type=int, default=200)
  args = parser.parse_args()

  stats = benchmark(args.url, args.requests)
  print("Inference benchmark (local FastAPI, single worker):")
  for key, value in stats.items():
    print(f"  {key}: {value}")


if __name__ == "__main__":
  main()
