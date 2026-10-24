# Cryptographic Trapdoor Arsenal Research Report & Verification Suite (V3.0)

This deliverable provides a rigorous academic research report and runnable Python verification suite of **10 brand-new, mathematically verified algebraic & kleptographic RSA/timelock trapdoors** (completely distinct from the existing Variants 5, 6, 7, and 9 in the repository), engineered specifically to defeat LLM-based automated cryptanalysis (DeepSeek-R1/V3, Tencent Yuanbao) across both web-search retrieval and sandbox execution.

## User Review & Critical Decisions

> [!IMPORTANT]
> All four core architectural decisions were confirmed during Phase 1 clarification and govern the scope of the research report and verification suite.

- **Confirmed Decision 1 (Deliverable Format)**: Produce an exhaustive, implementation-grade Markdown specification report (`TRAPDOOR_ARSENAL_V3.md`, plus updated documentation) paired with runnable Python verification scripts and an automated test/benchmark runner.
- **Confirmed Decision 2 (Runtime Dependency Baseline)**: Target pure Python 3 with `gmpy2` acceleration (and graceful fallback to the repository's self-contained `ctflib.py` primitives: Kronecker-substitution polynomial multiplication, Newton-iteration division, subproduct/remainder trees `batch_poly_gcd`, integer LLL, and ring/curve arithmetic).
- **Confirmed Decision 3 (Public Challenge Surface)**: Restrict all challenge surfaces strictly to standard $(N, e=65537, c)$, full-sized custom public exponent $(N, e, c)$, or standard timelock $(N, P_0, T)$ tuples—zero suspicious field names, zero exposed bit-masks, and full statistical indistinguishability.
- **Confirmed Decision 4 (Orthogonality to Existing Repo)**: All 10 methods are 100% distinct from the existing Variant 5 (2-stage quadratic $e$ lattice + shift Coppersmith), Variant 6 (hidden shared base $3^{186}+\delta_1$), Variant 7 ($\Phi_3(p)$ cubic Pell norm-1 torus), and Variant 9 ($D=3$ Eisenstein prime-order CM curve self-referential collision).

---

## 1. Overview & Core Concept

- **What It Does**: Delivers a two-part cryptographic design arsenal:
  1. **Exhaustive Specification Report**: Covers 10 advanced, cold-spot mathematical trapdoors across all 6 mandatory sections (Academic Provenance & Coldness Audit, KeyGen & Trapdoor Mathematics, Public Challenge Surface, Domestic LLM Failure Analysis across Sandbox & Search, Solver Algorithm Derivation, and Claude Implementation Specification with exact bit parameters, pseudocode, and edge-case pitfalls).
  2. **Runnable End-to-End Python Verification Suite**: Implements `generate_challenge()` and `solve_challenge()` for the new trapdoor families using `ctflib.py` and `gmpy2`, ensuring zero unverified heuristics, zero missing helper functions, and measured wall-clock solve times.
- **Target Audience / Persona**: Cryptographic challenge designers and automated implementation agents (Claude) building multi-layer "Creator vs. Solver" CTF challenges aimed at defeating frontier LLMs equipped with Python/SageMath sandboxes and web search.
- **Key Value**: Eliminates the failure modes identified in the repository's audit of the prior V2.0 report (broken congruences, missing `batch_poly_gcd`, unsolvable lattice bounds, and known CTF writeup collisions like `hxp 2021 f_cktoring`) by grounding every trapdoor in verified 1989–2026 academic number theory and testing each construction in Python.

---

## 2. User Experience & Visual Design

- **Key User Flows**:
  1. **Specification Review Flow**: The challenge designer or implementation agent reads `TRAPDOOR_ARSENAL_V3.md`, which presents a comparative difficulty/orthogonality matrix followed by the 10 complete 6-module technical specifications ready for direct coding.
  2. **Single-Method Verification Flow**: The user runs any individual trapdoor module from the CLI with configurable bit-security / search-bound flags to inspect KeyGen timing, public parameters, statistical sanity checks, and end-to-end solver recovery of $(p, q)$.
  3. **Full Suite Benchmark Flow**: The user runs the master verification suite to validate all 10 trapdoor mechanisms sequentially and output a clean summary table of KeyGen time, Solver time, and factor recovery verification.
- **Formatting & Editorial Structure**:
  - *Report Structure*: Crisp mathematical LaTeX notation (`$$\Phi_k(p)$$`, commutative diagrams, explicit ring homomorphisms), structured comparison tables, and self-contained Python/SageMath specification blocks.
  - *CLI Output Discipline*: Clean, deterministic progress logging matching the existing repository style (`[KeyGen]`, `[Public Surface]`, `[Solve]`, `[Verified]`) with timing telemetry.

---

## 3. Key Product Decisions & Trade-Offs

- **Decision 1: Selection of the 10 Orthogonal Trapdoor Constructions**
  - *Chosen Approach*: We curate 10 mathematically distinct constructions spanning five algebraic domains so that solving one layer provides zero reusable templates for the next:
    1. **Method 1 — $\Phi_6(p)$ Sextic Algebraic Torus $\mathbb{T}_6$ Rational Compression Trapdoor (`(N, e, c)`)**: Grounded in Rubin & Silverberg (*CRYPTO 2003*, CEILIDH) and Bruno Sterner (*IACR ePrint 2026/2116*, *"Smooth evaluations of cyclotomic quadratics"*). Embeds the trapdoor in $\Phi_6(p) = p^2 - p + 1$ using rational torus coordinates and a cross-modulus exponent entanglement, while keeping $p-1$, $p+1$, and $\Phi_3(p)$ strongly non-smooth.
    2. **Method 2 — $\Phi_4(p)$ Gaussian Norm-1 Conic & Rédei Rational Function Trapdoor (`(N, e, c)` or `(N, P0, T)`)**: Grounded in Barbero, Cerruti & Murru (*Designs, Codes and Cryptography* / *arXiv*, Rédei rational functions over Pell conics) and Bach & Shallit (*Math. Comp.* 1989). Operates over the non-split quadratic torus $x^2 + dy^2 \equiv 1 \pmod N$ of order $\Phi_4(p) = p^2+1$ via Rédei rational evaluation $R_k(z)$ with a hidden primes-only meet-in-the-middle exponent relation.
    3. **Method 3 — $\Phi_8(p) = p^4 + 1$ Octic Cyclotomic Ring Endomorphism Trapdoor (`(N, e, c)`)**: Grounded in Bach & Shallit (*Math. Comp.* 1989) and Williams/Guy higher-cyclotomic factoring. Constructs $p$ such that $p^4 + 1$ has a massive smooth cofactor while $p-1, p+1, p^2+1, p^2\pm p+1$ are all rough, requiring arithmetic in the quotient ring $(\mathbb{Z}/N\mathbb{Z})[t]/(t^4+1)$ combined with polynomial Batch-GCD.
    4. **Method 4 — Non-Maximal Imaginary Quadratic Order Conductor & Ring-Class Group Trapdoor (`(N, e=65537, c)`)**: Grounded in Paulus & Takagi (*PKC 2000*, NICE), Castagnos & Laguillaumie (*CT-RSA 2015*), and mutated beyond `hxp 2021 f_cktoring`. Uses a higher-conductor non-maximal order $\mathcal{O}_f$ with discriminant $\Delta_K = -7$ or $-11$ ($j$-invariant $\neq 0, 1728$, so $a, b \neq 0$) where $p$ and $q$ are coupled via the Frobenius trace across two distinct CM discriminants.
    5. **Method 5 — Genus-2 Hyperelliptic Kummer Surface $\mathcal{K}_C$ Fast Ladder Trapdoor (`(N, P0, T)` or `(N, e, c)`)**: Grounded in Gaudry (*EUROCRYPT 2007*), Cosset (*Math. Comp.* 2010, Kummer ECM), Costello, Bos, Hisil & Lauter (*EUROCRYPT 2013*), and Dryło & Pomykała (*2025*). Embeds a smooth/entangled group order in the Jacobian $\mathrm{Jac}(C)(\mathbb{F}_p)$ of a genus-2 curve of order $\approx p^2$, evaluated purely via inversion-free projective theta coordinates on the Kummer surface.
    6. **Method 6 — Non-Commutative Quaternion Algebra $\left(\frac{a, b}{\mathbb{Z}/N\mathbb{Z}}\right)$ Reduced-Norm Torus Trapdoor (`(N, e, c)`)**: Grounded in Markelova (*Prikladnaya Diskretnaya Matematika* 2022) and non-split quaternion division algebras over $\mathbb{F}_p$. Repairs the broken Variant 10 from the V2.0 report by using a genuine base-field twist and reduced-trace polynomial collision with small-norm smooth multipliers so evaluation takes seconds rather than 4.3 hours.
    7. **Method 7 — Third-Order Characteristic Lucas / Dickson Sequence $(V_n(P, Q, 1))$ Asymmetric Exponent Trapdoor (`(N, e, c)`)**: Grounded in Lidl, Mullen & Turnwald (*Dickson Polynomials*, Pitman Monographs) and third-order matrix/trace recurrence cryptanalysis. Uses trace representations of roots of an irreducible cubic $x^3 - Px^2 + Qx - 1 \pmod p$ where the characteristic polynomial splits as $(1+1+1)$ mod $q$ and remains irreducible $(3)$ mod $p$, creating an asymmetric exponent trapdoor between $p^2+p+1$ and $q-1$.
    8. **Method 8 — Reciprocal / Rational-Relation Implicit Factoring Orthogonal Lattice Trapdoor (`(N, e=65537, c)`)**: Grounded in May & Ritzenhofen (*PKC 2009*), Nitaj & Ariffin (*IACR ePrint 2014/548*), and Herrmann & May (*ASIACRYPT 2008*). Embeds a balanced nonlinear modular relation $a_1 p + a_2 q \equiv p_0 \pmod{M_{\text{hidden}}}$ or reciprocal relation $p \cdot q_{\text{rev}} \equiv \text{small} \pmod R$ that reveals zero MSB/LSB bit patterns in $N$, solvable via a low-dimension homogeneous orthogonal + Herrmann-May lattice within pure Python LLL limits ($\le 8$ dimensions).
    9. **Method 9 — Kleptographic Dual-Modulus / Self-Referential Polynomial ECDH SETUP Trapdoor (`(N, e=65537, c)`)**: Grounded in Young & Yung (*CRYPTO 1996/1997*), Crépeau & Slakmon (*CT-RSA 2003*), and Ting-Yun Yeh (*IACR ePrint 2025/1480*, *"SoK: Kleptographic Attacks"*). Embeds $p$ via an elliptic-curve / Chebyshev polynomial pseudorandom map seeded from a compressed algebraic invariant of $N$ itself, eliminating the explicit bit-window leakage of classic Crépeau-Slakmon.
    10. **Method 10 — Montgomery-Twisted $\Phi_{12}(p) = p^4 - p^2 + 1$ Sextic-Quadratic Cascade Trapdoor (`(N, e, c)`)**: Grounded in Lenstra & Verheul (*CRYPTO 2000*, XTR) and Bach & Shallit (*Math. Comp.* 1989). Places the smooth trapdoor inside the 12th cyclotomic polynomial $\Phi_{12}(p) = p^4 - p^2 + 1$, immune to all $\Phi_1, \Phi_2, \Phi_3, \Phi_4, \Phi_6$ factoring scripts and standard ECM, unlocked via degree-4 cyclotomic trace recurrences and subproduct-tree Batch-GCD.
  - *Why*: Every method targets a structural blind spot of LLM sandbox scripts (which only test $\Phi_1, \Phi_2$, standard ECM, and 1D Coppersmith) while avoiding all published CTF writeup signatures.
  - *Alternatives Considered*: Reusing or slightly tweaking $D=3$ Eisenstein CM (`variant9`) or $\Phi_3$ cubic Pell (`variant7`) was rejected per Confirmed Decision 4.

- **Decision 2: Fast Polynomial & Lattice Arithmetic Within Pure Python + `gmpy2`**
  - *Chosen Approach*: Leverage `ctflib.py`'s Kronecker-substitution polynomial multiplication and Newton-iteration remainder trees (`batch_poly_gcd`) alongside `gmpy2.mpz` arithmetic, and constrain all lattice-based methods to dimensions $d \le 10$ so integer LLL finishes in $< 3$ seconds without requiring external C++ `fpylll` binaries.
  - *Why*: Guarantees that every single method in the report has a 100% working, fast, self-contained Python implementation that runs in under 60 seconds per challenge.

---

## 4. Technical Architecture & Data Strategy *(Technical Reference)*

### Architecture & Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                TRAPDOOR_ARSENAL_V3.md (Master Research Report)              │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌───────────────────┐  │
│  │ 1. Literature &      │  │ 2-4. KeyGen Math,    │  │ 5-6. Solver Math  │  │
│  │    CTF Coldness      │  │      Public Surface, │  │      & Claude     │  │
│  │    Verification      │  │      LLM Failure Sim │  │      Coding Spec  │  │
│  └──────────────────────┘  └──────────────────────┘  └───────────────────┘  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Direct 1:1 Mathematical Mapping
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 Verification & Benchmark Suite (Python 3)                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Method Modules (10 Orthogonal Algebraic & Kleptographic Constructions)│  │
│  │  • Cyclotomic Tori: Phi_6 (T_6), Phi_4 (Redei), Phi_8, Phi_12         │  │
│  │  • Higher-Genus & CM: Non-Maximal CM Order, Genus-2 Kummer Surface    │  │
│  │  • Non-Commutative & Recurrence: Quaternion Norm-1, 3rd-Order Dickson │  │
│  │  • Lattice & Klepto: Reciprocal Orthogonal Lattice, Polynomial SETUP  │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      │ Calls Core Algebraic Primitives      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Shared Computational Engine (ctflib.py + gmpy2 acceleration)          │  │
│  │  • Kronecker Substitution Poly Mul & Newton Series Division           │  │
│  │  • Subproduct / Remainder Tree Batch-GCD over Z/NZ                    │  │
│  │  • de Weger Exact Integer LLL & Root Extraction                       │  │
│  │  • Projective / Torus / Kummer / Quaternion Ring Arithmetic mod N     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Model & State
- **Public Challenge Tuple**: Each trapdoor generator outputs a clean public tuple—either `(N, e, c)` (with $e=65537$ or full-sized $e \in \mathbb{Z}_N^*$) or `(N, P0, T)`—alongside a private verification dictionary `sk = {p, q, trapdoor_invariants}` used strictly by the test harness to assert correctness.
- **Solver Interface**: Each solver accepts *only* the public challenge tuple and public security bounds, returning `(p, q)` verified via `p * q == N` and primality checks.

### Interactive Component & State Mapping
- **CLI Verification Runner**: Supports running individual methods (`--method 1..10`), running quick smoke verification across all 10 methods (`--quick`), or running full benchmark scale (`--full`), validating that:
  1. $|p - q| > 2^{500}$ (immune to Fermat/Lehman).
  2. $p-1$ and $p+1$ contain large rough factors (immune to Pollard $p-1$ and Williams $p+1$).
  3. The solver recovers $p, q$ from the public tuple alone within the target time window.
