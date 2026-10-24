"""
verify_locks.py - End-to-End Verification Runner for the Trapdoor Lock Registry
================================================================================

Usage:
  python3 -u -m trapdoor.arsenal.verify_locks                  # every lock at quick bounds + a cascade
  python3 -u -m trapdoor.arsenal.verify_locks --lock lock05    # one lock at its default bounds
  python3 -u -m trapdoor.arsenal.verify_locks --lock variant9 --K 13
  python3 -u -m trapdoor.arsenal.verify_locks --cascade lock01,lock04,lock08,lock09
"""

import argparse
import inspect
import json
import sys
import time
from trapdoor.ctflib import BACKEND
from trapdoor.arsenal.cascade_engine import (
    LOCK_REGISTRY,
    generate_single_lock,
    solve_single_lock,
    build_cascade,
    solve_cascade,
)

# Bounds used by the full run so that it finishes in a few minutes. The V2.1
# variants default to much larger bounds (variant9: 2^15, ~12 min alone).
QUICK_PARAMS = {
    "variant5": {"mask_bits": 2},
    "variant6": {"d1_bits": 10},
    "variant7": {"K_bound": 1 << 11},
    "variant9": {"K_bound": 1 << 11},
}


def size_params(lock_id, k_bits):
    """Generator kwargs that set lock_id's search space to about 2^k_bits."""
    accepted = inspect.signature(LOCK_REGISTRY[lock_id]["generate"]).parameters
    if "K_bound" in accepted:
        return {"K_bound": 1 << k_bits}
    if "d1_bits" in accepted:
        return {"d1_bits": k_bits}
    if "mask_bits" in accepted:
        return {"mask_bits": k_bits}
    raise ValueError(f"{lock_id} has no search-size parameter")


def run_lock(lock_id, flag, seed, gen_params=None, verbose=True):
    gen = generate_single_lock(lock_id, flag_bytes=flag, seed=seed, verbose=verbose, **(gen_params or {}))
    sol = solve_single_lock(lock_id, gen["pub"], verbose=verbose, **gen["params"])
    ok = ({sol["p"], sol["q"]} == {gen["priv"]["p"], gen["priv"]["q"]}
          and sol["plaintext_bytes"] == flag)
    return gen, sol, ok


def run_all_benchmarks() -> None:
    print("=" * 92)
    print(" TRAPDOOR LOCK REGISTRY - END-TO-END VERIFICATION  (backends: %s)" %
          ", ".join(k for k, v in BACKEND.items() if v) or "pure Python")
    print("=" * 92)

    summary_rows = []
    all_passed = True
    lock_ids = sorted(LOCK_REGISTRY)
    for idx, lock_id in enumerate(lock_ids, start=1):
        meta = LOCK_REGISTRY[lock_id]
        if lock_id == "variant5" and not BACKEND["fpylll"]:
            print(f"\n[{idx:02d}/{len(lock_ids)}] {lock_id}: SKIPPED (needs fpylll)")
            summary_rows.append({"lock_id": lock_id, "status": "SKIP"})
            continue
        flag = f"FLAG{{{lock_id}_verified}}".encode("utf-8")
        print(f"\n[{idx:02d}/{len(lock_ids)}] {lock_id}: {meta['name']}")
        gen, sol, ok = run_lock(lock_id, flag, 20260400 + idx * 137, QUICK_PARAMS.get(lock_id))
        status = "PASS" if ok else "FAIL"
        all_passed &= ok
        print(f"        KeyGen {gen['gen_time_sec']:.2f}s | Solve {sol['solve_time_sec']:.2f}s | "
              f"p={sol['p'].bit_length()}b q={sol['q'].bit_length()}b | {status}")
        summary_rows.append({
            "lock_id": lock_id,
            "params": gen["params"],
            "N_bits": gen["pub"]["N"].bit_length(),
            "e_bits": gen["pub"]["e"].bit_length(),
            "gen_time_sec": gen["gen_time_sec"],
            "solve_time_sec": sol["solve_time_sec"],
            "status": status,
        })

    print("\n" + "=" * 92)
    cascade_seq = ["lock01", "lock04", "lock08", "lock09"]
    cascade_flag = b"FLAG{Composable_Cascade_01_04_08_09_Solved}"
    print(f"Cascade {' -> '.join(cascade_seq)}")
    t0 = time.time()
    bundle = build_cascade(cascade_seq, final_flag=cascade_flag, base_seed=20260999)
    print(f"  built in {time.time() - t0:.2f}s; public layer keys: {sorted(bundle['public']['challenge'])}")
    cascade_solved = solve_cascade(bundle)
    for step in cascade_solved["layer_trace"]:
        print(f"  -> layer {step['layer_index']} ({step['lock_id']}): {step['solve_time_sec']:.2f}s | "
              f"{step['recovered_message']}")
    cascade_ok = cascade_solved["final_flag"].encode("utf-8") == cascade_flag
    all_passed &= cascade_ok
    print(f"  final flag: {cascade_solved['final_flag']} [{'PASS' if cascade_ok else 'FAIL'}]")

    print("\n" + "=" * 92)
    print(f"{'Lock ID':<10} | {'N bits':<6} | {'e bits':<6} | {'KeyGen (s)':<10} | {'Solve (s)':<10} | Status")
    print("-" * 92)
    for r in summary_rows:
        if r["status"] == "SKIP":
            print(f"{r['lock_id']:<10} | {'':<6} | {'':<6} | {'':<10} | {'':<10} | SKIP")
            continue
        print(f"{r['lock_id']:<10} | {r['N_bits']:<6} | {r['e_bits']:<6} | "
              f"{r['gen_time_sec']:<10.3f} | {r['solve_time_sec']:<10.3f} | {r['status']}")
    print("=" * 92)

    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump({"all_passed": all_passed, "backends": BACKEND, "locks": summary_rows,
                   "cascade_demo": cascade_solved}, f, indent=2)
    if not all_passed:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Trapdoor lock registry runner")
    parser.add_argument("--lock", type=str, help=f"Run one lock: {', '.join(sorted(LOCK_REGISTRY))}")
    parser.add_argument("--K", type=int, help="Search space ~2^K for --lock (K_bound, d1_bits or mask_bits)")
    parser.add_argument("--seed", type=int, default=20260777)
    parser.add_argument("--cascade", type=str, help="Comma-separated lock IDs to chain into a cascade")
    args = parser.parse_args()

    if args.lock:
        lid = args.lock.strip()
        flag = f"FLAG{{Single_{lid}_Run}}".encode("utf-8")
        gen_params = size_params(lid, args.K) if args.K else {}
        gen, sol, ok = run_lock(lid, flag, args.seed, gen_params)
        print(json.dumps({
            "lock_id": lid,
            "params": gen["params"],
            "N_bits": gen["pub"]["N"].bit_length(),
            "e_bits": gen["pub"]["e"].bit_length(),
            "gen_time_sec": gen["gen_time_sec"],
            "solve_time_sec": sol["solve_time_sec"],
            "flag": sol["plaintext_bytes"].decode("utf-8", errors="replace"),
            "status": "PASS" if ok else "FAIL",
        }, indent=2))
        if not ok:
            sys.exit(1)
    elif args.cascade:
        seq = [x.strip() for x in args.cascade.split(",") if x.strip()]
        bundle = build_cascade(seq, final_flag=b"FLAG{Custom_Cascade_Verified}")
        sol = solve_cascade(bundle)
        print(json.dumps(sol, indent=2))
    else:
        run_all_benchmarks()


if __name__ == "__main__":
    main()
