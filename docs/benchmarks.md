# Benchmarks

All numbers were **measured** on 2026-10-24 on a 4-core cloud container
(x86_64, Python 3.13) with one generate + solve per point, seed 31337. Other
jobs ran at the same time, so treat single points as ±30 %. Reproduce with:

```bash
python3 -u -m trapdoor.arsenal.benchmark --out bench.jsonl          # all locks, default K lists
python3 -m trapdoor.arsenal.benchmark --report bench.jsonl          # this table
```

## Solve time vs search size (gmpy2 + fpylll installed)

"K" is each lock's size knob: log2 of `K_bound` for the collision locks,
`d1_bits` for variant6, `mask_bits` for the lattice locks.

| Lock | knob | solve time by K | exponent a (t ~ 2^(aK)) |
| :--- | :--- | :--- | ---: |
| lock01 | log2 K_bound | 9: 1.6s · 11: 2.0s · 13: 5.0s | 0.40 |
| lock02 | log2 K_bound | 9: 1.5s · 11: 1.5s · 13: 3.4s | 0.29 |
| lock03 | log2 K_bound | 9: 2.0s · 11: 3.2s · 13: 6.3s | 0.42 |
| lock04 | log2 K_bound | 9: 17.0s · 11: 22.1s · 13: 37.5s | 0.28 |
| lock05 | log2 K_bound | 9: 36.8s · 11: 42.0s · 13: 55.7s | 0.15 |
| lock06 | log2 K_bound | 9: 9.4s · 11: 10.8s · 13: 15.5s | 0.18 |
| lock07 | log2 K_bound | 9: 0.5s · 11: 0.7s · 13: 3.8s | 0.73 |
| lock08 | mask_bits | 2: 0.0s · 4: 0.0s · 6: 0.0s |  |
| lock09 | log2 K_bound | 9: 0.0s · 11: 0.0s · 13: 0.0s |  |
| lock10 | log2 K_bound | 9: 4.6s · 11: 6.0s · 13: 10.4s | 0.29 |
| variant5 | mask_bits | 1: 1.3s · 2: 1.2s · 3: 1.7s · 4: 3.0s | 0.41 |
| variant6 | d1_bits | 12: 0.0s · 16: 0.1s · 20: 1.4s |  |
| variant7 | log2 K_bound | 9: 1.1s · 11: 1.8s · 13: 5.5s | 0.59 |
| variant9 | log2 K_bound | 11: 1.4s · 13: 5.7s · 15: 19.2s | 0.95 |

## Effect of the optional backends

Same seed, `TRAPDOOR_PURE=1` (pure Python) vs gmpy2 + fpylll:

| Lock (K) | KeyGen pure → fast | Solve pure → fast | Where the time goes |
| :--- | ---: | ---: | :--- |
| variant6 (d1_bits 16) | 0.03 → 0.001 s | **87.1 → 0.08 s** | Coppersmith lattice (fpylll) |
| lock08 (mask 4) | 0.35 → 0.21 s | **4.2 → 0.01 s** | 4-dim lattices per δ (fpylll) |
| lock07 (2^11) | **78.9 → 5.2 s** | 1.1 → 0.7 s | primality tests on p and p²+p+1 (gmpy2) |
| variant9 (2^13) | 10.0 → 0.9 s | 9.0 → 5.7 s | primality tests; poly products (gmpy2) |
| lock06 (2^11) | 0.33 → 0.07 s | 13.0 → 10.8 s | quaternion exponentiation (pure-Python loops either way) |
| lock05 (2^11) | 0.08 → 0.01 s | 39.3 → 42.0 s | Cantor divisor arithmetic (pure-Python loops either way) |

## What the curves say

- **Up to K = 2^13, search size barely moves the clock.** Every exponent is
  below 1, so fixed per-solve costs (exponentiating by the smooth multiplier,
  building the curve or torus point) dominate. The batch-GCD tables only take
  over at larger K. The audit measured about K^1.65 at 2^15–2^18 for variant9.
- **lock08, lock09 and variant6 are effectively free once the structure is
  known.** Each costs one table lookup or a few tiny lattices, so their
  difficulty is entirely in recognising the construction. Raising K does not
  change that.
- **The fast backends matter most for lattices.** variant5's 20-dim Stage 2
  went from "not feasible" to about 0.5 s per δ with fpylll, and variant6's
  Coppersmith step went from 50–140 s to under 2 s.
- **variant9 is the only lock whose cost scales close to linearly** in this
  range, which is why it is the V4 entry layer.

## Long runs

**variant9 at K = 2^18, seed 20261023** (the audit's open TODO):
`python3 -u -m trapdoor.variants.variant9 --bits 18 --seed 20261023` factored N in
**2318 s (38.6 min)**. It hit on twist 14 with 23 000 × 23 000 tables, about
165 s per twist, using gmpy2 with three other jobs sharing the CPU. The earlier
1.6–1.8 h figure was a pure-Python extrapolation. Most of the cost is the 13
wrong twists tried first; their number depends on p and the solver cannot know it in advance.

## V4 tiers, end to end

| Tier | Lineup (K) | Build | Solve |
| :--- | :--- | ---: | ---: |
| ctf | variant9 (2^13) → lock02 (2^13) → lock08 (mask 4) → lock09 (2^11) | 1.9 s | 19.8 s |
| hard | variant9 (2^16) → lock02 (2^15) → variant5 (mask 8) → lock09 (2^13) | 1.3 s | 272.9 s (165.5 + 8.3 + 99.0 + 0.0) |
