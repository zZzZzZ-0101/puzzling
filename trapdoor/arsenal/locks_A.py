"""
locks_A.py — Pluggable Algebraic Trapdoor Locks 01 to 05
========================================================
Each lock implements a uniform pluggable interface:
  - generate(K_bound=..., seed=..., verbose=...) -> (pub_dict, sk_dict)
  - solve(pub_dict, verbose=...)                 -> (p, q)

All 5 locks in this module are 100% distinct from existing Variants 5, 6, 7, 9:
  Lock 01 : Phi_6(p) = p^2 - p + 1 Cyclotomic Ring Z_N[zeta_7] Frobenius Torus T_6
            with Self-Referential Cofactor Entanglement (Public surface: N, e=65537, c)
  Lock 02 : Phi_4(p) = p^2 + 1 Projective Redei Rational Conic over Z_N[i]
            with Dual-Track Exponent Entanglement (Public surface: N, e, c)
  Lock 03 : Phi_8(p) = p^4 + 1 Octic Cyclotomic Redei Torus P^1(R_4) over Z_N[t]/(t^4-2t^2+5)
            with Quartic Norm Non-Residue (Public surface: N, e, c)
  Lock 04 : Discriminant D = -7 (j = -3375 != 0, 1728) Conductor f=2 CM Curve
            with Quadratic-Congruence Frobenius Entanglement (Public surface: N, e=65537, c)
  Lock 05 : Genus-2 Quartic-CM Hyperelliptic Jacobian Jac(y^2 = x^5 + a) over Z/NZ
            via Cantor's Mumford Divisor Algorithm (Public surface: N, e, c)
"""
import math, random, time
from trapdoor.ctflib import (
    is_prime, primes_upto, sqrt_mod, inv_mod_n, FactorFound,
    batch_poly_gcd, ec_add, ec_mul
)


def _batch_inv_mod_n(vals, n):
    """Montgomery batch inversion modulo N (1 inversion + 3(k-1) muls).
    If any element shares a non-trivial factor with N, raises FactorFound(g).
    """
    if not vals:
        return []
    pref = [vals[0] % n]
    for v in vals[1:]:
        pref.append(pref[-1] * (v % n) % n)
    g = math.gcd(pref[-1], n)
    if g != 1:
        if 1 < g < n:
            raise FactorFound(g)
        for v in vals:
            gg = math.gcd(v % n, n)
            if 1 < gg < n:
                raise FactorFound(gg)
        raise ZeroDivisionError("batch_inv zero")
    inv_all = pow(pref[-1], -1, n)
    out = [0] * len(vals)
    for i in range(len(vals) - 1, 0, -1):
        out[i] = inv_all * pref[i - 1] % n
        inv_all = inv_all * (vals[i] % n) % n
    out[0] = inv_all
    return out


def _crt_combine(residues, moduli):
    r_all, M_all = 0, 1
    for r, l in zip(residues, moduli):
        g = pow(M_all, -1, l)
        r_all = r_all + M_all * ((r - r_all) * g % l)
        M_all *= l
    return r_all % M_all, M_all


def _lift_exponent(e_r, step, N, phi_N, tries=500):
    """Random e = e_r + m*step in (N/2, N) with gcd(e, phi_N) = 1.

    Taking the largest or smallest representative leaves e conspicuously close
    to N or short by a few bits; a random lift keeps e indistinguishable from
    a uniform exponent while preserving e mod step.
    """
    m_lo = max(0, (N // 2 - e_r) // step + 1)
    m_hi = (N - 1 - e_r) // step
    if m_hi < m_lo:
        return None
    for _ in range(tries):
        cand = e_r + random.randint(m_lo, m_hi) * step
        if 1 < cand < N and math.gcd(cand, phi_N) == 1:
            return cand
    return None


# ======================================================================
# LOCK 01: Phi_6(p) = p^2 - p + 1 Galois-Frobenius Torus T_6 in Z_N[zeta_7]
# ======================================================================

def _a7_canon(v, n):
    c6 = v[6]
    return [(v[i] - c6) % n for i in range(6)]


def _a7_mul(a, b, n):
    res = [0] * 7
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                res[(i + j) % 7] += ai * bj
    return [x % n for x in res]


def _a7_pow(base, k, n):
    res = [1, 0, 0, 0, 0, 0, 0]
    b = base[:]
    while k > 0:
        if k & 1:
            res = _a7_mul(res, b, n)
        b = _a7_mul(b, b, n)
        k >>= 1
    return res


def _a7_frob(a, k):
    s = pow(3, k, 7)
    out = [0] * 7
    for i in range(7):
        out[(i * s) % 7] = a[i]
    return out


def _poly_trim(p):
    p = p[:]
    while p and p[-1] == 0:
        p.pop()
    return p


def _poly_divmod_small(A, B, n):
    A = _poly_trim([x % n for x in A])
    B = _poly_trim([x % n for x in B])
    if not B:
        raise ZeroDivisionError
    if len(A) < len(B):
        return [], A
    inv_lc = inv_mod_n(B[-1], n)
    deg_diff = len(A) - len(B)
    Q = [0] * (deg_diff + 1)
    R = A[:]
    for i in range(deg_diff, -1, -1):
        if len(R) == i + len(B):
            coef = R[-1] * inv_lc % n
            Q[i] = coef
            if coef:
                for j in range(len(B)):
                    R[i + j] = (R[i + j] - coef * B[j]) % n
            R.pop()
            R = _poly_trim(R)
    return _poly_trim(Q), R


def _poly_extgcd_inv(a_canon, mod_poly, n):
    old_r, r = [x % n for x in mod_poly], _poly_trim([x % n for x in a_canon])
    old_t, t = [], [1]
    while r:
        q, rem = _poly_divmod_small(old_r, r, n)
        qt = [0] * (len(q) + len(t))
        for i, qi in enumerate(q):
            for j, tj in enumerate(t):
                qt[i + j] = (qt[i + j] + qi * tj) % n
        L = max(len(old_t), len(qt))
        new_t = [((old_t[i] if i < len(old_t) else 0) - (qt[i] if i < len(qt) else 0)) % n
                 for i in range(L)]
        old_r, r = r, rem
        old_t, t = t, _poly_trim(new_t)
    if len(old_r) != 1:
        for c in old_r:
            g = math.gcd(c, n)
            if 1 < g < n:
                raise FactorFound(g)
        raise ZeroDivisionError("poly not invertible")
    inv_c = inv_mod_n(old_r[0], n)
    deg = len(mod_poly) - 1
    return [(old_t[i] * inv_c) % n if i < len(old_t) else 0 for i in range(deg)]


def lock01_generate(K_bound=1 << 11, B=1 << 13, n_small=38, seed=None, verbose=True, decoy=False):
    if seed is not None:
        random.seed(seed)
    t0 = time.time()
    pool = [l for l in primes_upto(B) if l > (1 << 11) and l % 6 == 1 and l != 7]
    M_full = math.prod([l for l in primes_upto(B) if l % 6 == 1])

    while True:
        ls = random.sample(pool, n_small)
        L_smooth = math.prod(ls)
        if not (455 <= L_smooth.bit_length() <= 478):
            continue
        roots = []
        for l in ls:
            s = sqrt_mod(l - 3, l)
            r = (s + 1) * pow(2, -1, l) % l
            roots.append(r)
        r_all, M_all = _crt_combine(roots + [3, 1], ls + [7, 2])
        lo_p = 1 << 491
        k0 = (lo_p - r_all) // M_all
        p = None
        for k in range(k0, k0 + 250000):
            cand = r_all + k * M_all
            if cand.bit_length() == 492 and is_prime(cand):
                Phi6_cand = cand * cand - cand + 1
                G_cand = math.gcd(Phi6_cand, M_full)
                C6_cand = Phi6_cand // G_cand
                if C6_cand.bit_length() <= 516 and C6_cand % 2 == 1 and math.gcd(cand, C6_cand) == 1:
                    p = cand
                    Phi6 = Phi6_cand
                    C6 = C6_cand
                    break
        if p is not None:
            break

    # Optional false-hope 2-adic disguise: force N == 1 (mod 2^12). Off by default:
    # an honest N hits this with probability 2^-12, so it flags the key as built.
    mask_mod = 1 << 12 if decoy else 1
    while True:
        d1 = random.randrange(3, K_bound)
        if not is_prime(d1):
            continue
        d2 = random.randrange(3, K_bound)
        if d2 == d1 or not is_prime(d2):
            continue
        denom = (p * (d2 - 2 * d1)) % C6
        if math.gcd(denom, C6) != 1:
            continue
        # Projective Mobius Entanglement: d2 * (N - 3) == d1 * (2N + 5) (mod C6)
        r_q_c6 = (3 * d2 + 5 * d1) * pow(denom, -1, C6) % C6
        r_q_mask = pow(p, -1, mask_mod)
        r_q, step_q = _crt_combine([r_q_c6, r_q_mask], [C6, mask_mod])
        lo_q = (1 << 1023) // p + 1
        hi_q = ((1 << 1024) - 1) // p
        # Random start inside [lo_q, hi_q]; starting at lo_q made N ~ 2^1023 (top bits 100..0).
        m_lo = max(1, (lo_q - r_q) // step_q)
        m0 = random.randint(m_lo, max(m_lo, (hi_q - r_q) // step_q - 5000))
        q = None
        for m in range(m0, m0 + 5000):
            cand_q = r_q + m * step_q
            if lo_q <= cand_q <= hi_q and cand_q != p and is_prime(cand_q):
                q = cand_q
                break
        if q is not None:
            break

    N = p * q
    assert N.bit_length() == 1024
    assert (N - 1) % mask_mod == 0
    assert (d2 * M_full * (N - 3) - d1 * M_full * (2 * N + 5)) % Phi6 == 0
    if verbose:
        print("  [Lock 01 KeyGen] %.2fs | p=%db q=%db N=%db | C6=%db | Mobius(N-3,2N+5) | d1=%d d2=%d" %
              (time.time() - t0, p.bit_length(), q.bit_length(), N.bit_length(),
               C6.bit_length(), d1, d2))
    pub = {"N": N, "e": 65537}
    sk = {"p": p, "q": q, "d1": d1, "d2": d2, "Phi6": Phi6, "C6": C6}
    # Search bounds are solver knowledge, not part of the public surface.
    sk["params"] = {"K_bound": K_bound, "B": B}
    return pub, sk


def lock01_solve(pub, verbose=True, K_bound=1 << 11, B=1 << 13):
    N = int(pub["N"])
    t0 = time.time()

    M = math.prod([l for l in primes_upto(B) if l % 6 == 1])
    mod_phi7 = [1, 1, 1, 1, 1, 1, 1]

    try:
        beta = [2, 1, 0, 0, 0, 0, 0]
        num = _a7_mul(_a7_frob(beta, 4), _a7_frob(beta, 3), N)
        den = _a7_mul(_a7_frob(beta, 1), beta, N)
        den_inv_6 = _poly_extgcd_inv(_a7_canon(den, N), mod_phi7, N)
        tau = _a7_mul(num, den_inv_6 + [0], N)

        Q0 = _a7_pow(tau, M, N)
        Q_L = _a7_pow(Q0, N - 3, N)
        Q_R = _a7_pow(Q0, 2 * N + 5, N)

        lhs, cur = [], [1, 0, 0, 0, 0, 0, 0]
        for d2 in range(1, K_bound):
            cur = _a7_mul(cur, Q_L, N)
            if is_prime(d2):
                lhs.append(_a7_canon(cur, N)[0])

        rhs, cur = [], [1, 0, 0, 0, 0, 0, 0]
        for d1 in range(1, K_bound):
            cur = _a7_mul(cur, Q_R, N)
            if is_prime(d1):
                rhs.append(_a7_canon(cur, N)[0])

        g = batch_poly_gcd(lhs, rhs, N)
        if g and 1 < g < N:
            if verbose:
                print("  [Lock 01 Solve]  %.2fs | Phi_6(p) T_6 Mobius torus collision hit (%dx%d)" %
                      (time.time() - t0, len(lhs), len(rhs)))
            return g, N // g
    except FactorFound as ff:
        g = math.gcd(ff.p, N)
        if 1 < g < N:
            return g, N // g
    return None


# ======================================================================
# LOCK 02: Phi_4(p) = p^2 + 1 Projective Redei Conic over Z_N[i]
#          + Fake Continued-Fraction Convergent Disguise (ECF Honey-Trap)
# ======================================================================

def _r2_mul(a, b, n):
    return ((a[0] * b[0] - a[1] * b[1]) % n, (a[0] * b[1] + a[1] * b[0]) % n)


def _r2_add(a, b, n):
    return ((a[0] + b[0]) % n, (a[1] + b[1]) % n)


def _redei2_mul(P, Q, delta, n):
    U1, V1 = P
    U2, V2 = Q
    u1u2 = _r2_mul(U1, U2, n)
    v1v2 = _r2_mul(V1, V2, n)
    dv = _r2_mul(delta, v1v2, n)
    U3 = _r2_add(u1u2, dv, n)
    U1V2 = _r2_mul(U1, V2, n)
    V1U2 = _r2_mul(V1, U2, n)
    V3 = _r2_add(U1V2, V1U2, n)
    return (U3, V3)


def _redei2_pow(P, k, delta, n):
    res = ((1, 0), (0, 0))
    base = P
    while k > 0:
        if k & 1:
            res = _redei2_mul(res, base, delta, n)
        base = _redei2_mul(base, base, delta, n)
        k >>= 1
    return res


def lock02_generate(K_bound=1 << 11, B=1 << 13, n_small=35, seed=None, verbose=True, decoy=False):
    if seed is not None:
        random.seed(seed)
    t0 = time.time()
    pool = [l for l in primes_upto(B) if l > (1 << 11) and l % 4 == 1 and l != 5]
    M_full = 2 * math.prod([l for l in primes_upto(B) if l % 4 == 1])

    while True:
        ls = random.sample(pool, n_small)
        L_smooth = math.prod(ls)
        if not (435 <= L_smooth.bit_length() <= 475):
            continue
        roots = [sqrt_mod(l - 1, l) for l in ls]
        r_all, M_all = _crt_combine(roots + [7], ls + [20])
        lo_p = (1 << 511) + (1 << 510)
        k0 = (lo_p - r_all) // M_all
        p = None
        for k in range(k0, k0 + 250000):
            cand = r_all + k * M_all
            if cand.bit_length() == 512 and is_prime(cand):
                p = cand
                break
        if p is None:
            continue
        Phi4 = p * p + 1
        G = math.gcd(Phi4, M_full)
        C4 = Phi4 // G
        if 540 <= C4.bit_length() <= 585:
            break

    while True:
        q = random.getrandbits(512) | (1 << 511) | (1 << 510) | 1
        if q != p and (p * q).bit_length() == 1024 and is_prime(q):
            break
    N = p * q
    phi_N = (p - 1) * (q - 1)

    # Plant a Legendre Continued-Fraction Ghost Convergent k_fake / d_fake in e / N
    d_fake = random.getrandbits(196) | (1 << 195) | 1
    while not is_prime(d_fake):
        d_fake += 2
    k_fake = random.randrange(1 << 194, d_fake)
    while math.gcd(k_fake, d_fake) != 1:
        k_fake += 1
    # Without the decoy, aim e at a uniform point instead of the planted convergent.
    E_target = (k_fake * N) // d_fake if decoy else random.randrange(N // 2, N)

    while True:
        d1 = random.randrange(3, K_bound)
        if not is_prime(d1):
            continue
        d2 = random.randrange(3, K_bound)
        if d2 == d1 or not is_prime(d2):
            continue
        denom = (d2 - 2 * d1) % C4
        if math.gcd(denom, C4) != 1:
            continue
        # Twisted Bilinear Entanglement: d2 * (e + 3N) == d1 * (2e + 5N) (mod C4)
        e_r = (5 * d1 - 3 * d2) * N % C4 * pow(denom, -1, C4) % C4
        m_base = (E_target - e_r) // C4
        e = None
        for offset in range(0, 500):
            cand_e = e_r + (m_base + offset) * C4
            if 1 < cand_e < N and math.gcd(cand_e, phi_N) == 1:
                e = cand_e
                break
        if e is None:
            continue
        # Next partial quotient after k_fake/d_fake is ~ N / (d_fake * |e*d_fake - k_fake*N|);
        # require 2^52 so the advertised 2^50 spike holds with margin on every seed.
        err = abs(e * d_fake - k_fake * N)
        if not decoy or (err and N // (d_fake * err) >= 1 << 52):
            break

    assert N.bit_length() == 1024 and 1 < e < N
    assert not decoy or abs(e * d_fake - k_fake * N) * (2 * d_fake) < N
    assert (d2 * M_full * (e + 3 * N) - d1 * M_full * (2 * e + 5 * N)) % Phi4 == 0
    if verbose:
        print("  [Lock 02 KeyGen] %.2fs | p=%db q=%db N=%db | e=%db (ECF Ghost d_fake=%db) | d1=%d d2=%d" %
              (time.time() - t0, p.bit_length(), q.bit_length(), N.bit_length(),
               e.bit_length(), d_fake.bit_length(), d1, d2))
    pub = {"N": N, "e": e}
    sk = {"p": p, "q": q, "d1": d1, "d2": d2, "Phi4": Phi4, "C4": C4,
          "d_fake": d_fake, "k_fake": k_fake}
    # Search bounds are solver knowledge, not part of the public surface.
    sk["params"] = {"K_bound": K_bound, "B": B}
    return pub, sk


def lock02_solve(pub, verbose=True, K_bound=1 << 11, B=1 << 13):
    N = int(pub["N"])
    e = int(pub["e"])
    t0 = time.time()

    M = 2 * math.prod([l for l in primes_upto(B) if l % 4 == 1])
    delta = (1, 2)
    P0 = ((2, 1), (1, 0))

    try:
        Q_L = _redei2_pow(P0, M * (e + 3 * N), delta, N)
        Q_R = _redei2_pow(P0, M * (2 * e + 5 * N), delta, N)

        pts_L, cur = [], ((1, 0), (0, 0))
        for d2 in range(1, K_bound):
            cur = _redei2_mul(cur, Q_L, delta, N)
            if is_prime(d2):
                pts_L.append(cur)

        pts_R, cur = [], ((1, 0), (0, 0))
        for d1 in range(1, K_bound):
            cur = _redei2_mul(cur, Q_R, delta, N)
            if is_prime(d1):
                pts_R.append(cur)

        all_pts = pts_L + pts_R
        norms = [(V[0] * V[0] + V[1] * V[1]) % N for (_, V) in all_pts]
        inv_norms = _batch_inv_mod_n(norms, N)

        scalars = []
        for ((u0, u1), (v0, v1)), inv_nm in zip(all_pts, inv_norms):
            scalars.append((u0 * v0 + u1 * v1) % N * inv_nm % N)

        kL = len(pts_L)
        lhs, rhs = scalars[:kL], scalars[kL:]
        g = batch_poly_gcd(lhs, rhs, N)
        if g and 1 < g < N:
            if verbose:
                print("  [Lock 02 Solve]  %.2fs | Phi_4(p) Redei conic collision hit (%dx%d)" %
                      (time.time() - t0, len(lhs), len(rhs)))
            return g, N // g
    except FactorFound as ff:
        g = math.gcd(ff.p, N)
        if 1 < g < N:
            return g, N // g
    return None


# ======================================================================
# LOCK 03: Phi_8(p) = p^4 + 1 Octic Cyclotomic Torus P^1(R_4)
#          + Smooth (e - 1) Subgroup Decoy
# ======================================================================

def _r4_mul(a, b, n):
    c0 = a[0]*b[0]
    c1 = a[0]*b[1] + a[1]*b[0]
    c2 = a[0]*b[2] + a[1]*b[1] + a[2]*b[0]
    c3 = a[0]*b[3] + a[1]*b[2] + a[2]*b[1] + a[3]*b[0]
    c4 = a[1]*b[3] + a[2]*b[2] + a[3]*b[1]
    c5 = a[2]*b[3] + a[3]*b[2]
    c6 = a[3]*b[3]
    r0 = (c0 - 5 * c4 - 10 * c6) % n
    r1 = (c1 - 5 * c5) % n
    r2 = (c2 + 2 * c4 - c6) % n
    r3 = (c3 + 2 * c5) % n
    return (r0, r1, r2, r3)


def _r4_add(a, b, n):
    return ((a[0] + b[0]) % n, (a[1] + b[1]) % n, (a[2] + b[2]) % n, (a[3] + b[3]) % n)


def _redei4_mul(P, Q, n):
    U1, V1 = P
    U2, V2 = Q
    u1u2 = _r4_mul(U1, U2, n)
    v1v2 = _r4_mul(V1, V2, n)
    tv = ((-5 * v1v2[3]) % n, v1v2[0], (v1v2[1] + 2 * v1v2[3]) % n, v1v2[2])
    U3 = _r4_add(u1u2, tv, n)
    V3 = _r4_add(_r4_mul(U1, V2, n), _r4_mul(V1, U2, n), n)
    return (U3, V3)


def _redei4_pow(P, k, n):
    res = ((1, 0, 0, 0), (0, 0, 0, 0))
    base = P
    while k > 0:
        if k & 1:
            res = _redei4_mul(res, base, n)
        base = _redei4_mul(base, base, n)
        k >>= 1
    return res


def _r4_norm_conj(v, n):
    a0 = (v[0] * v[0] - 5 * v[2] * v[2]) % n
    a1 = (2 * v[0] * v[2] + 2 * v[2] * v[2]) % n
    b0 = (v[1] * v[1] - 5 * v[3] * v[3]) % n
    b1 = (2 * v[1] * v[3] + 2 * v[3] * v[3]) % n
    d0 = (a0 + 5 * b1) % n
    d1 = (a1 - b0 - 2 * b1) % n
    norm_Z = (d0 * d0 + 2 * d0 * d1 + 5 * d1 * d1) % n
    v_neg = (v[0], (-v[1]) % n, v[2], (-v[3]) % n)
    d_bar = ((d0 + 2 * d1) % n, 0, (-d1) % n, 0)
    v_adj = _r4_mul(v_neg, d_bar, n)
    return norm_Z, v_adj


def lock03_generate(K_bound=1 << 11, B=1 << 13, n_small=25, seed=None, verbose=True):
    if seed is not None:
        random.seed(seed)
    t0 = time.time()
    pool = [l for l in primes_upto(B) if l > (1 << 11) and l % 8 == 1]
    M_full = 2 * math.prod([l for l in primes_upto(B) if l % 8 == 1])

    while True:
        ls = random.sample(pool, n_small)
        L_smooth = math.prod(ls)
        if not (310 <= L_smooth.bit_length() <= 322):
            continue
        roots = []
        for l in ls:
            s = sqrt_mod(l - 1, l)
            r = sqrt_mod(s, l)
            if r is None:
                r = sqrt_mod(l - s, l)
            assert pow(r, 4, l) == l - 1
            roots.append(r)
        r_all, M_all = _crt_combine(roots + [7], ls + [20])
        lo_p = 1 << 331
        k0 = (lo_p - r_all) // M_all
        p = None
        for k in range(k0, k0 + 250000):
            cand = r_all + k * M_all
            if cand.bit_length() == 332 and is_prime(cand):
                Phi8_cand = pow(cand, 4) + 1
                G_cand = math.gcd(Phi8_cand, M_full)
                C8_cand = Phi8_cand // G_cand
                if C8_cand.bit_length() <= 1018:
                    p = cand
                    Phi8 = Phi8_cand
                    C8 = C8_cand
                    break
        if p is not None:
            break

    lo_q = (1 << 1023) // p + 1
    hi_q = ((1 << 1024) - 1) // p
    while True:
        q = random.randrange(lo_q, hi_q) | 1
        if q != p and (p * q).bit_length() == 1024 and is_prime(q):
            break
    N = p * q
    phi_N = (p - 1) * (q - 1)

    while True:
        d1 = random.randrange(3, K_bound)
        if not is_prime(d1):
            continue
        d2 = random.randrange(3, K_bound)
        if d2 == d1 or not is_prime(d2):
            continue
        denom = (d2 - 3 * d1) % C8
        if math.gcd(denom, C8) != 1:
            continue
        # Octic Shifted Entanglement: d2 * (e + 7N) == d1 * (3e + 11N) (mod C8)
        e_r = (11 * d1 - 7 * d2) * N % C8 * pow(denom, -1, C8) % C8
        e = _lift_exponent(e_r, C8, N, phi_N)
        if e is not None:
            break

    assert N.bit_length() == 1024 and 1 < e < N
    assert (d2 * M_full * (e + 7 * N) - d1 * M_full * (3 * e + 11 * N)) % Phi8 == 0
    if verbose:
        print("  [Lock 03 KeyGen] %.2fs | p=%db q=%db N=%db | e=%db (<N) | d1=%d d2=%d" %
              (time.time() - t0, p.bit_length(), q.bit_length(), N.bit_length(),
               e.bit_length(), d1, d2))
    pub = {"N": N, "e": e}
    sk = {"p": p, "q": q, "d1": d1, "d2": d2, "Phi8": Phi8, "C8": C8}
    # Search bounds are solver knowledge, not part of the public surface.
    sk["params"] = {"K_bound": K_bound, "B": B}
    return pub, sk


def lock03_solve(pub, verbose=True, K_bound=1 << 11, B=1 << 13):
    N = int(pub["N"])
    e = int(pub["e"])
    t0 = time.time()

    M = 2 * math.prod([l for l in primes_upto(B) if l % 8 == 1])
    P0 = ((2, 1, 0, 0), (1, 0, 0, 0))

    try:
        Q_L = _redei4_pow(P0, M * (e + 7 * N), N)
        Q_R = _redei4_pow(P0, M * (3 * e + 11 * N), N)

        pts_L, cur = [], ((1, 0, 0, 0), (0, 0, 0, 0))
        for d2 in range(1, K_bound):
            cur = _redei4_mul(cur, Q_L, N)
            if is_prime(d2):
                pts_L.append(cur)

        pts_R, cur = [], ((1, 0, 0, 0), (0, 0, 0, 0))
        for d1 in range(1, K_bound):
            cur = _redei4_mul(cur, Q_R, N)
            if is_prime(d1):
                pts_R.append(cur)

        all_pts = pts_L + pts_R
        norms, adjs = [], []
        for _, V in all_pts:
            nm, adj = _r4_norm_conj(V, N)
            norms.append(nm)
            adjs.append(adj)
        inv_norms = _batch_inv_mod_n(norms, N)

        scalars = []
        for (U, _), adj, inv_nm in zip(all_pts, adjs, inv_norms):
            prod0 = _r4_mul(U, adj, N)[0]
            scalars.append(prod0 * inv_nm % N)

        kL = len(pts_L)
        lhs, rhs = scalars[:kL], scalars[kL:]
        g = batch_poly_gcd(lhs, rhs, N)
        if g and 1 < g < N:
            if verbose:
                print("  [Lock 03 Solve]  %.2fs | Phi_8(p) octic torus collision hit (%dx%d)" %
                      (time.time() - t0, len(lhs), len(rhs)))
            return g, N // g
    except FactorFound as ff:
        g = math.gcd(ff.p, N)
        if 1 < g < N:
            return g, N // g
    return None


# ======================================================================
# LOCK 04: Non-Maximal Order Conductor f=2 CM Curve (D = -7, j = -3375)
#          + Fake ROCA Primorial Discrete-Log Signature Disguise
# ======================================================================

ROCA_DECOY_MOD = math.prod([3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37])


def lock04_generate(K_bound=1 << 11, B=1 << 13, n_small=18, seed=None, verbose=True, decoy=False):
    if seed is not None:
        random.seed(seed)
    t0 = time.time()
    roca_mod = ROCA_DECOY_MOD if decoy else 1
    pool = [l for l in primes_upto(B) if l > (1 << 11) and pow(l - 7, (l - 1) // 2, l) == 1]
    M_smooth = (1 << 16) * math.prod([l for l in primes_upto(B) if l == 7 or (l > 2 and pow(l - 7, (l - 1) // 2, l) == 1)])

    while True:
        ls = random.sample(pool, n_small)
        L_smooth = math.prod(ls)
        if not (220 <= L_smooth.bit_length() <= 232):
            continue
        v = (random.getrandbits(251) | (1 << 250)) & ~1
        roots = []
        for l in ls:
            s7 = sqrt_mod(l - 7, l)
            roots.append((1 + s7 * (v % l)) % l)
        r_u, M_u = _crt_combine(roots + [1], ls + [2])
        # Random start with u^2 in [2^511, 2^512): p = u^2 + 7v^2 is 512-bit and its top
        # bits are not pinned (starting at the minimum gave p ~ 2^511, N ~ 2^1023).
        lo_u = random.randrange(math.isqrt(1 << 511) + 1, (1 << 256) - (1 << 252))
        k0 = (lo_u - r_u) // M_u
        p = None
        for k in range(k0, k0 + 250000):
            u = r_u + k * M_u
            cand_p = u * u + 7 * v * v
            if cand_p.bit_length() != 512 or not is_prime(cand_p):
                continue
            M_p_cand = cand_p + 1 - 2 * u
            hit_twist = False
            for u0 in range(1, 6):
                w = (u0 ** 3 - 35 * u0 - 98) % cand_p
                a_curve = (-35 * w * w) % cand_p
                P0 = ((u0 * w) % cand_p, (w * w) % cand_p)
                if ec_mul(M_p_cand, P0, a_curve, cand_p) is None:
                    hit_twist = True
                    break
            if hit_twist:
                p = cand_p
                M_p = M_p_cand
                break
        if p is None:
            continue
        G = math.gcd(M_p, M_smooth)
        C_7 = M_p // G
        while C_7 % 2 == 0:
            C_7 //= 2
        if math.gcd(C_7, roca_mod) == 1:
            break

    while True:
        d1 = random.randrange(3, K_bound)
        if not is_prime(d1):
            continue
        d2 = random.randrange(3, K_bound)
        if d2 == d1 or not is_prime(d2):
            continue
        denom = (p * (d2 - 2 * d1)) % C_7
        if math.gcd(denom, C_7) != 1:
            continue
        # Projective Mobius CM Entanglement: d2 * (N - 2) == d1 * (2N + 3) (mod C_7)
        r_q_cm = (2 * d2 + 3 * d1) * pow(denom, -1, C_7) % C_7
        # Fake ROCA Primorial Disguise: N = p*q == 65537^1337 (mod ROCA_DECOY_MOD)
        r_q_roca = pow(65537, 1337, roca_mod) * pow(p, -1, roca_mod) % roca_mod
        r_q, step_q = _crt_combine([r_q_cm, r_q_roca, 1], [C_7, roca_mod, 2])
        lo_q = (1 << 1023) // p + 1
        hi_q = ((1 << 1024) - 1) // p
        # Random start inside [lo_q, hi_q]; starting at lo_q made N ~ 2^1023 (top bits 100..0).
        m_lo = max(1, (lo_q - r_q) // step_q)
        m0 = random.randint(m_lo, max(m_lo, (hi_q - r_q) // step_q - 5000))
        q = None
        for m in range(m0, m0 + 5000):
            cand = r_q + m * step_q
            if lo_q <= cand <= hi_q and cand != p and is_prime(cand):
                q = cand
                break
        if q is not None:
            break

    N = p * q
    assert N.bit_length() == 1024
    assert (N - pow(65537, 1337, roca_mod)) % roca_mod == 0
    assert (d2 * M_smooth * (N - 2) - d1 * M_smooth * (2 * N + 3)) % M_p == 0
    if verbose:
        print("  [Lock 04 KeyGen] %.2fs | p=%db q=%db N=%db | j=-3375 C_{-7}=%db (Fake ROCA mod P_37) | d1=%d d2=%d" %
              (time.time() - t0, p.bit_length(), q.bit_length(), N.bit_length(),
               C_7.bit_length(), d1, d2))
    pub = {"N": N, "e": 65537}
    sk = {"p": p, "q": q, "M_p": M_p, "C_7": C_7, "d1": d1, "d2": d2}
    # Search bounds are solver knowledge, not part of the public surface.
    sk["params"] = {"K_bound": K_bound, "B": B}
    return pub, sk


def lock04_solve(pub, verbose=True, K_bound=1 << 11, B=1 << 13):
    N = int(pub["N"])
    t0 = time.time()

    M_smooth = (1 << 16) * math.prod([l for l in primes_upto(B) if l == 7 or (l > 2 and pow(l - 7, (l - 1) // 2, l) == 1)])
    scalar_L = M_smooth * (N - 2)
    scalar_R = M_smooth * (2 * N + 3)

    for u0 in range(1, 6):
        w = (u0 ** 3 - 35 * u0 - 98) % N
        if w == 0 or math.gcd(w, N) != 1:
            continue
        a_curve = (-35 * w * w) % N
        x0 = (u0 * w) % N
        y0 = (w * w) % N
        P0 = (x0, y0)
        try:
            Q_L = ec_mul(scalar_L, P0, a_curve, N)
            Q_R = ec_mul(scalar_R, P0, a_curve, N)
            if Q_L is None or Q_R is None:
                continue
            lhs, cur = [], None
            for d2 in range(1, K_bound):
                cur = ec_add(cur, Q_L, a_curve, N)
                if cur is None:
                    break
                if is_prime(d2):
                    lhs.append(cur[0])
            rhs, cur = [], None
            for d1 in range(1, K_bound):
                cur = ec_add(cur, Q_R, a_curve, N)
                if cur is None:
                    break
                if is_prime(d1):
                    rhs.append(cur[0])
            g = batch_poly_gcd(lhs, rhs, N)
            if g and 1 < g < N:
                if verbose:
                    print("  [Lock 04 Solve]  %.2fs | D=-7 (j=-3375) Mobius CM hit on u0=%d (%dx%d)" %
                          (time.time() - t0, u0, len(lhs), len(rhs)))
                return g, N // g
        except FactorFound as ff:
            g = math.gcd(ff.p, N)
            if 1 < g < N:
                return g, N // g
        except ZeroDivisionError:
            continue
    return None


# ======================================================================
# LOCK 05: Genus-2 Hyperelliptic Curve Jacobian Jac(C)(Z/NZ)
#          + Fake Masked Low-Exponent (e == 3 mod 2^80) Disguise
# ======================================================================

def _p_add(A, B, n):
    L = max(len(A), len(B))
    return _poly_trim([((A[i] if i < len(A) else 0) + (B[i] if i < len(B) else 0)) % n
                       for i in range(L)])


def _p_sub(A, B, n):
    L = max(len(A), len(B))
    return _poly_trim([((A[i] if i < len(A) else 0) - (B[i] if i < len(B) else 0)) % n
                       for i in range(L)])


def _p_mul_small(A, B, n):
    if not A or not B:
        return []
    res = [0] * (len(A) + len(B) - 1)
    for i, a in enumerate(A):
        if a:
            for j, b in enumerate(B):
                res[i + j] = (res[i + j] + a * b) % n
    return _poly_trim(res)


def _p_extgcd(A, B, n):
    old_r, r = _poly_trim(A), _poly_trim(B)
    old_s, s = [1], []
    old_t, t = [], [1]
    while r:
        q, rem = _poly_divmod_small(old_r, r, n)
        old_r, r = r, rem
        old_s, s = s, _p_sub(old_s, _p_mul_small(q, s, n), n)
        old_t, t = t, _p_sub(old_t, _p_mul_small(q, t, n), n)
    if not old_r:
        return [], [], []
    inv_lc = inv_mod_n(old_r[-1], n)
    d = [c * inv_lc % n for c in old_r]
    s_out = [c * inv_lc % n for c in old_s]
    t_out = [c * inv_lc % n for c in old_t]
    return d, s_out, t_out


def cantor_add(D1, D2, f_curve, n):
    u1, v1 = D1
    u2, v2 = D2
    if len(u1) == 1:
        return D2
    if len(u2) == 1:
        return D1
    d1, e1, e2 = _p_extgcd(u1, u2, n)
    v_sum = _p_add(v1, v2, n)
    if not v_sum:
        d, c1, c2 = d1, [1], []
    else:
        d, c1, c2 = _p_extgcd(d1, v_sum, n)
    s1 = _p_mul_small(c1, e1, n)
    s2 = _p_mul_small(c1, e2, n)
    s3 = c2
    d_sq = _p_mul_small(d, d, n)
    u_prod = _p_mul_small(u1, u2, n)
    u, _ = _poly_divmod_small(u_prod, d_sq, n)
    t1 = _p_mul_small(_p_mul_small(s1, u1, n), v2, n)
    t2 = _p_mul_small(_p_mul_small(s2, u2, n), v1, n)
    t3 = _p_mul_small(s3, _p_add(_p_mul_small(v1, v2, n), f_curve, n), n)
    v_num = _p_add(_p_add(t1, t2, n), t3, n)
    v_quo, _ = _poly_divmod_small(v_num, d, n)
    _, v = _poly_divmod_small(v_quo, u, n)
    while len(u) - 1 > 2:
        f_minus_v2 = _p_sub(f_curve, _p_mul_small(v, v, n), n)
        u_next, _ = _poly_divmod_small(f_minus_v2, u, n)
        if not u_next:
            return ([1], [])
        inv_lc = inv_mod_n(u_next[-1], n)
        u = [c * inv_lc % n for c in u_next]
        neg_v = [(-c) % n for c in v]
        _, v = _poly_divmod_small(neg_v, u, n)
    inv_lc = inv_mod_n(u[-1], n)
    u = [c * inv_lc % n for c in u]
    return (u, v)


def cantor_mul(k, D, f_curve, n):
    res = ([1], [])
    base = D
    while k > 0:
        if k & 1:
            res = cantor_add(res, base, f_curve, n)
        base = cantor_add(base, base, f_curve, n)
        k >>= 1
    return res


def _mumford_disc_inv(u, n):
    u0 = u[0] if len(u) > 0 else 0
    u1 = u[1] if len(u) > 1 else 0
    return (u1 * u1 - 4 * u0) % n


def lock05_generate(K_bound=1 << 11, B=1 << 13, n_small=34, seed=None, verbose=True, decoy=False):
    if seed is not None:
        random.seed(seed)
    t0 = time.time()
    pool = [l for l in primes_upto(B) if l > (1 << 11) and l % 4 == 1 and l != 5]
    M_full = 2 * math.prod([l for l in primes_upto(B) if l % 4 == 1])

    while True:
        ls = random.sample(pool, n_small)
        L_smooth = math.prod(ls)
        if not (425 <= L_smooth.bit_length() <= 470):
            continue
        roots = [sqrt_mod(l - 1, l) for l in ls]
        r_all, M_all = _crt_combine(roots + [7], ls + [20])
        lo_p = (1 << 511) + (1 << 510)
        k0 = (lo_p - r_all) // M_all
        p = None
        for k in range(k0, k0 + 250000):
            cand = r_all + k * M_all
            if cand.bit_length() == 512 and is_prime(cand):
                p = cand
                break
        if p is None:
            continue
        J_ord = p * p + 1
        G = math.gcd(J_ord, M_full)
        C_jac = J_ord // G
        if 540 <= C_jac.bit_length() <= 585 and C_jac % 2 == 1:
            break

    while True:
        q = random.getrandbits(512) | (1 << 511) | (1 << 510) | 1
        if q != p and (p * q).bit_length() == 1024 and is_prime(q):
            break
    N = p * q
    phi_N = (p - 1) * (q - 1)

    mask80 = 1 << 80 if decoy else 1
    while True:
        d1 = random.randrange(3, K_bound)
        if not is_prime(d1):
            continue
        d2 = random.randrange(3, K_bound)
        if d2 == d1 or not is_prime(d2):
            continue
        denom = (d2 - 2 * d1) % C_jac
        if math.gcd(denom, C_jac) != 1:
            continue
        # Quadratic Self-Referential Jacobian Entanglement: d2*(e + N^2) == d1*(2e + N) (mod C_jac)
        e_jac = (d1 * N - d2 * N * N) % C_jac * pow(denom, -1, C_jac) % C_jac
        # Plant Fake Low-Exponent Mask: e == 3 (mod 2^80)
        e_r, step_e = _crt_combine([e_jac, 3 % mask80], [C_jac, mask80])
        e = _lift_exponent(e_r, step_e, N, phi_N)
        if e is not None:
            break

    assert N.bit_length() == 1024 and 1 < e < N
    assert e % mask80 == 3 % mask80
    assert (d2 * M_full * (e + N * N) - d1 * M_full * (2 * e + N)) % J_ord == 0
    if verbose:
        print("  [Lock 05 KeyGen] %.2fs | p=%db q=%db N=%db | e=%db (e==3 mod 2^80 decoy) | d1=%d d2=%d" %
              (time.time() - t0, p.bit_length(), q.bit_length(), N.bit_length(),
               e.bit_length(), d1, d2))
    pub = {"N": N, "e": e}
    sk = {"p": p, "q": q, "d1": d1, "d2": d2, "J_ord": J_ord, "C_jac": C_jac}
    # Search bounds are solver knowledge, not part of the public surface.
    sk["params"] = {"K_bound": K_bound, "B": B}
    return pub, sk


def lock05_solve(pub, verbose=True, K_bound=1 << 11, B=1 << 13):
    N = int(pub["N"])
    e = int(pub["e"])
    t0 = time.time()

    M = 2 * math.prod([l for l in primes_upto(B) if l % 4 == 1])
    f_curve = [8, 0, 0, 0, 0, 1]
    D0 = ([(-1) % N, 1], [3])

    try:
        D_L = cantor_mul(M * (e + N * N), D0, f_curve, N)
        D_R = cantor_mul(M * (2 * e + N), D0, f_curve, N)

        lhs, cur = [], ([1], [])
        for d2 in range(1, K_bound):
            cur = cantor_add(cur, D_L, f_curve, N)
            if is_prime(d2):
                lhs.append(_mumford_disc_inv(cur[0], N))

        rhs, cur = [], ([1], [])
        for d1 in range(1, K_bound):
            cur = cantor_add(cur, D_R, f_curve, N)
            if is_prime(d1):
                rhs.append(_mumford_disc_inv(cur[0], N))

        g = batch_poly_gcd(lhs, rhs, N)
        if g and 1 < g < N:
            if verbose:
                print("  [Lock 05 Solve]  %.2fs | Genus-2 Cantor Mumford-Disc collision hit (%dx%d)" %
                      (time.time() - t0, len(lhs), len(rhs)))
            return g, N // g
    except FactorFound as ff:
        g = math.gcd(ff.p, N)
        if 1 < g < N:
            if verbose:
                print("  [Lock 05 Solve]  %.2fs | Genus-2 Cantor division captured factor directly" %
                      (time.time() - t0))
            return g, N // g
    return None

