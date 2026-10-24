> Moved from the AI Studio export (`puzzling (1).zip`). Paths below are pre-reorganisation: `locks_A.py` etc. now live in `trapdoor/arsenal/`, `main.py` is `trapdoor/arsenal/dashboard.py`, `edge_tests.py` is `tests/edge_suite.py`. Claims here are the export's own; see `docs/ROADMAP.md` for verified status.

# Cryptographic Trapdoor Arsenal V3.2 — 10 Separated Locks & Composable Cascade Engine

This repository contains both the original 4-layer cryptographic challenge (`variant5.py`, `variant6.py`, `variant7.py`, `variant9.py`) and the newly architected **10-Lock Orthogonal Trapdoor Arsenal** (`trapdoors.md`, `TRAPDOOR_ARSENAL_V3.md`, `locks_A.py`, `locks_B.py`, `cascade_engine.py`, `verify_locks.py`, and `main.py`).

---

## 1. Repository File Architecture

| File | Role & Contents |
| :--- | :--- |
| `trapdoors.md` | **Formal Mathematical Framework**: Complete 6-module structure (Academic Source, Math Principles, Public Surface, AI Defeat Logic, Solver Path, Implementation Spec) for all 10 separated trapdoor locks plus the universal cascade specification. |
| `TRAPDOOR_ARSENAL_V3.md` | Chinese technical specification & anti-LLM defense architecture report for Locks 01–10. |
| `locks_A.py` | Pure-Python implementations (`generate` & `solve`) for **Locks 01 to 05** (Cyclotomic Torus $\mathbb{T}_6$, Gaussian Rédei $\Phi_4$, Octic Torus $\Phi_8$, $\Delta_K=-7$ CM Curve, Genus-2 Hyperelliptic Cantor Jacobian). |
| `locks_B.py` | Pure-Python implementations (`generate` & `solve`) for **Locks 06 to 10** (12D Quaternion Algebra $\mathbb{H}_{-1,-1}(R_3)$, Prime-Order $\mathrm{SL}_3$ Cubic Lucas, 4D+4D Dyadic Coppersmith Cascade, Chebyshev/Lucas-$V$ SETUP, Dodecic Torus $\mathbb{T}_{12}$). |
| `cascade_engine.py` | Unified `LOCK_REGISTRY`, standalone runner (`generate_single_lock`, `solve_single_lock`), and multi-layer Matryoshka cascade builder/solver (`build_cascade`, `solve_cascade`). |
| `main.py` | Interactive Web Dashboard server on `0.0.0.0:3000` (with REST endpoints `/`, `/health`, `/api/locks`, `/api/test-lock`, `/api/test-cascade`, `/api/report`) and CLI dispatcher. |
| `verify_locks.py` | Dedicated CLI verification & benchmark runner for testing individual locks, custom lock cascades, or the full 10-lock suite. |
| `edge_tests.py` | 6-dimensional adversarial test suite verifying strict 1024-bit $N$ & $1 < e < N$ geometry, NIST monobit entropy, planted False-Hope Honey-Trap disguises (ECF Ghost Convergent, Fake ROCA, etc.), LLM sandbox autopilot immunity, and Cascade HMAC tamper rejection. |
| `CHANGELOG.md` | Detailed chronological audit log of all architectural additions, mathematical proofs, bug fixes, and file updates. |
| `ctflib.py` | Self-contained pure-Python cryptographic & algebraic number theory library (Kronecker polynomial multiplication, Newton division, subproduct/remainder tree `batch_poly_gcd`, integer LLL `lll`, ECM/Pollard utilities). |
| `package.json` & `metadata.json` | Container supervisor startup (`npm run dev` / `npm run build`) and AI Studio applet metadata. |
| `variant5.py`, `variant6.py`, `variant7.py`, `variant9.py` | Original repository variants (preserved unmodified for backward compatibility). |

---

## 2. Summary of the 10 Separated Locks & Planted False-Hope Honey-Traps

Every lock exposes **only** a clean 1024-bit RSA tuple `(N, e, c)` with $1 < e < N$ on the public surface—zero auxiliary curve coefficients, zero matrix parameters, and zero bit-prefix hints—while embedding false-hope honey-trap decoys that lure automated solvers into dead-end branches:

1. **Lock 01 (`lock01`)**: $\Phi_6(p) = p^2 - p + 1$ Cyclotomic Ring $\mathbb{Z}_N[\zeta_7]$ Galois-Frobenius Torus $\mathbb{T}_6$ with Projective Möbius Entanglement $\delta_2(N-3) \equiv \delta_1(2N+5) \pmod{C_6}$ + **Fake 2-Adic Fermat Mask $N \equiv 1 \pmod{2^{12}}$** — **Surface: `(N, e=65537, c)`**.
2. **Lock 02 (`lock02`)**: $\Phi_4(p) = p^2 + 1$ Projective Rédei Conic $\mathbb{P}^1_\Delta(\mathbb{Z}_N[i])$ ($\Delta = 1 + 2i$) with Twisted Bilinear Entanglement $\delta_2(e+3N) \equiv \delta_1(2e+5N) \pmod{C_4}$ + **Legendre ECF Ghost Convergent $k_{\text{fake}}/d_{\text{fake}}$ ($a_r > 2^{50}$ continued-fraction spike)** — **Surface: `(N, e, c)`**.
3. **Lock 03 (`lock03`)**: $\Phi_8(p) = p^4 + 1$ Octic Cyclotomic Torus $\mathbb{P}^1_t(R_4)$ over $R_4 = \mathbb{Z}_N[t]/(t^4-2t^2+5)$ with Octic Shifted Entanglement $\delta_2(e+7N) \equiv \delta_1(3e+11N) \pmod{C_8}$ ($332\text{b} \times 692\text{b}$ exact $1024\text{b}$ $N$) — **Surface: `(N, e, c)`**.
4. **Lock 04 (`lock04`)**: Discriminant $\Delta_K = -7$ ($j = -3375 \neq 0, 1728$, conductor $f=2$) CM Curve with Projective Möbius Scalar $\delta_2(N-2) \equiv \delta_1(2N+3) \pmod{C_{-7}}$ + **Fake ROCA Primorial Signature $N \equiv 65537^{1337} \pmod{P_{37}}$** — **Surface: `(N, e=65537, c)`**.
5. **Lock 05 (`lock05`)**: Genus-2 Hyperelliptic Curve $\mathrm{Jac}(y^2 = x^5 + 8)$ Cantor Divisor Lock with Quadratic Self-Referential Entanglement $\delta_2(e+N^2) \equiv \delta_1(2e+N) \pmod{C_{\text{jac}}}$ + **Fake Low-Exponent Mask $e \equiv 3 \pmod{2^{80}}$** — **Surface: `(N, e, c)`**.
6. **Lock 06 (`lock06`)**: 12D Non-Commutative Quaternion Algebra $\mathbb{H}_{-1,-1}(\mathbb{Z}_N[t]/(t^3-2))$ Hilbert-90 & Relative Cubic Norm $\mathrm{Norm}_{6/2}(\beta)$ with $\delta_2(e-2N) \equiv \delta_1(3e+4N) \pmod{C_6}$ + **Fake 120-Bit LSB Match $e \equiv N \pmod{2^{120}}$** — **Surface: `(N, e, c)`**.
7. **Lock 07 (`lock07`)**: Prime-Order Companion Matrix Cubic Lucas Group $\mathrm{SL}_3(\mathbb{Z}/N\mathbb{Z})$ where $M_3 = p^2+p+1$ is a **1024-bit PRIME** (0% smoothness) with $\delta_2(e+2N) \equiv \delta_1(3e+5N) \pmod{M_3}$ and Dual-Trace Invariant $\mathrm{Tr}(\mathbf{A})+3\mathrm{Tr}(\mathbf{A}^2)$ — **Surface: `(N, e, c)`**.
8. **Lock 08 (`lock08`)**: Two-Stage 4D Cubic Orthogonal Lattice + Base-$2^{240}$ Dyadic-Folded 4D Linear Divisor Coppersmith Cascade (`m=2, t=2`, 106-bit root) — **Surface: `(N, e, c)`**.
9. **Lock 09 (`lock09`)**: Symmetric Chebyshev / Lucas-$V$ Product-to-Sum Kleptographic SETUP ($V_{d_1}(7)V_{d_2}(7) \equiv V_{d_1+d_2}(7) + V_{|d_1-d_2|}(7) \pmod{\Phi_6(2^{180})}$) + **Fake Fermat 20-Bit Near-Square Halo** — **Surface: `(N, e=65537, c)`**.
10. **Lock 10 (`lock10`)**: $\Phi_{12}(p) = p^4 - p^2 + 1$ Dodecic Cyclotomic Ring $\mathbb{Z}_N[\zeta_{13}]$ 4-Term Frobenius Torus Projection with Dodecic Galois-Twisted Entanglement $\delta_2(e+4N) \equiv \delta_1(5e+9N) \pmod{C_{12}}$ — **Surface: `(N, e, c)`**.

---

## 3. Quick Start & Usage

### Run Web Dashboard on Port 3000
```bash
python3 -m trapdoor.arsenal.dashboard
```

### Run Edge-Case, Honey-Trap Disguise & Adversarial Autopilot Test Suite
```bash
python3 -u -m tests.edge_suite
```

### Run a Single Lock or Cascade via CLI
```bash
python3 -u -m trapdoor.arsenal.verify_locks --lock lock01
python3 -u -m trapdoor.arsenal.verify_locks --lock lock02
python3 -u -m trapdoor.arsenal.verify_locks --cascade lock01,lock04,lock08,lock09
```
