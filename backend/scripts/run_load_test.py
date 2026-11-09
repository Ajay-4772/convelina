#!/usr/bin/env python3
"""
Consolith Performance & Load Testing Suite
Measures:
- Throughput (Requests per second)
- Latency percentiles (min, avg, p50, p90, p95, p99, max)
- Success / Error rates
- Baseline, Moderate, High, Stress, Sustained, and Recovery workloads.
Outputs structured JSON and human-readable summary.
"""

import asyncio
import time
import statistics
import json
import uuid
import httpx
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

# Generate isolated test user token for authenticated benchmarking
BENCH_UID = f"bench_user_{uuid.uuid4().hex[:8]}"
BENCH_TOKEN = f"test_token_:{BENCH_UID}:bench.user@perf.test:Benchmark User"

ENDPOINTS = [
    {
        "name": "Health Probes (/health)",
        "method": "GET",
        "url": f"{BASE_URL}/health",
        "headers": {},
        "weight": 25
    },
    {
        "name": "PKI Public Keys (/api/v1/pki/keys)",
        "method": "GET",
        "url": f"{BASE_URL}/api/v1/pki/keys",
        "headers": {"Authorization": f"Bearer {BENCH_TOKEN}"},
        "weight": 25
    },
    {
        "name": "Forms Repository (/api/v1/knowledge/forms)",
        "method": "GET",
        "url": f"{BASE_URL}/api/v1/knowledge/forms",
        "headers": {"Authorization": f"Bearer {BENCH_TOKEN}"},
        "weight": 25
    },
    {
        "name": "Authenticated User Profile (/api/v1/auth/me)",
        "method": "GET",
        "url": f"{BASE_URL}/api/v1/auth/me",
        "headers": {"Authorization": f"Bearer {BENCH_TOKEN}"},
        "weight": 25
    }
]

STAGE_CONFIGS = [
    {"stage": "Baseline Load", "concurrency": 1, "total_requests": 60},
    {"stage": "Moderate Load", "concurrency": 5, "total_requests": 200},
    {"stage": "High Load", "concurrency": 15, "total_requests": 450},
    {"stage": "Stress Load", "concurrency": 30, "total_requests": 600},
    {"stage": "Sustained Load", "concurrency": 20, "total_requests": 800},
    {"stage": "Recovery Verification", "concurrency": 1, "total_requests": 40},
]

async def send_request(client: httpx.AsyncClient, endpoint: dict) -> dict:
    start_time = time.perf_counter()
    status_code = 0
    success = False
    error_msg = None
    try:
        res = await client.request(
            method=endpoint["method"],
            url=endpoint["url"],
            headers=endpoint["headers"],
            timeout=15.0
        )
        status_code = res.status_code
        if 200 <= status_code < 400:
            success = True
        else:
            error_msg = f"HTTP {status_code}"
    except Exception as e:
        error_msg = str(e)
    duration_ms = (time.perf_counter() - start_time) * 1000.0
    return {
        "status_code": status_code,
        "success": success,
        "duration_ms": duration_ms,
        "endpoint": endpoint["name"],
        "error": error_msg
    }

async def run_stage(client: httpx.AsyncClient, stage_info: dict) -> dict:
    stage_name = stage_info["stage"]
    concurrency = stage_info["concurrency"]
    total_reqs = stage_info["total_requests"]
    
    print(f"\n---> Running {stage_name} (Concurrency: {concurrency}, Requests: {total_reqs})...")
    
    semaphore = asyncio.Semaphore(concurrency)
    results = []
    
    async def worker(req_idx: int):
        endpoint = ENDPOINTS[req_idx % len(ENDPOINTS)]
        async with semaphore:
            res = await send_request(client, endpoint)
            results.append(res)

    wall_start = time.perf_counter()
    tasks = [worker(i) for i in range(total_reqs)]
    await asyncio.gather(*tasks)
    wall_duration = time.perf_counter() - wall_start
    
    # Calculate statistics
    durations = [r["duration_ms"] for r in results]
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    
    durations.sort()
    count = len(durations)
    
    def percentile(p):
        if not count:
            return 0.0
        idx = int(round((p / 100.0) * count - 0.5))
        idx = max(0, min(idx, count - 1))
        return durations[idx]

    avg_lat = statistics.mean(durations) if count else 0.0
    p50_lat = percentile(50)
    p90_lat = percentile(90)
    p95_lat = percentile(95)
    p99_lat = percentile(99)
    min_lat = durations[0] if count else 0.0
    max_lat = durations[-1] if count else 0.0
    rps = count / wall_duration if wall_duration > 0 else 0.0
    error_rate = (len(failures) / count * 100.0) if count else 0.0
    
    stage_result = {
        "stage": stage_name,
        "concurrency": concurrency,
        "total_requests": count,
        "successful_requests": len(successes),
        "failed_requests": len(failures),
        "error_rate_pct": round(error_rate, 2),
        "duration_sec": round(wall_duration, 2),
        "throughput_rps": round(rps, 2),
        "latency_ms": {
            "min": round(min_lat, 2),
            "avg": round(avg_lat, 2),
            "p50": round(p50_lat, 2),
            "p90": round(p90_lat, 2),
            "p95": round(p95_lat, 2),
            "p99": round(p99_lat, 2),
            "max": round(max_lat, 2)
        }
    }
    
    print(f"     [Result] {stage_name}: RPS={stage_result['throughput_rps']} req/s | "
          f"Avg={stage_result['latency_ms']['avg']}ms | p50={stage_result['latency_ms']['p50']}ms | "
          f"p95={stage_result['latency_ms']['p95']}ms | p99={stage_result['latency_ms']['p99']}ms | "
          f"Errors={len(failures)} ({stage_result['error_rate_pct']}%)")
    
    return stage_result

async def main():
    print("=" * 70)
    print("CONSOLITH PERFORMANCE & LOAD TESTING SUITE")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Target: {BASE_URL}")
    print("=" * 70)
    
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=100)
    async with httpx.AsyncClient(limits=limits, timeout=20.0) as client:
        # 1. Warm-up & Provision
        print("\n---> Warming up connections & provisioning benchmark user profile...")
        prov_res = await client.post(
            f"{BASE_URL}/api/v1/auth/provision",
            headers={"Authorization": f"Bearer {BENCH_TOKEN}"},
            json={"full_name": "Benchmark User"}
        )
        print(f"     Warm-up provisioning status: {prov_res.status_code}")
        warmup_res = await client.get(f"{BASE_URL}/api/v1/auth/me", headers={"Authorization": f"Bearer {BENCH_TOKEN}"})
        print(f"     Warm-up auth /me status: {warmup_res.status_code}")
        
        all_stage_results = []
        for stage in STAGE_CONFIGS:
            res = await run_stage(client, stage)
            all_stage_results.append(res)
            await asyncio.sleep(0.5)  # brief cooldown between stages

    output_data = {
        "timestamp": datetime.now().isoformat(),
        "target_url": BASE_URL,
        "stages": all_stage_results,
        "endpoints_tested": [e["name"] for e in ENDPOINTS]
    }
    
    output_path = "docs/load_test_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nAll stages completed. Full raw metrics written to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
