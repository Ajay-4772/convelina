#!/usr/bin/env python3
"""
Verification Script for Module 1: Foundation
Tests:
1. PostgreSQL service connectivity (port 5432)
2. Qdrant vector database health (port 6333)
3. FastAPI backend health check (/health on port 8000)
4. Next.js frontend availability (/ on port 3000)
"""

import sys
import time
import urllib.request
import json

def check_postgres():
    print("[1/4] Checking PostgreSQL connectivity on port 5432...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        result = sock.connect_ex(('127.0.0.1', 5432))
        sock.close()
        if result == 0:
            print("  [OK] PostgreSQL port 5432 is open and accepting TCP connections.")
            return True
        else:
            print(f"  [FAIL] PostgreSQL port 5432 unreachable (error code: {result}).")
            return False
    except Exception as e:
        print(f"  [FAIL] PostgreSQL check failed: {e}")
        return False

def check_qdrant():
    print("[2/4] Checking Qdrant REST API on port 6333...")
    try:
        req = urllib.request.Request("http://127.0.0.1:6333/healthz")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                print("  [OK] Qdrant is healthy (/healthz returned HTTP 200).")
                return True
            else:
                print(f"  [FAIL] Qdrant returned status: {resp.status}")
                return False
    except Exception as e:
        print(f"  [FAIL] Qdrant check failed: {e}")
        return False

def check_backend():
    print("[3/4] Checking FastAPI backend on port 8000...")
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/health")
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"  Payload: {json.dumps(data, indent=2)}")
            if data.get("status") == "healthy" and \
               data.get("services", {}).get("backend", {}).get("status") == "up" and \
               data.get("services", {}).get("postgres", {}).get("status") == "up" and \
               data.get("services", {}).get("qdrant", {}).get("status") == "up":
                print("  [OK] Backend reported healthy with postgres and qdrant connected.")
                return True
            else:
                print(f"  [FAIL] Backend health check degraded: {data}")
                return False
    except Exception as e:
        print(f"  [FAIL] Backend check failed: {e}")
        return False

def check_frontend():
    print("[4/4] Checking Next.js frontend on port 3000...")
    try:
        req = urllib.request.Request("http://127.0.0.1:3000")
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            if resp.status == 200:
                body = resp.read().decode('utf-8', errors='ignore')
                if "CONVELINA" in body or "Consolith" in body:
                    print("  [OK] Frontend is running and serving CONVELINA application (HTTP 200).")
                    return True
                else:
                    print("  [FAIL] Frontend returned 200 but 'CONVELINA' not found in HTML.")
                    return False
            else:
                print(f"  [FAIL] Frontend returned status {resp.status}")
                return False
    except Exception as e:
        print(f"  [FAIL] Frontend check failed: {e}")
        return False

def main():
    print("==================================================")
    print("   Consolith Module 1 Verification: Foundation")
    print("==================================================")
    
    # Wait for services to be ready if called during spin-up
    max_retries = 12
    for attempt in range(1, max_retries + 1):
        print(f"\nAttempt {attempt}/{max_retries}...")
        pg_ok = check_postgres()
        qd_ok = check_qdrant()
        be_ok = check_backend()
        fe_ok = check_frontend()
        
        if pg_ok and qd_ok and be_ok and fe_ok:
            print("\n==================================================")
            print("  ALL SERVICES UP AND VERIFIED SUCCESSFULLY!")
            print("==================================================")
            return 0
        
        if attempt < max_retries:
            print("Services still settling, waiting 5 seconds...")
            time.sleep(5)
    
    print("\n==================================================")
    print("  VERIFICATION FAILED: One or more services down.")
    print("==================================================")
    return 1

if __name__ == "__main__":
    sys.exit(main())
