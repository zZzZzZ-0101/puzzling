# CHANGELOG — Cryptographic Trapdoor Arsenal & Composable Cascade Engine

All architectural additions, mathematical trapdoor constructions, debugging discoveries, and file updates are recorded below in detail.

---

## [V3.4.0] — 2026-10-24: False-Hope Honey-Trap Disguises, Projective Möbius Entanglements & Edge-Test Suite (`edge_tests.py`)

### 1. Planted False-Hope Honey-Trap Disguises (Anti-LLM Decoy Architecture)
- **Lock 01 (`locks_A.py`)**: Planted 2-adic Fermat mask $N \equiv 1 \pmod{2^{12}}$ coupled with Projective Möbius Torus entanglement $\delta_2(N - 3) \equiv \delta_1(2N + 5) \pmod{C_6}$ and $4$-term cyclotomic projection $\Psi_6(\beta) = \sigma_4(\beta)\sigma_3(\beta)(\sigma_1(\beta)\beta)^{-1} \in \mathbb{T}_6(\mathbb{F}_p)$.
- **Lock 02 (`locks_A.py`)**: Planted Legendre Continued-Fraction Ghost Convergent $k_{\text{fake}} / d_{\text{fake}}$ in $e / N$ ($d_{\text{fake}} \approx 2^{196}$ prime, producing a massive partial quotient spike $a_r > 2^{50}$ in Euclidean continued fractions that lures Wiener/Boneh–Durfee scripts into an unsolvable decoy lattice) while the true trapdoor is Twisted Bilinear Rédei $\delta_2(e + 3N) \equiv \delta_1(2e + 5N) \pmod{C_4}$.
- **Lock 03 (`locks_A.py`)**: Unbalanced $332\text{-bit} \times 692\text{-bit}$ exact $1024$-bit modulus $N$ with Octic Shifted Entanglement $\delta_2(e + 7N) \equiv \delta_1(3e + 11N) \pmod{C_8}$ ensuring $C_8 < N$ and $1 < e < N$.
- **Lock 04 (`locks_A.py`)**: Planted Fake ROCA Primorial Discrete-Log Signature $N \equiv 65537^{1337} \pmod{P_{37}}$ ($P_{37} = \prod_{3 \le \ell \le 37} \ell$) alongside Projective Möbius CM entanglement $\delta_2(N - 2) \equiv \delta_1(2N + 3) \pmod{C_{-7}}$ on $j = -3375$.
- **Lock 05 (`locks_A.py`)**: Planted Fake Masked Low-Exponent decoy $e \equiv 3 \pmod{2^{80}}$ with Quadratic Self-Referential Jacobian entanglement $\delta_2(e + N^2) \equiv \delta_1(2e + N) \pmod{C_{\text{jac}}}$ and Mumford discriminant invariant $\Delta_{\text{Mumford}}(u) = u_1^2 - 4u_0 \bmod N$.
- **Lock 06 (`locks_B.py`)**: Planted Fake 120-bit LSB Partial-Key Exposure $e \equiv N \pmod{2^{120}}$ with Hilbert's Theorem 90 + Relative Cubic Norm $\mathrm{Norm}_{6/2}(\beta) = \beta^{1+p^2+p^4}$ and Skolem–Noether conjugation over $\mathbb{H}_{-1,-1}(\mathbb{Z}_N[t]/(t^3-2))$.
- **Lock 07 (`locks_B.py`)**: Twisted Bilinear Matrix Exponent $\delta_2(e + 2N) \equiv \delta_1(3e + 5N) \pmod{M_3}$ over 1024-bit prime-order $\mathrm{SL}_3(\mathbb{Z}/N\mathbb{Z})$ with polynomial-time Dual-Trace Invariant $\mathrm{Tr}(\mathbf{A}) + 3\mathrm{Tr}(\mathbf{A}^2) \bmod N$.
- **Lock 09 (`locks_B.py`)**: Planted Fake Fermat 20-bit Near-Square Halo (`(H1 >> 132) == (H2 >> 132)` while $|p - q| \ge 2^{480}$) over Chebyshev product-to-sum SETUP.
- **Lock 10 (`locks_B.py`)**: Unbalanced $332\text{-bit} \times 692\text{-bit}$ exact $1024$-bit modulus $N$ with Dodecic Galois-Twisted Entanglement $\delta_2(e + 4N) \equiv \delta_1(5e + 9N) \pmod{C_{12}}$.

### 2. Comprehensive Edge-Case & Adversarial Autopilot Test Suite (`/edge_tests.py`)
- Added `/edge_tests.py` verifying strict $1024$-bit $N$ & $1 < e < N$ geometry, NIST monobit entropy, all planted honey-trap disguises, immunity against 5 standard LLM autopilot attacks, boundary Coppersmith root recovery, and Cascade HMAC tamper rejection.

---

## [V3.3.0] — 2026-10-24: Formal Mathematical Framework (`trapdoors.md`) & Final Repository Synchronization

### 1. Formal 6-Module Mathematical Framework (`/trapdoors.md`)
- Created `/trapdoors.md` presenting the formal mathematical framework for all 10 separated trapdoor locks (`Lock 01` – `Lock 10`), strictly adhering to the 6-module structure for every lock:
  1. **Academic Source & Obscurity Verification (学术溯源与冷门度验证)**
  2. **Core Mathematical Principles & KeyGen Trapdoor (核心数学原理与暗门生成算法)**
  3. **Public Challenge Surface (公开卷面呈现)**
  4. **AI Defeat Logic (国产 AI 破防推演)**
  5. **Solver Path (解题破译算法)**
  6. **Implementation Specification & Complexity Analysis (工程实现规范与复杂度对比)**
- Documented the Universal Composable Cascade Framework (`cascade_engine.py`) and empirical timings across all 10 locks.

### 2. Full-Repository Synchronization
- Synchronized `/README.md`, `/TRAPDOOR_ARSENAL_V3.md`, and `/cascade_engine.py` (`LOCK_REGISTRY`) so all mathematical formulas, curve equations, and benchmark metrics match the verified implementations in `/locks_A.py` and `/locks_B.py`.

---

## [V3.2.0] — 2026-10-24: Dev Server Resolution, Web Dashboard & Container Health Compliance

### 1. Dev Server Startup Fix
- **Root Cause**: The AI Studio container runtime expects a `package.json` with a valid `"dev"` or `"start"` script to resolve and start the background web process. Because the repository previously contained only Python scripts without `package.json` or `metadata.json`, the dev server failed with `could not resolve dev command: no 'dev'/'start' scripts found in package.json`.
- **Resolution**:
  - Created `/package.json` defining `"dev": "python3 main.py"`, `"start": "python3 main.py"`, and `"build": "python3 -m py_compile main.py cascade_engine.py locks_A.py locks_B.py verify_locks.py ctflib.py"`.
  - Created `/metadata.json` specifying application name, description, and the required `MAJOR_CAPABILITY_SERVER_SIDE_GEMINI_API` capability.
  - Re-invoked `restart_dev_server` and confirmed clean startup and zero-latency HTTP 200 OK responses on `http://0.0.0.0:3000/`.

### 2. Interactive Web Dashboard & API Server (`main.py`)
- Configured `main.py` with an embedded, zero-dependency `ThreadingHTTPServer` bound to `0.0.0.0:3000`.
- Implemented real-time interactive UI and JSON endpoints:
  - `GET /`: Full responsive web interface with visual lock explorer, status metrics, and interactive lock/cascade runner.
  - `GET /health`: Instant `{"status": "ok"}` health check for automated monitors.
  - `GET /api/locks`: JSON list of all 10 algebraic trapdoor locks, their mathematical groups, public surfaces, and trapdoor types.
  - `POST /api/test-lock`: On-demand live generation and solving of any chosen lock (e.g., `lock01`..`lock10`).
  - `POST /api/test-cascade`: On-demand composition and solving of arbitrary cascades (e.g. `[lock01, lock04, lock08, lock09]`).
  - `GET /api/report`: Direct Markdown rendering of the complete technical specification.

---

## [V3.1.0] — 2026-10-23: Mathematical Refinements, Fast-Startup Entry Point, and Solver Speedups

### 1. Mathematical & Engineering Refinements
- **Lock 04 (`lock04_generate` / `lock04_solve` in `/locks_A.py`)**:
  - **Parity Proof & Fix**: For any odd prime $p = u^2 + 7v^2$, the elliptic curve $E_w: y^2 = x^3 - 35w^2x - 98w^3$ ($j = -3375 \neq 0, 1728$) has all three 2-torsion points rational over $\mathbb{F}_p$ because $x^3 - 35x - 98 = (x - 7)(x^2 + 7x + 14)$ and $\Delta(x^2 + 7x + 14) = -7$ is a quadratic residue modulo $p$. Consequently, $M_p = p + 1 \mp 2u$ is **always divisible by 4** and never an odd prime.
  - **Bit-Length Calibration**: Updated $u \in [2^{255}, 2^{256})$ and $v \in [2^{253}, 2^{254})$ so $p = u^2 + 7v^2$ hits 512-bit primes in `< 0.02s`.
  - **Exact Twist Selection & Odd-Parity Shifted Quadratic Congruence**: Tested $[p + 1 \mp 2u]P_0 = \mathcal{O}$ on the isomorphic Weierstrass scaled point $P_0 = (u_0 w \bmod p, w^2 \bmod p)$ at $u_0 = 1$ ($w = u_0^3 - 35u_0 - 98$) to select the exact twist order $M_p$, and used the shifted congruence:
    $$\delta_2 (N - 2) \equiv \delta_1 \pmod{M_p} \implies \delta_2 (N^2 - 4) \equiv \delta_1 (N + 2) \pmod{M_p}$$
    Because $\delta_1$ is an odd prime and $2\delta_2$ is even, $\delta_1 + 2\delta_2$ is guaranteed odd, so $r_q = (\delta_1 + 2\delta_2)(\delta_2 p)^{-1} \bmod M_p$ is always odd even though $4 \mid M_p$, allowing immediate prime generation for $q$ while keeping `(N, e=65537, c)`.
- **Lock 08 (`_coppersmith_linear_4d` in `/locks_B.py`)**:
  - Preserved exact integer values for $c_0^2$ and $2c_0$ in rows 3 and 4 of the 4D Herrmann–May lattice basis (removing premature `% N` reduction that broke $p^2$ divisibility of $(x + c_0)^2$), and added critical-point interval bisection for polynomial root extraction.

- **Lock 07 (`lock07_generate` / `lock07_solve` in `/locks_B.py`)**:
  - Verified during `lock07_generate` that the first companion matrix $\mathbf{M}_{2,3}$ (corresponding to $x^3 - 2x^2 + 3x - 1$) has order dividing the 1024-bit prime $M_3 = p^2 + p + 1$ in $\mathrm{SL}_3(\mathbb{F}_p)$, guaranteeing that `lock07_solve` hits on `trial = 1` on the first pass.

- **Lock 08 & Lock 09 (`locks_B.py`)**:
  - Calibrated `mask_bits = 4` in Lock 08 (`_coppersmith_linear_4d` with Howgrave–Graham bound $X < N^{1/6} \approx 2^{170.6}$ and $x_0 = 106\text{ bits}$) and $d_1, d_2 \in [200, 2^{11})$ in Lock 09 so $V_{d_i}(7)$ always wraps around $M_{\text{cheb}} = \Phi_6(2^{180})$ multiple times.

- **Lock 10 (`lock10_generate` in `/locks_B.py`)**:
  - Fixed fallback 12th-cyclotomic root extraction `r = sqrt_mod((1 - u) % l, l)`.

- **Subproduct Tree Collision Bound (`K_bound = 1 << 11`)**:
  - Standardized default `K_bound = 2048` (309 primes per side) across all algebraic torus/CM/Jacobian/quaternion/matrix locks so `batch_poly_gcd` completes in `< 0.6s` per lock.

- **Fast-Startup Split (`/main.py` & `/verify_locks.py`)**:
  - Separated the fast `< 0.05s` registry overview in `/main.py` from the full benchmark suite in `/verify_locks.py` so the AI Studio container startup health check never blocks on heavy cryptographic runs.

---

## [V3.0.0] — 2026-10-23: Initial 10 Separated Orthogonal Locks & Composable Cascade Engine

- Created `/locks_A.py` (Locks 01–05), `/locks_B.py` (Locks 06–10), `/cascade_engine.py`, `/TRAPDOOR_ARSENAL_V3.md`, and `/README.md`.
- Preserved `/ctflib.py`, `/puzzle_gen.py`, `/puzzle_solve.py`, `/variant5.py`, `/variant6.py`, `/variant7.py`, `/variant9.py`, and `/challenge.json` intact.
