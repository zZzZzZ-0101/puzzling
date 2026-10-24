# Roadmap

_Last updated 2026-10-24, after Stages 1–3._

Numbers marked **measured** come from runs on 2026-10-24 (4-core cloud
container, gmpy2 + fpylll unless noted). Full tables: [benchmarks.md](benchmarks.md).

---

## Where things stand

### Lock registry (14 locks, one interface)

| Lock | Technique | Quick test | Edge suite, 20 seeds | Solve at default K |
| :--- | :--- | :--- | :--- | ---: |
| lock01 | Φ₆ torus T₆ | pass | pass (decoy off + on) | 2.0 s |
| lock02 | Φ₄ Rédei conic | pass | pass (decoy off + on) | 1.5 s |
| lock03 | Φ₈ torus, 332-bit p | pass | pass | 3.2 s |
| lock04 | D = −7 CM curve | pass | pass (decoy off + on) | 22.1 s |
| lock05 | genus-2 Jacobian | pass | pass (decoy off + on) | 42.0 s |
| lock06 | quaternion over R₃ | pass | pass (decoy off + on) | 10.8 s |
| lock07 | prime-order SL₃ | pass | pass | 0.7 s (keygen 5 s) |
| lock08 | 4D lattice + Coppersmith | pass | pass | 0.01 s |
| lock09 | Chebyshev / Lucas-V SETUP | pass | pass | < 0.01 s |
| lock10 | Φ₁₂ torus, 332-bit p | pass | pass | 6.0 s |
| variant5 | orthogonal lattice + 20-dim Coppersmith | pass (needs fpylll) | — | 1.2 s (mask 2) |
| variant6 | hidden shared base | pass | — | 0.1 s (d1 16 bits) |
| variant7 | cubic Pell torus Φ₃ | pass | — | 1.8 s (2^11) |
| variant9 | prime-order D = 3 CM curve | pass | — | 19.2 s (2^15) |

CI (`.github/workflows/ci.yml`) runs the quick tests and a one-seed edge suite
with and without gmpy2/fpylll. Both jobs passed on the first push.

---

## What was built

### Stage 1: correctness and hygiene ✅

- [x] **Public surface stripped.** Generators publish `{N, e}` only; search
      bounds moved to `sk["params"]` and into solver keyword arguments. A cascade
      is `{public, private}`, and each public layer is exactly `N, e, c, next`.
      Envelope keys depend on layer depth and primes, not on lock names.
- [x] **lock04 key generation fixed.** u started at 1.375·2^255, so p = u² + 7v²
      was always 511 bits and the 512-bit check rejected every candidate forever.
- [x] **N no longer sits at 2^1023.** lock01/lock04 started the q search at the
      bottom of its range, so N's top bits read 1000…0. The search start is now random.
- [x] **lock07** back in the edge suite (keygen 79 s pure, 5 s with gmpy2).
- [x] **lock02 decoy** now guarantees the advertised ≥ 2^50 continued-fraction
      spike. The edge suite passes on 20 seeds per lock, 340 instances in total.
- [x] **Decoys are opt-in** (`decoy=True`; default off). The edge suite
      asserts they are absent by default and present when requested.
- [x] **Exponents look uniform.** e used to sit just below N (lock05/06) or
      run 10+ bits short (lock03/10). It is now lifted to a random representative in (N/2, N).
- [x] `tests/test_quick.py` (15 tests, ~75 s) and a GitHub Actions workflow.

### Stage 2: difficulty calibration ✅ (one item not built)

- [x] `--K` knob for every lock (`verify_locks --lock X --K n`) and
      `trapdoor/arsenal/benchmark.py`, with results in [benchmarks.md](benchmarks.md).
- [x] Optional **gmpy2** (big-int products, primality) and **fpylll** (LLL)
      backends in `ctflib`; `TRAPDOOR_PURE=1` forces pure Python.
- [x] **variant5 Stage 2 runs**: the 20-dim Coppersmith lattice recovers p in
      5 s with fpylll (it was blocked before).
- [x] **variant9 at K = 2^18**: verified end to end. It factored N in 2318 s
      (38.6 min, hit on twist 14, gmpy2, shared CPU).
- [ ] **Generic-attack harness: not built in this round.** The edge suite
      still runs its existing small set of standard checks (trial division,
      Fermat, p−1, p+1, Wiener) against every generated key.

Main finding: up to K = 2^13 every lock's cost is dominated by fixed work
(fitted exponents 0.15–0.95). lock08, lock09 and variant6 cost almost nothing
once the structure is known, so their difficulty is all insight. variant9 is
the only lock whose cost scales close to linearly with K.

### Stage 3: unified cascade V4 ✅

- [x] Variants 5/6/7/9 registered in `LOCK_REGISTRY` (`variant_locks.py`).
      variant7's cubic non-residue `a` is no longer public; the solver searches for it.
- [x] One engine (HMAC envelope). The V2.1 XOR-keystream tri-cascade is kept
      as legacy, only so the published challenge stays solvable.
- [x] `trapdoor/v4.py`: build / solve / release check, in two tiers:

      | Tier | Layers | Build | Solve (measured) |
      | :--- | :--- | ---: | ---: |
      | ctf | variant9 2^13 → lock02 2^13 → lock08 mask 4 → lock09 2^11 | 1.9 s | 19.8 s |
      | hard | variant9 2^16 → lock02 2^15 → variant5 mask 8 → lock09 2^13 | 1.3 s | 272.9 s |

- [x] [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md); `v4 check` automates most of it.
- Deviation from the plan: **lock03/lock10 could not be rebalanced to 512/512.**
  With a 512-bit p, Φ₈(p) and Φ₁₂(p) are about 2048 bits. Keeping the trapdoor
  modulus below N then needs a smooth part of at least 1024 bits, and the CRT
  construction would have to pin p modulo a number larger than p itself. lock02
  (Φ₄, balanced primes) takes the torus slot instead.
- No challenge instance is committed. This repository names the V4 lineup, so
  a release must be built privately with a fresh seed (see the checklist).

---

## What is left

1. **Target difficulty: decided, ctf tier.** The release candidate is
   `python3 -m trapdoor.v4 build --tier ctf` (the default). The hard tier stays
   available, but it is not the release target.
2. **Stage 4: blind playtest of a ctf-tier build.** Give a freshly built
   `challenge.json`, and nothing else, to solvers, and record time per layer
   and where they stall. Adjust the ctf bounds from what the playtest shows.
3. **lock05 / lock06 speed.** These two solvers spend their time in
   pure-Python group arithmetic that neither backend touches. A vectorised or
   C implementation would let them run at larger K.
4. **Generic-attack coverage** beyond the edge suite's current checks, if wanted.
5. Doc cleanup: `docs/arsenal/*` still carry the export's original claims
   ("defeats frontier LLMs", etc.). They predate these measurements.
