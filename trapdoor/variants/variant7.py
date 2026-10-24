"""
变种 7 (V2.1): 三次 Pell 曲面 C_a(Z/NZ) 双轨交叉指数碰撞陷门

原报告问题修复:
  1. 完全没有 KeyGen (只给了 solver) -> 本文件补全。
  2. solve_variant7_cubic_pell(P0, M*e, N, a): 签名是 (P,k,a,n), a 与 n 被对调 -> 修正。
  3. rhs 只保留素数 d1, 但 KeyGen 未约束 d1 为素数 -> KeyGen 强制 d1 素数。
  4. batch_poly_gcd 未定义 -> 由 ctflib 提供。

数学 (复核无误):
  C_a: x^3 + a y^3 + a^2 z^3 - 3 a x y z = 1, 当 a 是模 p 的非三次剩余时,
  t^3 - a 在 F_p 上不可约, 该曲面是 F_{p^3} 的范数 1 环面, 群阶恰为
        |C_a(F_p)| = (p^3 - 1)/(p - 1) = p^2 + p + 1 = Phi_3(p)
  令 Phi_3(p) = L_smooth * C, 公钥设计为
        e ≡ (d1 * e0 + C) * (d2 + C)^{-1}   (mod Phi_3(p)),   e0 = N mod Phi_3(p)
  两边乘 (d2 + C) * M, 用 M*C ≡ 0 (mod Phi_3(p)):
        M e d2 + M e C ≡ M d1 e0 + M C   =>   d2 * (M e) ≡ d1 * (M N)  (mod Phi_3(p))
  故对任意基点 P0:
        (P0^(M e))^d2 ≡ (P0^(M N))^d1   (mod p)
"""
import math, random, time, argparse
from trapdoor.ctflib import is_prime, primes_upto, batch_poly_gcd

# ------------------------------------------------- 三次 Pell 群 (签名已修正)
def cubic_pell_mul(P, Q, a, n):
    x1, y1, z1 = P
    x2, y2, z2 = Q
    return ((x1 * x2 + a * (y1 * z2 + z1 * y2)) % n,
            (x1 * y2 + y1 * x2 + a * z1 * z2) % n,
            (x1 * z2 + y1 * y2 + z1 * x2) % n)


def cubic_pell_pow(P, k, a, n):
    res, base = (1, 0, 0), P
    while k > 0:
        if k & 1:
            res = cubic_pell_mul(res, base, a, n)
        base = cubic_pell_mul(base, base, a, n)
        k >>= 1
    return res


def norm_cubic(P, a, n):
    """R = (Z/nZ)[t]/(t^3-a) 中元素 x+yt+zt^2 的范数 = x^3 + a y^3 + a^2 z^3 - 3axyz."""
    x, y, z = P
    return (x ** 3 + a * y ** 3 + a * a * z ** 3 - 3 * a * x * y * z) % n


def on_surface(P, a, n):
    return norm_cubic(P, a, n) == 1 % n


# ------------------------------------------------------------------ KeyGen
def generate(K_bound=1 << 15, n_small=26, lo=1 << 11, hi=1 << 14, seed=None, verbose=True):
    """
    构造 512-bit 素数 p 使 Phi_3(p) = p^2+p+1 含大平滑因子 L_smooth。
    手法: 取素数 l_i ≡ 1 (mod 3), x^2+x+1 在 mod l_i 有根 r_i;
          CRT 得 p ≡ r (mod L), 再在该同余类里搜 512-bit 素数。
          则每个 l_i | p^2+p+1, 故 L_smooth = prod l_i | Phi_3(p)。
    """
    if seed is not None:
        random.seed(seed)
    t0 = time.time()
    pool = [l for l in primes_upto(hi) if l > lo and l % 3 == 1]
    while True:
        ls = random.sample(pool, n_small)
        L = math.prod(ls)
        if L.bit_length() > 400:            # 留出搜索空间
            continue
        roots = []
        for l in ls:
            r = next((x for x in range(1, l) if (x * x + x + 1) % l == 0), None)
            roots.append(r)
        # CRT
        r_all, M_all = 0, 1
        for r, l in zip(roots, ls):
            # 合并 r_all mod M_all 与 r mod l
            g = pow(M_all, -1, l)
            r_all = r_all + M_all * ((r - r_all) * g % l)
            M_all *= l
        r_all %= M_all
        # 在 p ≡ r_all (mod L) 中搜 512-bit 素数
        p = None
        lo512 = 1 << 511
        k0 = (lo512 - r_all) // M_all
        for k in range(k0, k0 + 400000):
            cand = r_all + k * M_all
            if cand.bit_length() != 512:
                continue
            if cand % 3 == 1 and is_prime(cand):
                p = cand
                break
        if p is None:
            continue
        Phi3 = p * p + p + 1
        L_smooth = 1
        for l in ls:
            assert Phi3 % l == 0
            L_smooth *= l
        C = Phi3 // L_smooth
        if C.bit_length() < 600:
            continue
        break

    # 第二个素数 q
    while True:
        q = random.getrandbits(512) | (1 << 511) | 1
        if is_prime(q):
            break
    N = p * q
    e0 = N % Phi3

    # 选 a 为模 p 的非三次剩余 (保证 t^3-a 不可约 => 群阶 = Phi_3(p))
    exp3 = (p - 1) // 3
    a = next(x for x in range(2, 500) if pow(x, exp3, p) != 1)

    # 秘密 (d1, d2): d1 素数 (与 solver 约定一致)
    while True:
        d1 = random.randrange(3, K_bound)
        if not is_prime(d1):
            continue
        d2 = random.randrange(2, K_bound)
        if math.gcd(d1, d2) != 1:
            continue
        if math.gcd(d2 + C, Phi3) != 1:
            continue
        e = (d1 * e0 + C) * pow(d2 + C, -1, Phi3) % Phi3
        if e <= 1 or math.gcd(e, (p - 1) * (q - 1)) != 1:
            continue
        break

    # 自检: d2 * (M e) ≡ d1 * (M N) mod Phi3
    M = math.prod(ls)
    assert (d2 * M * e - d1 * M * N) % Phi3 == 0, "双轨消元恒等式不成立"
    if verbose:
        print("  [KeyGen] %.1fs  p=%d bit  Phi3=%d bit  L_smooth=%d bit  C=%d bit" %
              (time.time() - t0, p.bit_length(), Phi3.bit_length(),
               L_smooth.bit_length(), C.bit_length()))
        print("  [KeyGen] 平滑素因子 %d 个, 最大 %d ; a=%d (非三次剩余)" % (len(ls), max(ls), a))
    return N, e, a, dict(p=p, q=q, Phi3=Phi3, C=C, d1=d1, d2=d2, ls=ls, M=M)


# ------------------------------------------------------------------ Solver
def solve(N, e, a, B=1 << 14, K_bound=1 << 15, block=None, max_trial=11, verbose=True):
    """公开卷面: (N, e, a, c)。解题者需自行推导双轨消元式并实现乘积树碰撞。"""
    M = math.prod([l for l in primes_upto(B) if l % 3 == 1])
    for trial in range(1, max_trial + 1):
        # 基点必须落在范数 1 环面上, 否则其阶整除 p^3-1 而非 Phi_3(p), 碰撞式失效。
        # 构造: 任取 beta, m = Norm(beta); 则 Norm(beta^3 * m^{-1}) = m^3 / m^3 = 1。
        beta = (trial + 1, trial, 1)
        m = norm_cubic(beta, a, N)
        if math.gcd(m, N) != 1:
            g = math.gcd(m, N)
            if 1 < g < N:
                return g, N // g
            continue
        b3 = cubic_pell_pow(beta, 3, a, N)
        im = pow(m, -1, N)
        P0 = tuple(c * im % N for c in b3)
        assert norm_cubic(P0, a, N) == 1, "基点未归一到范数 1"
        Q_left = cubic_pell_pow(P0, M * e, a, N)      # <-- 参数顺序已修正 (a, N)
        Q_right = cubic_pell_pow(P0, M * N, a, N)
        lhs, cur = [], (1, 0, 0)
        for _ in range(1, K_bound):
            cur = cubic_pell_mul(cur, Q_left, a, N)
            lhs.append(cur[0])
        rhs, cur = [], (1, 0, 0)
        for d1 in range(1, K_bound):
            cur = cubic_pell_mul(cur, Q_right, a, N)
            if is_prime(d1):
                rhs.append(cur[0])
        g = batch_poly_gcd(lhs, rhs, N, block=block)
        if g and 1 < g < N:
            if verbose:
                print("  [Solve] trial=%d 命中, 表长 %d x %d" % (trial, len(lhs), len(rhs)))
            return g, N // g
    return None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bits", type=int, default=13)
    ap.add_argument("--seed", type=int, default=77)
    args = ap.parse_args()
    K = 1 << args.bits
    print("=== 变种 7  K_bound = 2^%d ===" % args.bits)
    N, e, a, sk = generate(K, seed=args.seed)
    print("  [真值] d1=%d (素数) d2=%d" % (sk["d1"], sk["d2"]))
    t0 = time.time()
    res = solve(N, e, a, K_bound=K)
    el = time.time() - t0
    if res:
        print("  [Solve] %.1fs  分解成功: %s" % (el, {res[0], res[1]} == {sk["p"], sk["q"]}))
    else:
        print("  [Solve] %.1fs  失败" % el)
