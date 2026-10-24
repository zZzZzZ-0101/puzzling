# Roadmap — next-stage proposal

_Last updated 2026-10-24, after the repository reorganisation._

This document records what has been verified, what is broken, and a staged plan
for the next round of work. Numbers marked **measured** were measured on a
4-core cloud container on 2026-10-24. Everything else is quoted from the
earlier docs and has not been re-run.

---

## Where things stand

### V2.1 Tri-Cascade (variants 6 → 9 → 7)

| Item | Status |
| :--- | :--- |
| Reference solver on the published `challenge.json` | 401 s end to end (from the audit doc) |
| variant6 `--seed 606` via new package path | **measured** PASS, 139 s |
| variant7 `--bits 12 --seed 77` via new package path | **measured** PASS, 12 s |
| variant9 at K = 2^18 ("hard" tier) | **never verified end to end**; 1.6–1.8 h is an extrapolation |
| variant5 Stage 2 | blocked: needs a 20-dim LLL (`fpylll`/Sage) |
| Layer A (variant6) | weakest layer and it is the entry point: δ₁ has 16 bits of entropy, base 3^186 is guessable |

### V3 Arsenal (10 locks, from the AI Studio export)

Each lock was run once (seed 20260777) through `generate_single_lock` → `solve_single_lock`:

| Lock | Construction | KeyGen | Solve | Result |
| :--- | :--- | ---: | ---: | :--- |
| lock01 | Φ₆ torus T₆ | 0.06 s | 2.3 s | **PASS** |
| lock02 | Φ₄ Rédei conic | 0.05 s | 1.7 s | **PASS** (via verify_locks) |
| lock03 | Φ₈ octic torus | 0.19 s | 3.1 s | **PASS** (via verify_locks); p is only 332 bits |
| lock04 | D = −7 CM curve | did not finish | — | **TIMEOUT**: key generation did not finish in the test run (see Stage 1) |
| lock05 | genus-2 Jacobian | 0.12 s | 44.4 s | **PASS** |
| lock06 | quaternion over R₃ | 0.23 s | 14.3 s | **PASS** |
| lock07 | prime-order SL₃ | 61.4 s | 1.2 s | **PASS**; slow keygen (needs p and p²+p+1 both prime); edge suite skips it by default |
| lock08 | 4D lattice + Coppersmith | 1.7 s | 13.1 s | **PASS** |
| lock09 | Chebyshev / Lucas-V SETUP | 0.10 s | 0.6 s | **PASS** |
| lock10 | Φ₁₂ torus | 0.10 s | 6.7 s | **PASS**; p is only 332 bits |

`tests/edge_suite.py` **fails** at lock02 on both the original export and the
reorganised tree. The test asserts a continued-fraction spike ≥ 2^50, but the
generator never enforces it. Measured spikes on three seeds were 2^51, 2^57
and 2^63, so the threshold is borderline and some seeds fall below it.

### Problems found in V3 (beyond pass/fail)

1. **The public surface is not just (N, e, c).** The cascade bundle publishes
   `lock_sequence` and each layer's `lock_id`, and most `pub` dicts also carry
   `K_bound`/`B` (lock08 carries `mask_bits`/`x0_bits`). A solver is told which
   trapdoor each layer uses. This contradicts the main design claim.
2. **The difficulty is far below V2.1.** All locks default to `K_bound = 2^11`
   (309 primes per side). Eight of the nine passing locks solve in under 15 s
   in pure Python (lock05 takes 44 s). V2.1 Layer B uses 2^16 and takes about 217 s. The "defeat frontier
   LLMs" claims in the V3 docs are untested.
3. **The decoys give the key away.** N ≡ 1 (mod 2^12), e ≡ 3 (mod 2^80),
   e ≡ N (mod 2^120), and N ≡ 65537^1337 (mod P₃₇) are each events with
   probability 2^-12 to 2^-120 for an honest key. One `N % 2**k` check shows
   that the key was constructed, which points straight at a planted trapdoor.
4. **Unbalanced primes.** lock03/lock10 use 332-bit p. That is out of ECM
   reach today (the record is about 274 bits), but the margin is much smaller
   than for 512-bit p, and p ≠ q bit length is itself a fingerprint once p is found.
5. **Two cascade frameworks.** `tricascade/` (XOR keystream, seed from the RSA
   plaintext) and `arsenal/cascade_engine.py` (HMAC envelope, key from p, q)
   do the same job differently.
6. `requirements.txt` in the export listed `gmpy2`, but nothing imports it.

---

## Proposed next stage

The ordering is deliberate. Stage 1 makes results trustworthy. Stage 2 makes
difficulty a measured number. Only then does Stage 3 assemble a challenge.

### Stage 1: Correctness and hygiene (small, do first)

- [ ] **Strip the public surface.** `build_cascade` should publish only
      `(N, e, c, next_envelope)` per layer. Move `lock_id`, `K_bound`, `B`,
      `mask_bits`, `x0_bits` into the private side. Solvers take search bounds as
      parameters rather than reading them from the challenge.
- [ ] **Fix lock04 key generation**: find which loop does not terminate (twist
      selection over u₀ ∈ 1..5, or the C₋₇ ⟂ P₃₇ filter) and bound it.
- [ ] **lock07**: key generation works but takes about 60 s. Add it back to the
      edge suite (it is excluded unless `--with-lock07` is passed), or cache valid p.
- [ ] **lock02 decoy**: either loop in the generator until the spike is ≥ 2^50,
      or drop the assertion. Then make `tests/edge_suite.py` pass on every seed in
      a fixed set of 20.
- [ ] **pytest wrapper + CI.** Add `tests/test_quick.py` that runs every
      lock and variant at a small bound (K = 2^9–2^11) with fixed seeds. Run it in
      GitHub Actions on push, with a budget under 10 min.
- [ ] Remove or redesign the statistical decoys (item 3 above). A decoy must
      be indistinguishable from a random key, or it shouldn't be there.

### Stage 2: Difficulty calibration (measure instead of claim)

- [ ] Add `--K` (search bound) to every lock and produce a solve-time curve
      per lock (K = 2^11, 2^13, 2^15, 2^16, 2^18), as the audit did for variant9.
      Commit results to `docs/benchmarks.md`.
- [ ] **Run variant9 at K = 2^18 end to end** with
      `nohup python3 -u -m trapdoor.variants.variant9 --bits 18 --seed 20261023 > v9_hard.log &`
      on a machine that does not reap background jobs. This is the oldest open TODO.
- [ ] Optional `gmpy2` backend in `ctflib` (drop-in `mpz` when importable)
      to measure how much a well-equipped solver gains.
- [ ] `fpylll` path for variant5 Stage 2 (m = 5, t = 10, 20-dim) and lock08
      at larger parameters.
- [ ] **Attack harness** (`tools/redteam.py`): run the generic attacks against
      each public surface and record which ones succeed. Cover Fermat, Pollard
      p−1, Williams p+1, Φₖ-cyclotomic p-methods for k ≤ 12, short ECM, Wiener and
      Boneh–Durfee, and the low-bit/known-residue Coppersmith family. A lock ships only if every
      generic attack fails and only its intended path succeeds.

### Stage 3: Unified cascade V4 (the actual next challenge)

- [ ] Fold variants 5/6/7/9 into `LOCK_REGISTRY` so there is **one** cascade
      engine (keep the HMAC envelope from V3 and retire the XOR keystream).
- [ ] Choose layers for **orthogonal techniques**, so one toolchain can't
      solve them all. Suggested lineup, subject to Stage 2 numbers:

      | Layer | Lock | Technique family |
      | :--- | :--- | :--- |
      | 1 (entry) | variant9 or lock07 at calibrated K | prime-order group, self-referential collision |
      | 2 | lock10 or lock03 (rebalanced to 512/512) | high-degree cyclotomic torus |
      | 3 | variant5 / lock08 via fpylll | lattice / Coppersmith |
      | 4 | lock09 | kleptographic SETUP |

      Retire variant6 as an entry layer: it is the weakest link and the cascade
      is only as strong as its first gate.
- [ ] Re-generate with fresh seeds, keep `solution.json` outside git, and
      write a release checklist (no δ/p/q/M_p in the public file, seeds not in docs).

### Stage 4: External validation

- [ ] Blind playtest: give the V4 public file to solvers (human and AI) with
      no repo access, and record time to each layer and where they got stuck.
- [ ] Update the docs with measured results only. Remove marketing claims
      ("90% original", "locks out AI") unless the playtest supports them.

---

## Decision needed from the maintainer

**Target difficulty.** "Hard but solvable in a weekend CTF" and "maximal
barrier" lead to different K bounds and a different entry layer. Stage 2 gives
the numbers, but the target has to be chosen before Stage 3.
