# puzzling — RSA Trapdoor Challenge Workbench

RSA kleptographic-trapdoor (陷门) CTF challenges: generators, reference solvers,
a shared pure-Python number-theory library, and the audit notes behind them.

The repo holds two generations of work:

| Generation | What it is | Status |
| :--- | :--- | :--- |
| **V2.1 Tri-Cascade** | Audit of the "V2.0 超算级隐式陷门" report; 4 repaired variants (5/6/7/9) and a 3-layer cascade challenge (6 → 9 → 7) | End-to-end verified: reference solver recovers the flag in ~400 s |
| **V3 Arsenal** | 10 new "locks" (Φ₄/Φ₆/Φ₈/Φ₁₂ tori, D=−7 CM, genus-2 Jacobian, quaternion, SL₃, lattice, Chebyshev SETUP) + a composable cascade engine + web dashboard. Imported from the AI Studio export | Partially verified. See [docs/ROADMAP.md](docs/ROADMAP.md#where-things-stand) |

The next stage is proposed in **[docs/ROADMAP.md](docs/ROADMAP.md)**.

---

## Layout

```
trapdoor/                    Python package (pure Python 3.10+, stdlib only)
├── ctflib.py                shared library: Kronecker poly-mul, Newton division,
│                            subproduct-tree batch_poly_gcd, EC arithmetic mod N, integer LLL
├── variants/                V2.1 repaired trapdoor variants
│   ├── variant5.py          two-stage orthogonal lattice + Coppersmith (Stage 2 needs fpylll)
│   ├── variant6.py          hidden shared base 3^186 + δ₁, no-wrap residue
│   ├── variant7.py          cubic Pell norm-1 torus Φ₃(p)
│   └── variant9.py          prime-order D=3 CM curve, self-referential collision
├── tricascade/              V2.1 three-layer challenge
│   ├── puzzle_gen.py        builds challenge.json + solution.json
│   └── puzzle_solve.py      reference solver (reads only challenge.json)
└── arsenal/                 V3 ten-lock arsenal
    ├── locks_A.py           locks 01–05
    ├── locks_B.py           locks 06–10
    ├── cascade_engine.py    LOCK_REGISTRY, single-lock runner, HMAC-enveloped cascade
    ├── verify_locks.py      CLI benchmark / verification runner
    └── dashboard.py         HTTP dashboard on :3000 (was main.py)

tests/
└── edge_suite.py            V3 edge-case / decoy / autopilot-attack suite (was edge_tests.py)

challenges/tri-cascade/
└── challenge.json           published V2.1 challenge (solution.json is git-ignored)

docs/
├── ROADMAP.md               current status + next-stage proposal
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

Run everything from the repo root (modules are invoked with `-m`).

```bash
# V2.1 tri-cascade
python3 -m trapdoor.tricascade.puzzle_gen --bbits 16 --seed 1023   # → challenges/tri-cascade/
python3 -m trapdoor.tricascade.puzzle_solve                         # ~400 s, prints the flag

# Single V2.1 variants
python3 -m trapdoor.variants.variant9 --bits 15 --seed 20261023
python3 -m trapdoor.variants.variant7 --bits 13 --seed 77
python3 -m trapdoor.variants.variant6 --seed 606
python3 -m trapdoor.variants.variant5 --mask 4

# V3 arsenal
python3 -u -m trapdoor.arsenal.verify_locks --lock lock01
python3 -u -m trapdoor.arsenal.verify_locks --cascade lock01,lock04,lock08,lock09
python3 -u -m tests.edge_suite
python3 -m trapdoor.arsenal.dashboard        # http://localhost:3000
```

`npm run dev|verify|test|build` wraps the same commands for the AI Studio runtime.

## Before publishing a challenge

- Never commit `solution.json` (it is in `.gitignore`).
- Re-generate with a fresh seed. `--seed 1023` is public in the docs.
- Don't publish a V3 cascade bundle as-is. It currently names every layer's lock (see ROADMAP, Stage 1).
