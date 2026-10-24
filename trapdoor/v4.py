"""
v4.py - Cascade V4: build, solve and release-check a four-layer challenge
=========================================================================

One layer per technique family, so no single toolchain opens every layer:

    layer 1 (entry)  variant9  prime-order D=3 CM curve, self-referential collision
    layer 2          lock02    Phi_4(p) Redei conic torus (balanced 512/512 primes)
    layer 3          lattice   lock08 (ctf tier) or variant5 (hard tier, needs fpylll)
    layer 4          lock09    Chebyshev / Lucas-V kleptographic SETUP

The public file holds only (N, e, c) for the outer layer plus the encrypted
inner layers. Opening layer i's envelope needs layer i's primes.

Usage:
  python3 -m trapdoor.v4 build --tier ctf --out challenges/v4
  python3 -m trapdoor.v4 solve challenges/v4/challenge.json --tier ctf
  python3 -m trapdoor.v4 check challenges/v4/challenge.json --solution challenges/v4/solution.json

Note: this file names the lineup. Publish challenge.json, not this repository.
"""

import argparse
import json
import os
import re
import secrets
import subprocess
import sys
import time

from trapdoor.arsenal.cascade_engine import CASCADE_FORMAT, build_cascade, solve_cascade

# Generator kwargs per layer. Solver params are the same search bounds (see
# sk["params"]), so a tier alone is enough to re-run the reference solver.
TIERS = {
    "ctf": [
        ("variant9", {"K_bound": 1 << 13}),
        ("lock02", {"K_bound": 1 << 13}),
        ("lock08", {"mask_bits": 4}),
        ("lock09", {"K_bound": 1 << 11}),
    ],
    "hard": [
        ("variant9", {"K_bound": 1 << 16}),
        ("lock02", {"K_bound": 1 << 15}),
        ("variant5", {"mask_bits": 8}),
        ("lock09", {"K_bound": 1 << 13}),
    ],
}

PUBLIC_LAYER_KEYS = {"N", "e", "c", "next"}
ENVELOPE_KEYS = {"nonce", "ciphertext", "hmac_sha256"}


def tier_hints(tier):
    lineup = TIERS[tier]
    return {"lock_sequence": [lid for lid, _ in lineup],
            "solver_params": [dict(params) for _, params in lineup]}


def cmd_build(a):
    seed = a.seed if a.seed is not None else secrets.randbits(40)
    flag = (a.flag or f"flag{{v4_{secrets.token_hex(12)}}}").encode()
    lineup = TIERS[a.tier]
    t0 = time.time()
    bundle = build_cascade([lid for lid, _ in lineup], final_flag=flag, seed=seed,
                           layer_params=[dict(p) for _, p in lineup], verbose=a.verbose)
    bundle["private"]["tier"] = a.tier
    os.makedirs(a.out, exist_ok=True)
    pub_path = os.path.join(a.out, "challenge.json")
    sol_path = os.path.join(a.out, "solution.json")
    with open(pub_path, "w", encoding="utf-8") as f:
        json.dump(bundle["public"], f, indent=1)
    with open(sol_path, "w", encoding="utf-8") as f:
        json.dump(bundle["private"], f, indent=1)
    print(f"built {a.tier} tier in {time.time() - t0:.1f}s")
    print(f"  public : {pub_path}")
    print(f"  private: {sol_path}  (never publish or commit)")
    return 0


def cmd_solve(a):
    public = json.load(open(a.challenge, encoding="utf-8"))
    if a.solution:
        hints = json.load(open(a.solution, encoding="utf-8"))
    else:
        hints = tier_hints(a.tier)
    res = solve_cascade(public, hints, verbose=a.verbose)
    for step in res["layer_trace"]:
        print(f"  layer {step['layer_index'] + 1} ({step['lock_id']}): {step['solve_time_sec']:.1f}s"
              f"  -> {step['recovered_message']}")
    print(f"FLAG = {res['final_flag']}")
    print(f"total {res['total_solve_time_sec']:.1f}s")
    return 0


def release_problems(public, private=None, repo_root="."):
    """Return a list of reasons the public file is not fit to publish."""
    problems = []
    if set(public) != {"format", "layers", "challenge"}:
        problems.append(f"unexpected top-level keys: {sorted(public)}")
    if public.get("format") != CASCADE_FORMAT:
        problems.append(f"format is {public.get('format')!r}, expected {CASCADE_FORMAT!r}")
    layer = public.get("challenge", {})
    if set(layer) != PUBLIC_LAYER_KEYS:
        problems.append(f"outer layer keys are {sorted(layer)}, expected {sorted(PUBLIC_LAYER_KEYS)}")
    if layer.get("next") is not None and set(layer["next"]) != ENVELOPE_KEYS:
        problems.append(f"envelope keys are {sorted(layer['next'])}")
    text = json.dumps(public)
    if re.search(r"lock|variant|K_bound|mask_bits|d1_bits|seed|flag", text, re.IGNORECASE):
        problems.append("public file mentions a lock name, search bound, seed or flag")
    if private:
        secrets_ = [private.get("flag", "")]
        for fac in private.get("factors", []):
            secrets_ += [fac["p"], fac["q"]]
        for s in filter(None, secrets_):
            if s in text:
                problems.append("a prime or the flag from solution.json appears in the public file")
                break
        # Seeds must not appear in the docs, or the challenge can be regenerated.
        for seed in private.get("seeds", []):
            hit = subprocess.run(["git", "grep", "-q", "-w", str(seed), "--", "docs", "README.md"],
                                 cwd=repo_root, capture_output=True)
            if hit.returncode == 0:
                problems.append(f"layer seed {seed} appears in the docs")
    return problems


def cmd_check(a):
    public = json.load(open(a.challenge, encoding="utf-8"))
    private = json.load(open(a.solution, encoding="utf-8")) if a.solution else None
    problems = release_problems(public, private)
    if a.solution:
        ignored = subprocess.run(["git", "check-ignore", "-q", a.solution], capture_output=True)
        if ignored.returncode != 0:
            problems.append(f"{a.solution} is not git-ignored")
    for p in problems:
        print("FAIL:", p)
    if not problems:
        print("OK: public file exposes only (N, e, c) and the encrypted envelope")
    return 1 if problems else 0


def main():
    ap = argparse.ArgumentParser(description="Cascade V4 builder / solver / release check")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--tier", choices=sorted(TIERS), default="ctf")
    b.add_argument("--seed", type=int, help="default: fresh random seed (keep it private)")
    b.add_argument("--flag", type=str, help="default: random flag")
    b.add_argument("--out", default=os.path.join("challenges", "v4"))
    b.add_argument("--verbose", action="store_true")
    s = sub.add_parser("solve")
    s.add_argument("challenge")
    s.add_argument("--solution", help="private manifest; without it the tier's lineup is used")
    s.add_argument("--tier", choices=sorted(TIERS), default="ctf")
    s.add_argument("--verbose", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("challenge")
    c.add_argument("--solution")
    a = ap.parse_args()
    return {"build": cmd_build, "solve": cmd_solve, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
