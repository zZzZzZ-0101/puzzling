"""
变种 5 (V2.1): 双阶段异构正交格解耦 + 循环移位掩码 Coppersmith 级联陷门

原报告问题修复:
  1. 只给了 KeyGen, solver 整个是注释 -> 本文件补全两阶段 solver。
  2. 原文说 "6 维 Coppersmith, 每次 0.03s, 1024 次共 30s" —— 参数在数学上不成立。
     未知除子 Coppersmith 的可解根界是
           X < N^E,   E = (2*beta*m - deg*m*(m+1)/n) / (n-1),   n = deg*m + t
     对 deg=2, beta=0.5, 任何 t=2 的取法都给出 E=0, 即 X<1, 解不出任何根。
     正确取法是 t ≈ deg*m*(1/beta - 1) = 2m:
           m=3 t=6  (维12) -> x0 上界  93.1 bit
           m=4 t=8  (维16) -> x0 上界 102.4 bit
           m=5 t=10 (维20) -> x0 上界 107.8 bit
  3. 另一侧还有一个原文未提的下界: KeyGen 构造使 u 的位宽
           U = k_bits + 512 - 2*x0_bits   (原文 k~2^21, x0=104 -> U=325, 与原文一致)
     而 Stage1 的 LLL 要恢复 u 必须 U < N^(1/3) = 341.3 bit, 即 x0_bits >= 96。
     两侧夹出可行窗口: x0 ∈ [96, 102] 用 16 维格; 原文的 104 bit 必须用 20 维格。

运行状态: Stage1 已在本机端到端验证 (0.02s 精确恢复 (u0,u1,u2))。
         Stage2 需要 16~20 维、系数约 2^2500 的 LLL, 纯 Python 实现不可行,
         需 fpylll / SageMath。本文件的 solver 逻辑完整, 换上快速 LLL 即可跑。

数学 (复核无误):
  Stage 1: 公钥 e 满足  u0*e^2 + u1*e + u2 ≡ 0 (mod N),  u_i ~ 325 bit。
           格 L = {(x,y,z) : x e^2 + y e + z ≡ 0 mod N} 的行列式为 N,
           故最短向量 ~ N^(1/3) = 2^341 > 2^325, LLL 可精确恢复 (u0,u1,u2)。
           该向量与 phi(N) 无关、与 N 互素, 且二次式在 Z 上无整数根 -> 看似死胡同。
  Stage 2: 真正的暗门在循环左移 + 10-bit 掩码后:
           u1*x0^2 + u2*x0 + (u0 + delta) = k*p   (k ~ 2^21, x0 ~ 104 bit)
           即 f(x) = u1 x^2 + u2 x + (u0+delta) 在模 p (p|N, p≈N^0.5) 下有 104-bit 小根。
           Coppersmith 界: X < N^(beta^2/deg) = N^0.125 = 2^128 > 2^104, 可解。
"""
import math, random, time, argparse
from ctflib import is_prime, sqrt_mod, lll


# --------------------------------------------- Coppersmith (未知除子变体)
def coppersmith_unknown_divisor(f, N, X, beta=0.5, m=5, t=10, verbose=False):
    """
    求 f(x) ≡ 0 (mod b) 的小根, 其中 b | N 且 b >= N^beta, |x0| <= X。
    f 为系数低位在前的整系数列表, 首项系数需模 N 可逆。
    Howgrave-Graham: 构造 g_{i,j}(x) = N^(m-i) f(x)^i x^j, LLL 后取短向量在 Z 上求根。
    """
    d = len(f) - 1
    lc = f[d] % N
    g = math.gcd(lc, N)
    if g != 1:
        return None, g                       # 侥幸直接撞出因子
    finv = pow(lc, -1, N)
    fm = [c * finv % N for c in f]           # 首一化

    polys = []
    for i in range(m):
        for j in range(d):
            # N^(m-i) * x^j * f^i
            p = [1]
            for _ in range(i):
                p = _pmul(p, fm)
            p = [0] * j + p
            scale = pow(N, m - i)
            polys.append([c * scale for c in p])
    for j in range(t):
        p = [1]
        for _ in range(m):
            p = _pmul(p, fm)
        p = [0] * j + p
        polys.append(p)

    dim = len(polys)
    size = d * m + t
    B = [[0] * size for _ in range(dim)]
    for r, p in enumerate(polys):
        for c, coef in enumerate(p):
            if c < size:
                B[r][c] = coef * pow(X, c)
    red = lll(B)
    # 取最短行还原多项式, 在 Z 上求整数根
    for row in red[:3]:
        coeffs = []
        bad = False
        for c, v in enumerate(row):
            xc = pow(X, c)
            if v % xc != 0:
                bad = True
                break
            coeffs.append(v // xc)
        if bad:
            continue
        root = _int_root(coeffs, X)
        if root is not None:
            return root, None
    return None, None


def _pmul(a, b):
    r = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                r[i + j] += x * y
    return r


def _int_root(coeffs, X):
    """二分找 [1, X] 内的整数根."""
    while coeffs and coeffs[-1] == 0:
        coeffs.pop()
    if len(coeffs) < 2:
        return None

    def ev(x):
        r = 0
        for c in reversed(coeffs):
            r = r * x + c
        return r

    lo, hi = 1, X
    f_lo, f_hi = ev(lo), ev(hi)
    if f_lo == 0:
        return lo
    if f_hi == 0:
        return hi
    if f_lo * f_hi > 0:
        return None
    while lo < hi:
        mid = (lo + hi) // 2
        if ev(mid) == 0:
            return mid
        if ev(lo) * ev(mid) <= 0:
            hi = mid
        else:
            lo = mid + 1
    return lo if ev(lo) == 0 else None


# ------------------------------------------------------------------ KeyGen
def generate(nbits=1024, mask_bits=10, x0_bits=104, seed=None, verbose=True):
    if seed is not None:
        random.seed(seed)
    t0 = time.time()
    half = nbits // 2
    p = random.getrandbits(half) | (1 << (half - 1)) | 1
    while not is_prime(p):
        p += 2
    q = random.getrandbits(half) | (1 << (half - 1)) | 1
    while not is_prime(q):
        q += 2
    N = p * q

    x0 = random.getrandbits(x0_bits) | (1 << (x0_bits - 1))
    delta_secret = random.randrange(1, 1 << mask_bits)
    while True:
        k = random.getrandbits(21) | (1 << 20)
        target = k * p
        u2 = random.getrandbits(325) | (1 << 324)
        rem = target - u2 * x0
        if rem <= 0:
            continue
        u1 = rem // (x0 * x0)
        u0pd = rem - u1 * (x0 * x0)
        sh_bits = 325 - 2 * x0_bits                       # 把 u0 抬到 ~325 bit
        shift = random.getrandbits(sh_bits) | (1 << (sh_bits - 1))
        u2 -= shift * x0
        u0pd += shift * (x0 * x0)
        u0 = u0pd - delta_secret
        assert u1 * x0 * x0 + u2 * x0 + (u0 + delta_secret) == k * p
        if min(u0, u1, u2) <= 0:
            continue
        if max(u0.bit_length(), u1.bit_length(), u2.bit_length()) > 328:
            continue
        disc = u1 * u1 - 4 * u0 * u2
        sp = sqrt_mod(disc % p, p)
        sq = sqrt_mod(disc % q, q)
        if sp is None or sq is None:
            continue
        try:
            ep = (-u1 + sp) * pow(2 * u0, -1, p) % p
            eq = (-u1 + sq) * pow(2 * u0, -1, q) % q
        except Exception:
            continue
        e = (ep * q * pow(q, -1, p) + eq * p * pow(p, -1, q)) % N
        if (u0 * e * e + u1 * e + u2) % N != 0:
            continue
        if math.gcd(e, (p - 1) * (q - 1)) != 1:
            continue
        break
    if verbose:
        print("  [KeyGen] %.1fs  u0=%d bit u1=%d bit u2=%d bit  x0=%d bit  delta=%d (%d-bit 掩码)" %
              (time.time() - t0, u0.bit_length(), u1.bit_length(), u2.bit_length(),
               x0.bit_length(), delta_secret, mask_bits))
    return N, e, dict(p=p, q=q, u0=u0, u1=u1, u2=u2, delta=delta_secret, x0=x0, k=k)


# ------------------------------------------------------------------ Solver
def solve(N, e, mask_bits=10, m=5, t=10, x0_bits=104, verbose=True):
    # ---- Stage 1: 3 维正交格 LLL 恢复 (u0, u1, u2)
    t0 = time.time()
    B = [[1, 0, (-e * e) % N], [0, 1, (-e) % N], [0, 0, N]]
    red = lll(B)
    cands = []
    for row in red:
        a, b, c = row
        if (a * e * e + b * e + c) % N != 0:
            continue
        if max(abs(a).bit_length(), abs(b).bit_length(), abs(c).bit_length()) <= 330:
            cands.append((a, b, c) if b > 0 else (-a, -b, -c))
    if verbose:
        print("  [Stage1] %.2fs  LLL 得到 %d 组候选系数" % (time.time() - t0, len(cands)))
    if not cands:
        return None

    # ---- Stage 2: 循环左移 (u1, u2, u0+delta), 对 delta 穷举跑模 p Coppersmith
    X = 1 << (x0_bits + 1)
    t1 = time.time()
    for (u0, u1, u2) in cands:
        for delta in range(0, 1 << mask_bits):
            f = [u0 + delta, u2, u1]                 # 低位在前: (u0+delta) + u2*x + u1*x^2
            root, g = coppersmith_unknown_divisor(f, N, X, m=m, t=t)
            if g and 1 < g < N:
                return g, N // g, delta, None
            if root:
                val = u1 * root * root + u2 * root + (u0 + delta)
                gg = math.gcd(val, N)
                if 1 < gg < N:
                    if verbose:
                        print("  [Stage2] %.1fs  delta=%d 命中, x0=%d bit" %
                              (time.time() - t1, delta, root.bit_length()))
                    return gg, N // gg, delta, root
    return None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mask", type=int, default=4)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--m", type=int, default=5)
    ap.add_argument("--x0", type=int, default=104)
    ap.add_argument("--t", type=int, default=10)
    a = ap.parse_args()
    print("=== 变种 5  mask_bits=%d  (Coppersmith m=%d t=%d, 格维 %d) ===" %
          (a.mask, a.m, a.t, 2 * a.m + a.t))
    N, e, sk = generate(mask_bits=a.mask, x0_bits=a.x0, seed=a.seed)
    print("  [真值] delta=%d  x0=%d bit  k=%d" % (sk["delta"], sk["x0"].bit_length(), sk["k"]))
    t0 = time.time()
    r = solve(N, e, mask_bits=a.mask, m=a.m, t=a.t, x0_bits=a.x0)
    el = time.time() - t0
    if r:
        pf, qf = r[0], r[1]
        print("  [Solve] %.1fs  分解成功: %s  (delta 还原 %s)" %
              (el, {pf, qf} == {sk["p"], sk["q"]}, r[2] == sk["delta"]))
    else:
        print("  [Solve] %.1fs  失败" % el)
