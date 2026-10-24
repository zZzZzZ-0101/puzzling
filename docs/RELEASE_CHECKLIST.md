# Release checklist (Cascade V4)

Work through this list every time a challenge is published. Steps marked
**auto** are enforced by `python3 -m trapdoor.v4 check`.

## Build

1. Pick a tier (`ctf` or `hard`; see `trapdoor/v4.py` and `docs/benchmarks.md`).
2. Build with a fresh random seed. Don't pass `--seed`, and never reuse a seed
   that appears anywhere in this repository:
   ```bash
   python3 -m trapdoor.v4 build --tier ctf --out challenges/v4
   ```
3. Solve it once with the reference solver, using the private manifest:
   ```bash
   python3 -m trapdoor.v4 solve challenges/v4/challenge.json --solution challenges/v4/solution.json
   ```
   The flag must match `solution.json`.

## Check

4. Run the release check:
   ```bash
   python3 -m trapdoor.v4 check challenges/v4/challenge.json --solution challenges/v4/solution.json
   ```
   It verifies the following:
   - **auto**: top level is exactly `format`, `layers`, `challenge`
   - **auto**: the outer layer is exactly `N`, `e`, `c`, `next`, and the envelope is exactly `nonce`, `ciphertext`, `hmac_sha256`
   - **auto**: no lock name, search bound, seed or flag text in the public file
   - **auto**: no prime and no flag from `solution.json` appears in the public file
   - **auto**: no layer seed appears in `docs/` or `README.md`
   - **auto**: `solution.json` is git-ignored
5. Manual: the published package contains `challenge.json` and nothing else.
   This repository names the V4 lineup (`trapdoor/v4.py`) and the solvers, so
   publishing the repo next to the challenge hands out the solution path.

## Keep

6. Store `solution.json` somewhere private and durable, outside the repo. If it
   is lost, `trapdoor.v4 solve --tier <tier>` still solves the challenge, because
   the tier fixes the lineup and search bounds. Only the flag text and seeds are
   unique to the manifest.
