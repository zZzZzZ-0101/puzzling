"""
变种 6 (V2.1 重构): 非 2 幂次动态基共享模数陷门

原方案为何不可救:
  原 solver 要求动态模数 M = 3^186 + d1 在 [101, 50000] 内至少有 8 个小素因子,
  用 Legendre 符号做二次剩余筛。实测扫遍 d1 ∈ [1,128):
        小素因子个数分布 {0:53, 1:49, 2:24, 3:1}, 最大仅 3 个
  没有任何 d1 能通过 >=8 的门槛 -> candidates 恒为空列表。
  且原构造 N ≡ a0*p^2 + d2*p (mod M) 对 p 是二次的, 还原 p 需在未知分解的
  295-bit 合数 M 上开平方 —— 这本身就是一道独立难题, 不是"0.001 秒筛掉 99.9%"。

重构思路 (保留"隐藏共享基 M"的核心创意, 换掉不可行的求解路径):
  把 q 的低块从依赖 L 改为常数 d2, 使关系对 p 变成线性:
        p = H1 * M + L,      q = H2 * M + d2,      M = 3^186 + d1
        => N = p*q ≡ L * d2   (mod M)
  再强制 L < 2^260 且 d2 < 2^8, 于是 L*d2 < 2^268 < M ≈ 2^294.8 不发生回绕,
  因此 **N mod M 作为整数恰好等于 L*d2**。位长本身就是判据:
        猜对 d1  -> (N mod M).bit_length() <= 268
        猜错 d1  -> N mod M 在 [0,M) 上近似均匀, 位长 ~295
  筛选代价是 2^16 次大整数取模 (~0.1 秒), 而非 4096 次 Coppersmith (57 小时)。
  定位 d1 后, 分解小整数 r = N mod M 得 d2 与 L, 最后一次
  "已知低位" Coppersmith (f(x) = M*x + L mod p, 根 H1 ~ 2^217 < N^0.25) 还原 p。

诚实的强度说明: d1 只有 16 bit 熵, 这是"谜题难度"而非密码学难度 ——
解题者一旦推导出共享基结构, 枚举是平凡的。真正的壁垒在于推导出
(a) p,q 共享隐藏基 M=3^186+d1, (b) 残数小到不回绕, (c) 已知低位 Coppersmith。
"""
import math, random, time, argparse
from ctflib import is_prime
from variant5 import coppersmith_unknown_divisor

R_BASE = 3 ** 186          # 295 bit, 非 2 幂次基


def generate(d1_bits=16, L_bits=260, d2_bits=8, seed=None, verbose=True):
    if seed is not None:
        random.seed(seed)
    t0 = time.time()
    d1 = random.randrange(1, 1 << d1_bits)
    M = R_BASE + d1
    while True:
        L = random.getrandbits(L_bits) | (1 << (L_bits - 1))
        H1 = random.getrandbits(217) | (1 << 216)
        p = H1 * M + L
        if p.bit_length() == 512 and is_prime(p):
            break
    while True:
        d2 = random.randrange(3, 1 << d2_bits)
        H2 = random.getrandbits(217) | (1 << 216)
        q = H2 * M + d2
        if q.bit_length() == 512 and is_prime(q) and math.gcd(d2, L) == 1:
            break
    N = p * q
    assert N % M == L * d2, "无回绕关系不成立"
    assert (L * d2).bit_length() <= L_bits + d2_bits
    if verbose:
        print("  [KeyGen] %.1fs  d1=%d  d2=%d  L=%d bit  M=%d bit  N=%d bit" %
              (time.time() - t0, d1, d2, L.bit_length(), M.bit_length(), N.bit_length()))
        print("  [KeyGen] |p-q| = 2^%d  ; N mod M 位长 = %d (阈值 %d)" %
              (abs(p - q).bit_length(), (L * d2).bit_length(), L_bits + d2_bits))
    return N, 65537, dict(p=p, q=q, M=M, d1=d1, d2=d2, L=L, H1=H1)


def solve(N, d1_bits=16, thresh=272, d2_bits=8, L_bits=260, m=5, t=5, verbose=True):
    # ---- Stage 1: 用"不回绕"判据定位 d1 (2^16 次取模, 极快)
    t0 = time.time()
    hits = []
    for d1 in range(1, 1 << d1_bits):
        M = R_BASE + d1
        r = N % M
        if r.bit_length() <= thresh:
            hits.append((d1, M, r))
    if verbose:
        print("  [Stage1] %.2fs  扫描 2^%d 个 d1, 通过不回绕判据的候选: %d 个" %
              (time.time() - t0, d1_bits, len(hits)))
    if not hits:
        return None

    # ---- Stage 2: 分解 r = L * d2, d2 < 2^d2_bits
    for d1, M, r in hits:
        for d2 in range(2, 1 << d2_bits):
            if r % d2:
                continue
            L = r // d2
            # L 的最高位由 KeyGen 置位, 故位长精确已知 -> 把 d2 候选压到近乎唯一,
            # 避免对错误的 d2 白跑 50 秒的 Coppersmith
            if L.bit_length() != L_bits:
                continue
            # ---- Stage 3: 已知低位 Coppersmith, f(x) = M*x + L mod p
            t1 = time.time()
            root, g = coppersmith_unknown_divisor([L, M], N, 1 << 220, m=m, t=t)
            if g and 1 < g < N:
                return g, N // g, d1, d2
            if root:
                pc = root * M + L
                if 1 < pc < N and N % pc == 0:
                    if verbose:
                        print("  [Stage3] %.1fs  Coppersmith 还原 H1 (%d bit), d1=%d d2=%d" %
                              (time.time() - t1, root.bit_length(), d1, d2))
                    return pc, N // pc, d1, d2
    return None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=606)
    ap.add_argument("--d1bits", type=int, default=16)
    a = ap.parse_args()
    print("=== 变种 6 (重构版)  d1 ∈ [1, 2^%d) ===" % a.d1bits)
    N, e, sk = generate(d1_bits=a.d1bits, seed=a.seed)
    print("  [真值] d1=%d d2=%d" % (sk["d1"], sk["d2"]))
    t0 = time.time()
    r = solve(N, d1_bits=a.d1bits)
    el = time.time() - t0
    if r:
        print("  [Solve] %.1fs  分解成功: %s  (d1 %s, d2 %s)" %
              (el, {r[0], r[1]} == {sk["p"], sk["q"]},
               r[2] == sk["d1"], r[3] == sk["d2"]))
    else:
        print("  [Solve] %.1fs  失败" % el)
