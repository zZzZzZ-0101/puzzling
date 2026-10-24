"""
verify_locks.py - End-to-End Verification & Benchmark Runner for the 10-Lock Trapdoor Arsenal
=============================================================================================

Usage:
  python3 -u -m trapdoor.arsenal.verify_locks                  # Verify all 10 locks individually + run a 4-layer cascade test
  python3 -u -m trapdoor.arsenal.verify_locks --lock lock05    # Verify a single lock by ID
  python3 -u -m trapdoor.arsenal.verify_locks --cascade lock01,lock04,lock08,lock09
"""

import argparse
import json
import sys
import time
from trapdoor.arsenal.cascade_engine import (
    LOCK_REGISTRY,
    generate_single_lock,
    solve_single_lock,
    build_cascade,
    solve_cascade,
)


def run_all_benchmarks() -> None:
    print("=" * 92)
    print(" CRYPTOGRAPHIC TRAPDOOR ARSENAL V3 - 10 SEPARATED LOCKS & COMPOSABLE CASCADE VERIFICATION")
    print("=" * 92)

    summary_rows = []
    all_passed = True

    for idx, lock_id in enumerate(sorted(LOCK_REGISTRY.keys()), start=1):
        meta = LOCK_REGISTRY[lock_id]
        expected_flag = f"FLAG{{Lock_{idx:02d}_{lock_id}_Verified_2026}}".encode("utf-8")
        seed = 20260400 + idx * 137

        print(f"\n[{idx:02d}/10] Testing {lock_id}: {meta['name']}")
        print(f"        Public Surface : {meta['surface']}")
        print(f"        Algebraic Group: {meta['algebraic_group']}")

        gen_res = generate_single_lock(lock_id, flag_bytes=expected_flag, seed=seed, verbose=True)
        pub = gen_res["pub"]
        priv = gen_res["priv"]
        gen_t = gen_res["gen_time_sec"]

        N_bits = pub["N"].bit_length()
        e_bits = pub["e"].bit_length()
        print(f"        KeyGen Complete: N={N_bits} bits, e={e_bits} bits in {gen_t:.3f}s")

        solve_res = solve_single_lock(lock_id, pub, verbose=True)
        solve_t = solve_res["solve_time_sec"]
        p_rec, q_rec = solve_res["p"], solve_res["q"]
        pt_rec = solve_res["plaintext_bytes"]

        factors_ok = (p_rec * q_rec == pub["N"]) and ({p_rec, q_rec} == {priv["p"], priv["q"]})
        flag_ok = (pt_rec == expected_flag)
        passed = factors_ok and flag_ok

        status_str = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False

        print(f"        Trapdoor Solve : [{status_str}] recovered p ({p_rec.bit_length()}b), q ({q_rec.bit_length()}b) in {solve_t:.3f}s")
        print(f"        Recovered Flag : {pt_rec.decode('utf-8', errors='replace')}")

        summary_rows.append({
            "lock_id": lock_id,
            "name": meta["name"],
            "surface": meta["surface"],
            "N_bits": N_bits,
            "e_bits": e_bits,
            "gen_time_sec": gen_t,
            "solve_time_sec": solve_t,
            "status": status_str,
        })

    print("\n" + "=" * 92)
    print(" TESTING MULTI-LAYER MATRYOSHKA CASCADE ENGINE (COMPOSABLE PUZZLE CHAINING)")
    print("=" * 92)
    cascade_seq = ["lock01", "lock04", "lock08", "lock09"]
    cascade_flag = b"FLAG{Composable_Cascade_01_04_08_09_Solved}"
    print(f"Building 4-Layer Cascade: {' -> '.join(cascade_seq)}")
    t0 = time.time()
    bundle = build_cascade(cascade_seq, final_flag=cascade_flag, base_seed=20260999)
    build_t = time.time() - t0
    print(f"Cascade Built in {build_t:.3f}s. Solving from outermost public challenge...")

    cascade_solved = solve_cascade(bundle)
    for step in cascade_solved["layer_trace"]:
        print(
            f"  -> Layer {step['layer_index']} ({step['lock_id']}): "
            f"factored {step['p_bits']}b x {step['q_bits']}b in {step['solve_time_sec']:.3f}s | "
            f"Msg: {step['recovered_message']}"
        )
    cascade_ok = (cascade_solved["final_flag"].encode("utf-8") == cascade_flag)
    print(f"Cascade Final Flag: {cascade_solved['final_flag']} [{'PASS' if cascade_ok else 'FAIL'}]")
    if not cascade_ok:
        all_passed = False

    print("\n" + "=" * 92)
    print(f"{'Lock ID':<8} | {'Surface':<16} | {'N bits':<6} | {'e bits':<6} | {'KeyGen (s)':<10} | {'Solve (s)':<10} | {'Status'}")
    print("-" * 92)
    for r in summary_rows:
        print(
            f"{r['lock_id']:<8} | {r['surface']:<16} | {r['N_bits']:<6} | {r['e_bits']:<6} | "
            f"{r['gen_time_sec']:<10.3f} | {r['solve_time_sec']:<10.3f} | {r['status']}"
        )
    print("=" * 92)

    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "all_passed": all_passed,
                "locks": summary_rows,
                "cascade_demo": cascade_solved,
            },
            f,
            indent=2,
        )

    if not all_passed:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="10-Lock Cryptographic Trapdoor Arsenal Runner")
    parser.add_argument("--lock", type=str, help="Run a single lock by ID (lock01..lock10)")
    parser.add_argument("--cascade", type=str, help="Comma-separated list of lock IDs to chain into a cascade")
    args = parser.parse_args()

    if args.lock:
        lid = args.lock.strip()
        flag = f"FLAG{{Single_{lid}_Run}}".encode("utf-8")
        gen = generate_single_lock(lid, flag_bytes=flag, seed=20260777, verbose=True)
        sol = solve_single_lock(lid, gen["pub"], verbose=True)
        print(json.dumps({
            "lock_id": lid,
            "N_bits": gen["pub"]["N"].bit_length(),
            "e_bits": gen["pub"]["e"].bit_length(),
            "gen_time_sec": gen["gen_time_sec"],
            "solve_time_sec": sol["solve_time_sec"],
            "flag": sol["plaintext_bytes"].decode("utf-8", errors="replace"),
        }, indent=2))
    elif args.cascade:
        seq = [x.strip() for x in args.cascade.split(",") if x.strip()]
        bundle = build_cascade(seq, final_flag=b"FLAG{Custom_Cascade_Verified}")
        sol = solve_cascade(bundle)
        print(json.dumps(sol, indent=2))
    else:
        run_all_benchmarks()


if __name__ == "__main__":
    main()
