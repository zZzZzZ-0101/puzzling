"""
locks_B.py — Pluggable Algebraic Trapdoor Locks 06 to 10
========================================================
Each lock implements the uniform pluggable interface:
  - generate(K_bound=..., seed=..., verbose=...) -> (pub_dict, sk_dict)
  - solve(pub_dict, verbose=...)                 -> (p, q)
"""
import math, random, time
from trapdoor.ctflib import (
    is_prime, primes_upto, sqrt_mod, inv_mod_n, FactorFound,
    batch_poly_gcd, lll
)
from trapdoor.arsenal.locks_A import _crt_combine, _poly_extgcd_inv, _poly_divmod_small, _poly_trim


# ======================================================================
# LOCK 06: 12D Non-Commutative Quaternion Algebra H_{-1,-1}(R_3)
# ======================================================================

def _r3_mul(a, b, c_twist, n):
    d0 = a[0] * b[0] + c_twist * (a[1] * b[2] + a[2] * b[1])
    d1 = a[0] * b[1] + a[1] * b[0] + c_twist * a[2] * b[2]
    d2 = a[0] * b[2] + a[1] * b[1] + a[2] * b[0]
    return (d0 % n, d1 % n, d2 % n)


def _r3_add(a, b, n):
    return ((a[0] + b[0]) % n, (a[1] + b[1]) % n, (a[2] + b[2]) % n)


def _r3_sub(a, b, n):
    return ((a[0] - b[0]) % n, (a[1] - b[1]) % n, (a[2] - b[2]) % n)


def _q12_mul(Q1, Q2, c_twist, n):
    w1, x1, y1, z1 = Q1
    w2, x2, y2, z2 = Q2
    w = _r3_sub(
        _r3_sub(_r3_sub(_r3_mul(w1, w2, c_twist, n), _r3_mul(x1, x2, c_twist, n), n),
                _r3_mul(y1, y2, c_twist, n), n),
        _r3_mul(z1, z2, c_twist, n), n
    )
    x = _r3_sub(
        _r3_add(_r3_add(_r3_mul(w1, x2, c_twist, n), _r3_mul(x1, w2, c_twist, n), n),
                _r3_mul(y1, z2, c_twist, n), n),
        _r3_mul(z1, y2, c_twist, n), n
    )
    y = _r3_add(
        _r3_add(_r3_sub(_r3_mul(w1, y2, c_twist, n), _r3_mul(x1, z2, c_twist, n), n),
                _r3_mul(y1, w2, c_twist, n), n),
        _r3_mul(z1, x2, c_twist, n), n
    )
    z = _r3_add(
        _r3_sub(_r3_add(_r3_mul(w1, z2, c_twist, n), _r3_mul(x1, y2, c_twist, n), n),
                _r3_mul(y1, x2, c_twist, n), n),
        _r3_mul(z1, w2, c_twist, n), n
    )
    return (w, x, y, z)


def _q12_conj(Q, n):
    w, x, y, z = Q
    neg = lambda r: ((-r[0]) % n, (-r[1]) % n, (-r[2]) % n)
    return (w, neg(x), neg(y), neg(z))


def _q12_nrd(Q, c_twist, n):
    w, x, y, z = Q
    return _r3_add(
        _r3_add(_r3_mul(w, w, c_twist, n), _r3_mul(x, x, c_twist, n), n),
        _r3_add(_r3_mul(y, y, c_twist, n), _r3_mul(z, z, c_twist, n), n),
        n
    )


def _r3_inv(a, c_twist, n):
    x, y, z = a
    adj = (
        (x * x - c_twist * y * z) % n,
        (c_twist * z * z - x * y) % n,
        (y * y - x * z) % n
    )
    norm = (x ** 3 + c_twist * y ** 3 + c_twist * c_twist * z ** 3 - 3 * c_twist * x * y * z) % n
    inv_nm = inv_mod_n(norm, n)
    return (adj[0] * inv_nm % n, adj[1] * inv_nm % n, adj[2] * inv_nm % n)


def _q12_inv(Q, c_twist, n):
    nrd_inv = _r3_inv(_q12_nrd(Q, c_twist, n), c_twist, n)
    w, x, y, z = _q12_conj(Q, n)
    return (
        _r3_mul(w, nrd_inv, c_twist, n),
        _r3_mul(x, nrd_inv, c_twist, n),
        _r3_mul(y, nrd_inv, c_twist, n),
        _r3_mul(z, nrd_inv, c_twist, n),
    )


def _q12_pow(Q, k, c_twist, n):
    one = ((1, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0))
    res, base = one, Q
    while k > 0:
        if k & 1:
            res = _q12_mul(res, base, c_twist, n)
        base = _q12_mul(base, base, c_twist, n)
        k >>= 1
    return res


def lock06_generate(K_bound=1 << 11, B=1 << 13, n_small=34, seed=None, verbose=True):
    if seed is not None:
        random.seed(seed)
    t0 = time.time()
    pool = [l for l in primes_upto(B) if l > (1 << 11) and l % 6 == 1]
    M_full = math.prod([l for l in primes_upto(B) if l % 6 == 1])

    while True:
        ls = random.sample(pool, n_small)
        L_smooth = math.prod(ls)
        if not (425 <= L_smooth.bit_length() <= 470):
            continue
        roots = []
        for l in ls:
            s = sqrt_mod(l - 3, l)
            r = (s + 1) * pow(2, -1, l) % l
            roots.append(r)
        r_all, M_all = _crt_combine(roots + [3], ls + [4])
        lo_p = (1 << 511) + (1 << 510)
        k0 = (lo_p - r_all) // M_all
        p = None
        for k in range(k0, k0 + 300000):
            cand = r_all + k * M_all
            if cand.bit_length() != 512 or cand % 3 != 1:
                continue
            if not is_prime(cand):
                continue
            if pow(2, (cand - 1) // 3, cand) != 1:
                p = cand
                break
        if p is None:
            continue
        Phi6 = p * p - p + 1
        G = math.gcd(Phi6, M_full)
        C6 = Phi6 // G
        if 540 <= C6.bit_length() <= 585 and C6 % 2 == 1:
            break

    while True:
        q = random.getrandbits(512) | (1 << 511) | (1 << 510) | 1
        if q != p and (p * q).bit_length() == 1024 and is_prime(q):
            break
    N = p * q
    phi_N = (p - 1) * (q - 1)

    mask120 = 1 << 120
    while True:
        d1 = random.randrange(3, K_bound)
        if not is_prime(d1):
            continue
        d2 = random.randrange(3, K_bound)
        if d2 == d1 or not is_prime(d2):
            continue
        denom = (d2 - 3 * d1) % C6
        if math.gcd(denom, C6) != 1:
            continue
        # Quaternion Norm-Shifted Entanglement: d2*(e - 2N) == d1*(3e + 4N) (mod C6)
        e_c6 = (4 * d1 + 2 * d2) * N % C6 * pow(denom, -1, C6) % C6
        # Plant Fake 120-Bit LSB Partial-Key Exposure Disguise: e == N (mod 2^120)
        e_r, step_e = _crt_combine([e_c6, N % mask120], [C6, mask120])
        m_hi = (N - 1 - e_r) // step_e
        e = None
        for m in range(m_hi, max(1, m_hi - 500), -1):
            cand_e = e_r + m * step_e
            if 1 < cand_e < N and math.gcd(cand_e, phi_N) == 1:
                e = cand_e
                break
        if e is not None:
            break

    assert N.bit_length() == 1024 and 1 < e < N
    assert (e - N) % mask120 == 0
    assert (d2 * M_full * (e - 2 * N) - d1 * M_full * (3 * e + 4 * N)) % Phi6 == 0
    if verbose:
        print("  [Lock 06 KeyGen] %.2fs | p=%db q=%db N=%db | e=%db (120b LSB match decoy) | d1=%d d2=%d" %
              (time.time() - t0, p.bit_length(), q.bit_length(), N.bit_length(),
               e.bit_length(), d1, d2))
    pub = {"N": N, "e": e, "K_bound": K_bound, "B": B}
    sk = {"p": p, "q": q, "d1": d1, "d2": d2, "Phi6": Phi6, "C6": C6}
    return pub, sk


def lock06_solve(pub, verbose=True):
    N = int(pub["N"])
    e = int(pub["e"])
    K_bound = int(pub.get("K_bound", 1 << 11))
    B = int(pub.get("B", 1 << 13))
    t0 = time.time()
    c_twist = 2
    M = math.prod([l for l in primes_upto(B) if l % 6 == 1])

    try:
        alpha = ((1, 1, 0), (1, 0, 1), (0, 0, 0), (0, 0, 0))
        alpha_inv = _q12_inv(alpha, c_twist, N)
        beta = _q12_mul(_q12_conj(alpha, N), alpha_inv, c_twist, N)

        bw, bx, _, _ = beta
        u = ((bw[0], 0, 0), (bx[0], 0, 0), (0, 0, 0), (0, 0, 0))
        v = ((bw[1], 0, 0), (bx[1], 0, 0), (0, 0, 0), (0, 0, 0))
        z = ((bw[2], 0, 0), (bx[2], 0, 0), (0, 0, 0), (0, 0, 0))
        u3 = _q12_pow(u, 3, c_twist, N)
        v3 = _q12_pow(v, 3, c_twist, N)
        z3 = _q12_pow(z, 3, c_twist, N)
        uvz = _q12_mul(_q12_mul(u, v, c_twist, N), z, c_twist, N)
        scale_q = lambda Q, s: tuple(tuple(c * s % N for c in comp) for comp in Q)
        add_q = lambda A, B_: tuple(_r3_add(A[idx], B_[idx], N) for idx in range(4))
        sub_q = lambda A, B_: tuple(_r3_sub(A[idx], B_[idx], N) for idx in range(4))

        norm_6_2 = sub_q(
            add_q(add_q(u3, scale_q(v3, c_twist)), scale_q(z3, c_twist * c_twist)),
            scale_q(uvz, 3 * c_twist)
        )
        norm_6_2_inv = _q12_inv(norm_6_2, c_twist, N)
        beta3 = _q12_pow(beta, 3, c_twist, N)
        gamma = _q12_mul(beta3, norm_6_2_inv, c_twist, N)

        S = ((1, 0, 0), (0, 0, 0), (1, 0, 0), (0, 1, 0))
        S_inv = _q12_inv(S, c_twist, N)
        Q0 = _q12_mul(_q12_mul(S, gamma, c_twist, N), S_inv, c_twist, N)

        exp_L = M * (e - 2 * N)
        if exp_L < 0:
            Q0_base = _q12_inv(Q0, c_twist, N)
            Q_L = _q12_pow(Q0_base, -exp_L, c_twist, N)
        else:
            Q_L = _q12_pow(Q0, exp_L, c_twist, N)
        Q_R = _q12_pow(Q0, M * (3 * e + 4 * N), c_twist, N)

        one = ((1, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0))
        lhs, cur = [], one
        for d2 in range(1, K_bound):
            cur = _q12_mul(cur, Q_L, c_twist, N)
            if is_prime(d2):
                lhs.append((2 * cur[0][1] + 3 * cur[0][2]) % N)

        rhs, cur = [], one
        for d1 in range(1, K_bound):
            cur = _q12_mul(cur, Q_R, c_twist, N)
            if is_prime(d1):
                rhs.append((2 * cur[0][1] + 3 * cur[0][2]) % N)

        g = batch_poly_gcd(lhs, rhs, N)
        if g and 1 < g < N:
            if verbose:
                print("  [Lock 06 Solve]  %.2fs | 12D Quaternion reduced-trace collision hit (%dx%d)" %
                      (time.time() - t0, len(lhs), len(rhs)))
            return g, N // g
    except FactorFound as ff:
        g = math.gcd(ff.p, N)
        if 1 < g < N:
            return g, N // g
    return None


# ======================================================================
# LOCK 07: Prime-Order Companion Matrix Cubic Lucas Sequence V_n(P, Q)
#          + Twisted Bilinear Matrix Exponent & Dual-Trace Invariant
# ======================================================================

def _mat3_mul(A, B, n):
    return (
        (A[0]*B[0] + A[1]*B[3] + A[2]*B[6]) % n,
        (A[0]*B[1] + A[1]*B[4] + A[2]*B[7]) % n,
        (A[0]*B[2] + A[1]*B[5] + A[2]*B[8]) % n,
        (A[3]*B[0] + A[4]*B[3] + A[5]*B[6]) % n,
        (A[3]*B[1] + A[4]*B[4] + A[5]*B[7]) % n,
        (A[3]*B[2] + A[4]*B[5] + A[5]*B[8]) % n,
        (A[6]*B[0] + A[7]*B[3] + A[8]*B[6]) % n,
        (A[6]*B[1] + A[7]*B[4] + A[8]*B[7]) % n,
        (A[6]*B[2] + A[7]*B[5] + A[8]*B[8]) % n,
    )


def _mat3_pow(M, k, n):
    res = (1, 0, 0, 0, 1, 0, 0, 0, 1)
    base = M
    while k > 0:
        if k & 1:
            res = _mat3_mul(res, base, n)
        base = _mat3_mul(base, base, n)
        k >>= 1
    return res


def _mat3_dual_trace(A, n):
    tr1 = (A[0] + A[4] + A[8]) % n
    A2 = _mat3_mul(A, A, n)
    tr2 = (A2[0] + A2[4] + A2[8]) % n
    return (tr1 + 3 * tr2) % n


def lock07_generate(K_bound=1 << 11, seed=None, verbose=True):
    if seed is not None:
        random.seed(seed)
    t0 = time.time()
    I3 = (1, 0, 0, 0, 1, 0, 0, 0, 1)
    while True:
        p = (random.getrandbits(511) | (1 << 511) | 1) & ~(1 << 510)
        if p % 3 != 2 or not is_prime(p):
            continue
        M_3 = p * p + p + 1
        if not is_prime(M_3):
            continue
        M_test = (2 % p, (-3) % p, 1, 1, 0, 0, 0, 1, 0)
        if _mat3_pow(M_test, M_3, p) == I3 and _mat3_pow(M_test, 1, p) != I3:
            break

    while True:
        q = random.getrandbits(512) | (1 << 511) | (1 << 510) | 1
        if q > p + 2 and (p * q).bit_length() == 1024 and is_prime(q):
            break
    N = p * q
    assert M_3 < N

    while True:
        d1 = random.randrange(3, K_bound)
        if not is_prime(d1):
            continue
        d2 = random.randrange(3, K_bound)
        if d2 == d1 or not is_prime(d2):
            continue
        denom = (d2 - 3 * d1) % M_3
        if denom == 0:
            continue
        # Twisted Bilinear Matrix Entanglement: d2*(e + 2N) == d1*(3e + 5N) (mod M_3)
        e = (5 * d1 - 2 * d2) * N % M_3 * pow(denom, -1, M_3) % M_3
        if 1 < e < N and math.gcd(e, (p - 1) * (q - 1)) == 1:
            break

    assert N.bit_length() == 1024 and 1 < e < N
    assert (d2 * (e + 2 * N) - d1 * (3 * e + 5 * N)) % M_3 == 0
    if verbose:
        print("  [Lock 07 KeyGen] %.2fs | p=%db q=%db N=%db | M_3=%db PRIME (0%% smooth) | d1=%d d2=%d" %
              (time.time() - t0, p.bit_length(), q.bit_length(), N.bit_length(), M_3.bit_length(), d1, d2))
    pub = {"N": N, "e": e, "K_bound": K_bound}
    sk = {"p": p, "q": q, "M_3": M_3, "d1": d1, "d2": d2}
    return pub, sk


def lock07_solve(pub, verbose=True):
    N = int(pub["N"])
    e = int(pub["e"])
    K_bound = int(pub.get("K_bound", 1 << 11))
    t0 = time.time()

    for trial in range(1, 6):
        P_val = trial + 1
        Q_val = trial * 2 + 1
        M_base = (
            P_val % N, (-Q_val) % N, 1,
            1, 0, 0,
            0, 1, 0
        )
        A_mat = _mat3_pow(M_base, e + 2 * N, N)
        B_mat = _mat3_pow(M_base, 3 * e + 5 * N, N)
        if (A_mat[0] + A_mat[4] + A_mat[8]) % N == 3:
            continue

        I3 = (1, 0, 0, 0, 1, 0, 0, 0, 1)
        lhs, cur = [], I3
        for d2 in range(1, K_bound):
            cur = _mat3_mul(cur, A_mat, N)
            if is_prime(d2):
                lhs.append(_mat3_dual_trace(cur, N))

        rhs, cur = [], I3
        for d1 in range(1, K_bound):
            cur = _mat3_mul(cur, B_mat, N)
            if is_prime(d1):
                rhs.append(_mat3_dual_trace(cur, N))

        g = batch_poly_gcd(lhs, rhs, N)
        if g and 1 < g < N:
            if verbose:
                print("  [Lock 07 Solve]  %.2fs | Prime-order Cubic Lucas SL_3 dual-trace hit on trial=%d (%dx%d)" %
                      (time.time() - t0, trial, len(lhs), len(rhs)))
            return g, N // g
    return None


# ======================================================================
# LOCK 08: Two-Stage 4D Cubic Orthogonal Lattice + Base-2^240 Dyadic
#          4D Linear Divisor Coppersmith Cascade
# ======================================================================

def _fp_poly_mul_mod(A, B, F, p):
    res = [0] * (len(A) + len(B) - 1)
    for i, a in enumerate(A):
        if a:
            for j, b in enumerate(B):
                res[i + j] = (res[i + j] + a * b) % p
    while len(res) >= len(F):
        c = res[-1]
        deg_diff = len(res) - len(F)
        if c:
            for j in range(len(F) - 1):
                res[deg_diff + j] = (res[deg_diff + j] - c * F[j]) % p
        res.pop()
    return _poly_trim(res)


def _fp_poly_pow_mod(base, k, F, p):
    res = [1]
    b = base[:]
    while k > 0:
        if k & 1:
            res = _fp_poly_mul_mod(res, b, F, p)
        b = _fp_poly_mul_mod(b, b, F, p)
        k >>= 1
    return res


def _fp_poly_gcd(A, B, p):
    A = _poly_trim([x % p for x in A])
    B = _poly_trim([x % p for x in B])
    while B:
        _, r = _poly_divmod_small(A, B, p)
        A, B = B, r
    if A:
        inv_lc = pow(A[-1], -1, p)
        A = [c * inv_lc % p for c in A]
    return A


def _cubic_root_mod_p(u0, u1, u2, u3, p):
    if u3 % p == 0:
        return None
    inv_u3 = pow(u3, -1, p)
    F = [u0 * inv_u3 % p, u1 * inv_u3 % p, u2 * inv_u3 % p, 1]
    xp = _fp_poly_pow_mod([0, 1], p, F, p)
    xp_minus_x = _poly_trim([
        xp[0] if len(xp) > 0 else 0,
        ((xp[1] if len(xp) > 1 else 0) - 1) % p,
        xp[2] if len(xp) > 2 else 0
    ])
    g = _fp_poly_gcd(F, xp_minus_x, p)
    deg = len(g) - 1
    if deg <= 0:
        return None
    if deg == 1:
        return (-g[0]) % p
    for shift in range(1, 30):
        h = _fp_poly_pow_mod([shift, 1], (p - 1) // 2, g, p)
        h[0] = (h[0] - 1) % p
        h = _poly_trim(h)
        sp = _fp_poly_gcd(g, h, p)
        if len(sp) - 1 == 1:
            return (-sp[0]) % p
    return None


def _coppersmith_linear_4d(U_hi, U_lo_delta, N, X):
    g0 = math.gcd(U_hi, N)
    if 1 < g0 < N:
        return None, g0
    inv_hi = pow(U_hi, -1, N)
    c0 = U_lo_delta * inv_hi % N
    c0_sq = c0 * c0
    c0_2 = 2 * c0
    X2 = X * X
    X3 = X2 * X
    B = [
        [N * N, 0, 0, 0],
        [N * c0, N * X, 0, 0],
        [c0_sq, c0_2 * X, X2, 0],
        [0, c0_sq * X, c0_2 * X2, X3],
    ]
    red = lll(B)
    for row in red[:3]:
        c_0 = row[0]
        c_1 = row[1] // X
        c_2 = row[2] // X2
        c_3 = row[3] // X3
        coeffs = _poly_trim([c_0, c_1, c_2, c_3])
        if len(coeffs) < 2:
            continue
        def ev(x):
            r = 0
            for c in reversed(coeffs):
                r = r * x + c
            return r

        pts = [1, X]
        if len(coeffs) == 3 and coeffs[2] != 0:
            a1, a2 = coeffs[1], coeffs[2]
            crit = -a1 // (2 * a2)
            for d in (-1, 0, 1):
                if 1 < crit + d < X:
                    pts.append(crit + d)
        elif len(coeffs) == 4 and coeffs[3] != 0:
            a1, a2, a3 = coeffs[1], coeffs[2], coeffs[3]
            disc = 4 * a2 * a2 - 12 * a1 * a3
            if disc >= 0:
                s = math.isqrt(disc)
                for sign in (-1, 1):
                    crit = (-2 * a2 + sign * s) // (6 * a3)
                    for d in (-1, 0, 1):
                        if 1 < crit + d < X:
                            pts.append(crit + d)
        pts = sorted(set(pts))
        for p_x in pts:
            if ev(p_x) == 0:
                return p_x, None
        for i in range(len(pts) - 1):
            lo, hi = pts[i], pts[i + 1]
            flo, fhi = ev(lo), ev(hi)
            if flo == 0:
                return lo, None
            if fhi == 0:
                return hi, None
            if flo * fhi < 0:
                while lo < hi:
                    mid = (lo + hi) // 2
                    fmid = ev(mid)
                    if fmid == 0:
                        return mid, None
                    if flo * fmid <= 0:
                        hi = mid
                        fhi = fmid
                    else:
                        lo = mid + 1
                        flo = ev(lo)
                if ev(lo) == 0:
                    return lo, None
    return None, None


def lock08_generate(mask_bits=4, x0_bits=106, seed=None, verbose=True):
    if seed is not None:
        random.seed(seed)
    t0 = time.time()
    p = random.getrandbits(512) | (1 << 511) | (1 << 510) | 1
    while p.bit_length() != 512 or not is_prime(p):
        p += 2

    x0 = random.getrandbits(x0_bits) | (1 << (x0_bits - 1)) | 1
    delta_secret = random.randrange(1, 1 << mask_bits)
    base240 = 1 << 240

    while True:
        k_bits = 480 + x0_bits - 512
        k = random.getrandbits(k_bits) | (1 << (k_bits - 1))
        target = k * p - delta_secret
        U_hi = target // x0
        U_lo = target - U_hi * x0
        s_bits = 479 - x0_bits
        s = random.getrandbits(s_bits) | (1 << (s_bits - 1))
        U_hi -= s
        U_lo += s * x0
        assert U_hi * x0 + U_lo + delta_secret == k * p
        u3, u2 = U_hi >> 240, U_hi & (base240 - 1)
        u1, u0 = U_lo >> 240, U_lo & (base240 - 1)
        if min(u0, u1, u2, u3) <= 0:
            continue
        if max(u0.bit_length(), u1.bit_length(), u2.bit_length(), u3.bit_length()) > 242:
            continue
        ep = _cubic_root_mod_p(u0, u1, u2, u3, p)
        if ep is not None:
            break

    while True:
        q = random.getrandbits(512) | (1 << 511) | (1 << 510) | 1
        if q == p or (p * q).bit_length() != 1024 or not is_prime(q):
            continue
        eq = _cubic_root_mod_p(u0, u1, u2, u3, q)
        if eq is None:
            continue
        N = p * q
        e = (ep * q * pow(q, -1, p) + eq * p * pow(p, -1, q)) % N
        if 1 < e < N and (u3 * pow(e, 3, N) + u2 * e * e + u1 * e + u0) % N == 0:
            if math.gcd(e, (p - 1) * (q - 1)) == 1:
                break

    assert N.bit_length() == 1024 and 1 < e < N
    if verbose:
        print("  [Lock 08 KeyGen] %.2fs | p=%db q=%db N=%db | u_i~%db x0=%db delta=%d" %
              (time.time() - t0, p.bit_length(), q.bit_length(), N.bit_length(),
               u3.bit_length(), x0.bit_length(), delta_secret))
    pub = {"N": N, "e": e, "mask_bits": mask_bits, "x0_bits": x0_bits}
    sk = {"p": p, "q": q, "u0": u0, "u1": u1, "u2": u2, "u3": u3, "delta": delta_secret, "x0": x0}
    return pub, sk


def lock08_solve(pub, verbose=True):
    N = int(pub["N"])
    e = int(pub["e"])
    mask_bits = int(pub.get("mask_bits", 4))
    x0_bits = int(pub.get("x0_bits", 106))
    t0 = time.time()

    e2 = e * e % N
    e3 = e2 * e % N
    B1 = [
        [1, 0, 0, (-e3) % N],
        [0, 1, 0, (-e2) % N],
        [0, 0, 1, (-e) % N],
        [0, 0, 0, N],
    ]
    red1 = lll(B1)
    cands = []
    for row in red1:
        u3, u2, u1, u0 = row
        if (u3 * e3 + u2 * e2 + u1 * e + u0) % N != 0:
            continue
        if u3 < 0:
            u3, u2, u1, u0 = -u3, -u2, -u1, -u0
        if max(u3.bit_length(), u2.bit_length(), u1.bit_length(), u0.bit_length()) <= 245:
            cands.append((u0, u1, u2, u3))

    if not cands:
        return None

    X = 1 << (x0_bits + 1)
    for (u0, u1, u2, u3) in cands:
        U_hi = (u3 << 240) + u2
        U_lo = (u1 << 240) + u0
        for delta in range(1, 1 << mask_bits):
            root, g = _coppersmith_linear_4d(U_hi, U_lo + delta, N, X)
            if g and 1 < g < N:
                return g, N // g
            if root:
                g = math.gcd(U_hi * root + U_lo + delta, N)
                if 1 < g < N:
                    if verbose:
                        print("  [Lock 08 Solve]  %.2fs | 4D+4D Dyadic Lattice hit delta=%d x0=%db" %
                              (time.time() - t0, delta, root.bit_length()))
                    return g, N // g
    return None


# ======================================================================
# LOCK 09: Symmetric Chebyshev Product-to-Sum Kleptographic SETUP
#          + Fake Fermat Top-20-Bit Near-Square Halo Disguise
# ======================================================================

M_CHEB = (1 << 360) - (1 << 180) + 1
G_CHEB = 7


def _lucas_v_seq(g0, limit, mod_m):
    v = [2 % mod_m, g0 % mod_m]
    for _ in range(2, limit + 1):
        v.append((g0 * v[-1] - v[-2]) % mod_m)
    return v


def lock09_generate(K_bound=1 << 11, seed=None, verbose=True):
    if seed is not None:
        random.seed(seed)
    t0 = time.time()
    v_table = _lucas_v_seq(G_CHEB, 2 * K_bound, M_CHEB)

    # Plant Fake Fermat Near-Square Halo: lock top 20 bits of H1 and H2
    shared_prefix = (random.getrandbits(20) | (1 << 19) | (1 << 18)) << 132

    while True:
        d1 = random.randrange(200, K_bound)
        if not is_prime(d1):
            continue
        R_p = v_table[d1]
        for _ in range(500):
            H1 = shared_prefix | random.getrandbits(132)
            cand_p = H1 * M_CHEB + R_p
            if cand_p.bit_length() == 512 and is_prime(cand_p):
                p = cand_p
                break
        else:
            continue
        break

    while True:
        d2 = random.randrange(200, K_bound)
        if d2 == d1 or not is_prime(d2):
            continue
        R_q = v_table[d2]
        for _ in range(500):
            H2 = shared_prefix | random.getrandbits(132)
            cand_q = H2 * M_CHEB + R_q
            if cand_q.bit_length() == 512 and cand_q != p and (p * cand_q).bit_length() == 1024 and is_prime(cand_q):
                q = cand_q
                break
        else:
            continue
        break

    N = p * q
    assert N.bit_length() == 1024
    assert (H1 >> 132) == (H2 >> 132)
    assert (N - (v_table[d1 + d2] + v_table[abs(d1 - d2)])) % M_CHEB == 0
    if verbose:
        print("  [Lock 09 KeyGen] %.2fs | p=%db q=%db N=%db | Fake Fermat 20b Halo | d1=%d d2=%d" %
              (time.time() - t0, p.bit_length(), q.bit_length(), N.bit_length(), d1, d2))
    pub = {"N": N, "e": 65537, "K_bound": K_bound}
    sk = {"p": p, "q": q, "d1": d1, "d2": d2, "H1": H1, "H2": H2}
    return pub, sk


def lock09_solve(pub, verbose=True):
    N = int(pub["N"])
    K_bound = int(pub.get("K_bound", 1 << 11))
    t0 = time.time()

    v_table = _lucas_v_seq(G_CHEB, 2 * K_bound, M_CHEB)
    lookup = {val: idx for idx, val in enumerate(v_table)}
    n_mod = N % M_CHEB

    cands_d = []
    for D in range(0, K_bound):
        target = (n_mod - v_table[D]) % M_CHEB
        if target in lookup:
            S = lookup[target]
            if (S + D) % 2 == 0:
                d1 = (S + D) // 2
                d2 = (S - D) // 2
                if 1 < d1 < K_bound and 1 < d2 < K_bound:
                    cands_d.extend([d1, d2])

    X = 1 << 153
    for d_cand in cands_d:
        R_p = v_table[d_cand]
        root, g = _coppersmith_linear_4d(M_CHEB, R_p, N, X)
        if g and 1 < g < N:
            return g, N // g
        if root:
            p_cand = root * M_CHEB + R_p
            if 1 < p_cand < N and N % p_cand == 0:
                if verbose:
                    print("  [Lock 09 Solve]  %.2fs | Chebyshev V_a*V_b=V_{a+b}+V_{|a-b|} hit d=%d" %
                          (time.time() - t0, d_cand))
                return p_cand, N // p_cand
    return None


# ======================================================================
# LOCK 10: Phi_12(p) = p^4 - p^2 + 1 Dodecic Cyclotomic Torus T_12
#          + Dodecic Galois-Twisted Entanglement (1 < e < N)
# ======================================================================

def _a13_canon(v, n):
    c12 = v[12]
    return [(v[i] - c12) % n for i in range(12)]


def _a13_mul(a, b, n):
    res = [0] * 13
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                res[(i + j) % 13] += ai * bj
    return [x % n for x in res]


def _a13_pow(base, k, n):
    res = [1] + [0] * 12
    b = base[:]
    while k > 0:
        if k & 1:
            res = _a13_mul(res, b, n)
        b = _a13_mul(b, b, n)
        k >>= 1
    return res


def _a13_frob(a, k):
    s = pow(2, k, 13)
    out = [0] * 13
    for i in range(13):
        out[(i * s) % 13] = a[i]
    return out


def lock10_generate(K_bound=1 << 11, B=1 << 13, n_small=25, seed=None, verbose=True):
    if seed is not None:
        random.seed(seed)
    t0 = time.time()
    pool = [l for l in primes_upto(B) if l > (1 << 11) and l % 12 == 1 and l != 13]
    M_full = math.prod([l for l in primes_upto(B) if l % 12 == 1])

    while True:
        ls = random.sample(pool, n_small)
        L_smooth = math.prod(ls)
        if not (310 <= L_smooth.bit_length() <= 322):
            continue
        roots = []
        for l in ls:
            s3 = sqrt_mod(l - 3, l)
            u = (s3 + 1) * pow(2, -1, l) % l
            r = sqrt_mod(u, l)
            if r is None:
                r = sqrt_mod((1 - u) % l, l)
            assert (pow(r, 4, l) - r * r + 1) % l == 0
            roots.append(r)
        r_all, M_all = _crt_combine(roots + [2, 1], ls + [13, 2])
        lo_p = 1 << 331
        k0 = (lo_p - r_all) // M_all
        p = None
        for k in range(k0, k0 + 250000):
            cand = r_all + k * M_all
            if cand.bit_length() == 332 and is_prime(cand):
                Phi12_cand = pow(cand, 4) - cand * cand + 1
                G_cand = math.gcd(Phi12_cand, M_full)
                C12_cand = Phi12_cand // G_cand
                if C12_cand.bit_length() <= 1018:
                    p = cand
                    Phi12 = Phi12_cand
                    C12 = C12_cand
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
        denom = (d2 - 5 * d1) % C12
        if math.gcd(denom, C12) != 1:
            continue
        # Dodecic Galois-Twisted Entanglement: d2*(e + 4N) == d1*(5e + 9N) (mod C12)
        e = (9 * d1 - 4 * d2) * N % C12 * pow(denom, -1, C12) % C12
        if 1 < e < N and math.gcd(e, phi_N) == 1:
            break

    assert N.bit_length() == 1024 and 1 < e < N
    assert (d2 * M_full * (e + 4 * N) - d1 * M_full * (5 * e + 9 * N)) % Phi12 == 0
    if verbose:
        print("  [Lock 10 KeyGen] %.2fs | p=%db q=%db N=%db | e=%db (<N) | d1=%d d2=%d" %
              (time.time() - t0, p.bit_length(), q.bit_length(), N.bit_length(),
               e.bit_length(), d1, d2))
    pub = {"N": N, "e": e, "K_bound": K_bound, "B": B}
    sk = {"p": p, "q": q, "d1": d1, "d2": d2, "Phi12": Phi12, "C12": C12}
    return pub, sk


def lock10_solve(pub, verbose=True):
    N = int(pub["N"])
    e = int(pub["e"])
    K_bound = int(pub.get("K_bound", 1 << 11))
    B = int(pub.get("B", 1 << 13))
    t0 = time.time()

    M = math.prod([l for l in primes_upto(B) if l % 12 == 1])
    mod_phi13 = [1] * 13

    try:
        beta = [2, 1] + [0] * 11
        num = _a13_mul(_a13_frob(beta, 8), _a13_frob(beta, 6), N)
        den = _a13_mul(_a13_frob(beta, 2), beta, N)
        den_inv_12 = _poly_extgcd_inv(_a13_canon(den, N), mod_phi13, N)
        tau = _a13_mul(num, den_inv_12 + [0], N)

        Q_L = _a13_pow(tau, M * (e + 4 * N), N)
        Q_R = _a13_pow(tau, M * (5 * e + 9 * N), N)

        one = [1] + [0] * 12
        lhs, cur = [], one
        for d2 in range(1, K_bound):
            cur = _a13_mul(cur, Q_L, N)
            if is_prime(d2):
                lhs.append(_a13_canon(cur, N)[0])

        rhs, cur = [], one
        for d1 in range(1, K_bound):
            cur = _a13_mul(cur, Q_R, N)
            if is_prime(d1):
                rhs.append(_a13_canon(cur, N)[0])

        g = batch_poly_gcd(lhs, rhs, N)
        if g and 1 < g < N:
            if verbose:
                print("  [Lock 10 Solve]  %.2fs | Phi_12(p) T_12 torus collision hit (%dx%d)" %
                      (time.time() - t0, len(lhs), len(rhs)))
            return g, N // g
    except FactorFound as ff:
        g = math.gcd(ff.p, N)
        if 1 < g < N:
            return g, N // g
    return None

