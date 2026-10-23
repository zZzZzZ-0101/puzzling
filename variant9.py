"""
变种 9 (V2.1 加硬版): 纯素数阶复乘椭圆曲线跨模自指碰撞陷门

原报告问题修复:
  1. solver 只把素数 d1 放进 rhs 表 -> 实测仅 11.1% 的合法 (d1,d2) 满足, 近九成自解不开。
     改为: KeyGen 强制 d1 为素数 (与 solver 约定一致), 且仍保证 gcd(d1,d2)=1。
  2. ec_add / ec_mul / batch_poly_gcd 从未定义 -> 由 ctflib 提供。
  3. 声称 "20 秒", 实测 4 秒 -> 朴素暴力反而更容易撞开。加硬见下。

加硬 (HARD 档):
  把 (d1,d2) 的搜索域从 2^15 提到 2^22。朴素做法要枚举 2^44 对, 不可行;
  即使只做两条长度 2^22 的点列再两两 gcd 也是 2^44 次 gcd。
  唯一可行路径仍是乘积树 Batch-GCD, 但此时表长 4.2e6, 必须分块 + 控制内存,
  且必须先推导出碰撞式是可分离的 (LHS 只含 d1, RHS 只含 d2) 才能降到 2*2^22 步。
"""
import math, random, time, argparse
from ctflib import is_prime, ec_add, ec_mul, batch_poly_gcd, FactorFound

# ------------------------------------------------------------------ KeyGen
def generate(K_bound=1 << 15, seed=None, verbose=True):
    """
    D=3 (Eisenstein) 复乘: p = A^2 - A*B + B^2, Frobenius 迹 t = 2A - B,
    群阶 M_p = p + 1 - t 强制为 512-bit 素数 (0% 平滑度)。

    再取秘密 (d1, d2), d1 为素数, 令
        q = ((t-1)^{-1} * d1 * d2^{-1} mod M_p) + M_p
    则 p = M_p + t - 1  =>  p ≡ t-1 (mod M_p), 故
        N = p*q ≡ (t-1) * (t-1)^{-1} d1 d2^{-1} ≡ d1 * d2^{-1}  (mod M_p)
    即  d2 * N ≡ d1  (mod M_p)。
    """
    if seed is not None:
        random.seed(seed)
    t0 = time.time()
    tries = 0
    while True:
        tries += 1
        A = random.getrandbits(256) | (1 << 255)
        B = random.getrandbits(256) | (1 << 255)
        p = A * A - A * B + B * B
        if p.bit_length() != 512 or not is_prime(p):
            continue
        t = 2 * A - B
        M_p = p + 1 - t
        if M_p.bit_length() == 512 and is_prime(M_p):
            break
    assert 4 * p - t * t == 3 * B * B, "t 不是合法 Frobenius 迹"
    assert p == M_p + t - 1

    inv_t1 = pow(t - 1, -1, M_p)
    cnt = 0
    while True:
        cnt += 1
        # d1, d2 均取素数: 与 solver 的枚举约定一致 (原报告的致命不一致所在),
        # 自动保证 gcd=1, 消除 (k*d1, k*d2) 比例平凡解,
        # 并把两侧表长从 K 压到 pi(K) -> 乘积树代价降低约 87 倍
        d1 = random.randrange(3, K_bound)
        if not is_prime(d1):
            continue
        d2 = random.randrange(3, K_bound)
        if d2 == d1 or not is_prime(d2):
            continue
        r = d1 * pow(d2, -1, M_p) % M_p
        q = (inv_t1 * r % M_p) + M_p
        if q.bit_length() == 512 and is_prime(q):
            break
    N = p * q
    assert (d2 * N - d1) % M_p == 0, "核心自指同余不成立"
    if verbose:
        print("  [KeyGen] %.1fs  曲线搜索 %d 次, (d1,d2) 抽样 %d 次" %
              (time.time() - t0, tries, cnt))
        print("  [KeyGen] p=%d bit  M_p=%d bit (素数)  q=%d bit  N=%d bit" %
              (p.bit_length(), M_p.bit_length(), q.bit_length(), N.bit_length()))
        print("  [KeyGen] |p-q| = 2^%d  (Fermat/Lehman 失效)" % abs(p - q).bit_length())
    return N, 65537, dict(p=p, q=q, M_p=M_p, t=t, d1=d1, d2=d2)


# ------------------------------------------------------------------ Solver
def solve(N, K_bound=1 << 15, max_trial=25, block=None, verbose=True):
    """
    公开卷面只有 (N, e=65537, c)。解题者必须自行推导出:
      p 上存在复乘曲线, 其阶 M_p 满足 d2*N ≡ d1 (mod M_p),
      故在 E_b(Z/NZ) 上取 Q0 = [N]P0, 必有 [d2]Q0 ≡ [d1]P0 (mod p)。
    碰撞式可分离 -> 两条长度 K 的点列 + 乘积树 Batch-GCD。
    """
    for trial in range(1, max_trial + 1):
        x0, y0 = trial + 2, trial * 5 + 3
        P0 = (x0, y0)                      # 隐式定义 b = y0^2 - x0^3 mod N
        try:
            Q0 = ec_mul(N, P0, 0, N)
            if Q0 is None:
                continue
            lhs, cur = [], None            # [d2]Q0 的 x 坐标, 只枚举素数 d2
            for d2 in range(1, K_bound):
                cur = ec_add(cur, Q0, 0, N)
                if cur is None:
                    break
                if is_prime(d2):
                    lhs.append(cur[0])
            rhs, cur = [], None            # [d1]P0, 只保留素数 d1
            for d1 in range(1, K_bound):
                cur = ec_add(cur, P0, 0, N)
                if cur is None:
                    break
                if is_prime(d1):
                    rhs.append(cur[0])
            if verbose:
                print("  [Solve] trial=%d 表长 %d x %d, 开始乘积树扫描..." %
                      (trial, len(lhs), len(rhs)), flush=True)
            g = batch_poly_gcd(lhs, rhs, N, block=block)
            if g and 1 < g < N:
                if verbose:
                    print("  [Solve] trial=%d 命中, 表长 %d x %d" % (trial, len(lhs), len(rhs)))
                return g, N // g
        except FactorFound as ff:
            g = math.gcd(ff.p, N)
            if 1 < g < N:
                if verbose:
                    print("  [Solve] trial=%d 点加求逆直接捕获因子" % trial)
                return g, N // g
        except ZeroDivisionError:
            continue
    return None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bits", type=int, default=15, help="K_bound = 2^bits")
    ap.add_argument("--seed", type=int, default=20261023)
    a = ap.parse_args()
    K = 1 << a.bits
    print("=== 变种 9  K_bound = 2^%d ===" % a.bits)
    N, e, sk = generate(K, seed=a.seed)
    print("  [真值] d1=%d (素数) d2=%d" % (sk["d1"], sk["d2"]))
    t0 = time.time()
    res = solve(N, K)
    el = time.time() - t0
    if res:
        p_f, q_f = res
        ok = {p_f, q_f} == {sk["p"], sk["q"]}
        print("  [Solve] %.1fs  分解成功: %s" % (el, ok))
    else:
        print("  [Solve] %.1fs  失败" % el)
