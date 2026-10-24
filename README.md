# puzzling — RSA Trapdoor Challenge Workbench

RSA kleptographic-trapdoor (陷门) CTF challenges: generators, reference solvers,
a shared pure-Python number-theory library, and the audit notes behind them.

The repo holds two generations of work:

| Generation | What it is | Status |
| :--- | :--- | :--- |
| **V2.1 Tri-Cascade** | Audit of the "V2.0 超算级隐式陷门" report; 4 repaired variants (5/6/7/9) and a 3-layer cascade challenge (6 → 9 → 7) | End-to-end verified: reference solver recovers the flag in ~400 s |
| **V3 Arsenal** | 10 "locks" (Φ₄/Φ₆/Φ₈/Φ₁₂ tori, D=−7 CM, genus-2 Jacobian, quaternion, SL₃, lattice, Chebyshev SETUP) + cascade engine + web dashboard. Imported from the AI Studio export | All 10 pass; edge suite on 20 seeds |
| **V4 Cascade** | One registry for all 14 locks (V3 + variants 5/6/7/9), a public file with only (N, e, c) per layer, and a four-layer lineup with one technique family per layer | Built and solved end to end; see `trapdoor/v4.py` |

Status, measurements and remaining work: **[docs/ROADMAP.md](docs/ROADMAP.md)**.
Solve-time curves: **[docs/benchmarks.md](docs/benchmarks.md)**.

---

## Layout

```
trapdoor/                    Python package (pure Python 3.10+, stdlib only)
├── ctflib.py                shared library: Kronecker poly-mul, Newton division,
│                            subproduct-tree batch_poly_gcd, EC arithmetic mod N, integer LLL;
│                            uses gmpy2 / fpylll when installed (TRAPDOOR_PURE=1 disables)
├── v4.py                    Cascade V4: build / solve / release check
├── variants/                V2.1 repaired trapdoor variants
│   ├── variant5.py          two-stage orthogonal lattice + Coppersmith (Stage 2 needs fpylll)
│   ├── variant6.py          hidden shared base 3^186 + δ₁, no-wrap residue
│   ├── variant7.py          cubic Pell norm-1 torus Φ₃(p)
│   └── variant9.py          prime-order D=3 CM curve, self-referential collision
├── tricascade/              V2.1 three-layer challenge
│   ├── puzzle_gen.py        builds challenge.json + solution.json
│   └── puzzle_solve.py      reference solver (reads only challenge.json)
└── arsenal/                 lock registry (V3 locks + V2.1 variants)
    ├── locks_A.py           locks 01–05
    ├── locks_B.py           locks 06–10
    ├── variant_locks.py     variants 5/6/7/9 behind the same lock interface
    ├── cascade_engine.py    LOCK_REGISTRY, single-lock runner, public/private cascade
    ├── verify_locks.py      CLI verification runner (--lock, --K, --cascade)
    ├── benchmark.py         solve-time curves -> docs/benchmarks.md
    └── dashboard.py         HTTP dashboard on :3000 (was main.py)

tests/
├── test_quick.py            pytest: every lock at a small bound + cascade surface (~75 s)
└── edge_suite.py            edge-case / decoy / autopilot suite, --seeds N (was edge_tests.py)

.github/workflows/ci.yml     quick tests + one-seed edge suite, with and without gmpy2/fpylll

challenges/
├── tri-cascade/challenge.json   published V2.1 challenge (legacy format)
└── v4/                          V4 build output (solution.json is git-ignored)

docs/
├── ROADMAP.md               current status, what was built, what is left
├── benchmarks.md            measured solve-time curves per lock
├── RELEASE_CHECKLIST.md     steps before publishing a challenge
├── CHANGELOG.md             V3 change log (from the AI Studio export)
├── audit/TRI_CASCADE_AUDIT.md   V2.0 report audit + V2.1 design and measurements (was README.md, Chinese)
├── arsenal/
│   ├── README_V3.md         V3 overview (from the export)
│   ├── TRAPDOOR_ARSENAL_V3.md   V3 spec (Chinese); served by the dashboard at /api/report
│   └── trapdoors.md         V3 formal six-module framework per lock
└── archive/aistudio_implementation_plan.md

package.json, metadata.json  AI Studio container entry points (dev/start → dashboard)
```

## Quick start

Run everything from the repo root (modules are invoked with `-m`). Pure Python
works; `pip install -r requirements-fast.txt` adds gmpy2/fpylll (needed for variant5).

```bash
# V4 cascade
python3 -m trapdoor.v4 build --tier ctf                     # -> challenges/v4/{challenge,solution}.json
python3 -m trapdoor.v4 solve challenges/v4/challenge.json --solution challenges/v4/solution.json
python3 -m trapdoor.v4 check challenges/v4/challenge.json --solution challenges/v4/solution.json

# Tests
python3 -m pytest -q tests/test_quick.py
python3 -u -m tests.edge_suite --seeds 20

# V2.1 tri-cascade (legacy)
python3 -m trapdoor.tricascade.puzzle_gen --bbits 16 --seed 1023   # → challenges/tri-cascade/
python3 -m trapdoor.tricascade.puzzle_solve                         # ~400 s, prints the flag

# Single V2.1 variants
python3 -m trapdoor.variants.variant9 --bits 15 --seed 20261023
python3 -m trapdoor.variants.variant7 --bits 13 --seed 77
python3 -m trapdoor.variants.variant6 --seed 606
python3 -m trapdoor.variants.variant5 --mask 4

# Lock registry
python3 -u -m trapdoor.arsenal.verify_locks                    # all 14 locks at quick bounds
python3 -u -m trapdoor.arsenal.verify_locks --lock variant9 --K 13
python3 -u -m trapdoor.arsenal.benchmark --locks lock02 --K 9,11,13 --out bench.jsonl
python3 -m trapdoor.arsenal.dashboard        # http://localhost:3000
```

`npm run dev|verify|test|build` wraps the same commands for the AI Studio runtime.

## Before publishing a challenge

Follow [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md). In short: build with a fresh
seed, run `trapdoor.v4 check`, publish `challenge.json` only (not this repo), and keep
`solution.json` private.
