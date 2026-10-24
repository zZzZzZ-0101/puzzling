"""
benchmark.py - solve-time curves per lock (search size -> seconds)

Usage:
  python3 -u -m trapdoor.arsenal.benchmark --locks lock01,lock02 --out bench.jsonl
  python3 -u -m trapdoor.arsenal.benchmark --locks variant9 --K 11,13,15 --out bench.jsonl
  python3 -m trapdoor.arsenal.benchmark --report bench.jsonl > docs/benchmarks.md

Each run appends one JSON line, so several processes can share a file and the
report can be rebuilt at any time. "K" means the size knob of each lock:
log2(K_bound) for collision locks, d1_bits for variant6, mask_bits for the
lattice locks (variant5, lock08).
"""

import argparse
import json
import math
import platform
import time
from collections import defaultdict

from trapdoor.ctflib import BACKEND
from trapdoor.arsenal.cascade_engine import LOCK_REGISTRY, generate_single_lock, solve_single_lock
from trapdoor.arsenal.verify_locks import size_params

DEFAULT_K = {
    "variant5": [1, 2, 3, 4],
    "variant6": [12, 16, 20],
    "variant9": [11, 13, 15],
    "lock08": [2, 4, 6],
}
DEFAULT_K_COLLISION = [9, 11, 13]


def run_one(lock_id, k_bits, seed):
    flag = f"FLAG{{bench_{lock_id}_{k_bits}}}".encode()
    gen = generate_single_lock(lock_id, flag_bytes=flag, seed=seed, **size_params(lock_id, k_bits))
    sol = solve_single_lock(lock_id, gen["pub"], **gen["params"])
    ok = {sol["p"], sol["q"]} == {gen["priv"]["p"], gen["priv"]["q"]} and sol["plaintext_bytes"] == flag
    return {
        "lock_id": lock_id,
        "K": k_bits,
        "seed": seed,
        "gen_sec": gen["gen_time_sec"],
        "solve_sec": sol["solve_time_sec"],
        "ok": ok,
        "backends": [k for k, v in BACKEND.items() if v],
        "machine": platform.machine(),
        "date": time.strftime("%Y-%m-%d"),
    }


def report(path):
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    by_lock = defaultdict(dict)
    for r in rows:
        by_lock[r["lock_id"]][r["K"]] = r
    out = ["| Lock | knob | solve time by K | exponent a (t ~ 2^(aK)) |",
           "| :--- | :--- | :--- | ---: |"]
    for lid in sorted(by_lock):
        cells = []
        for k, r in sorted(by_lock[lid].items()):
            cells.append(f"{k}: {r['solve_sec']:.1f}s" + ("" if r["ok"] else " FAIL"))
        # Fit over the points with t >= 0.5 s (below that, fixed costs dominate).
        pts = sorted((k, r["solve_sec"]) for k, r in by_lock[lid].items() if r["ok"] and r["solve_sec"] >= 0.5)
        slope = ""
        if len(pts) >= 2:
            (k0, t0), (k1, t1) = pts[0], pts[-1]
            slope = f"{math.log2(t1 / t0) / (k1 - k0):.2f}"
        knob = "mask_bits" if lid in ("variant5", "lock08") else ("d1_bits" if lid == "variant6" else "log2 K_bound")
        out.append(f"| {lid} | {knob} | " + " · ".join(cells) + f" | {slope} |")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--locks", type=str, help="comma-separated lock ids (default: all)")
    ap.add_argument("--K", type=str, help="comma-separated K values (default: per-lock list)")
    ap.add_argument("--seed", type=int, default=31337)
    ap.add_argument("--out", type=str, default="benchmark.jsonl")
    ap.add_argument("--report", type=str, help="render a JSONL file as a markdown table and exit")
    a = ap.parse_args()
    if a.report:
        print(report(a.report))
        return
    locks = a.locks.split(",") if a.locks else sorted(LOCK_REGISTRY)
    for lid in locks:
        ks = [int(x) for x in a.K.split(",")] if a.K else DEFAULT_K.get(lid, DEFAULT_K_COLLISION)
        for k in ks:
            r = run_one(lid, k, a.seed)
            print(json.dumps(r), flush=True)
            with open(a.out, "a", encoding="utf-8") as f:
                f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    main()
