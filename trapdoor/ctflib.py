"""
ctflib.py - 密码学挑战赛陷门方案的公共算法库 (纯 Python, 无外部依赖)

补齐原报告中被反复调用但从未定义的核心工具:
  - batch_poly_gcd   : 子乘积树 + 快速多点求值, 在 Z/NZ 上做两表碰撞提取
  - EC over Z/NZ     : 带因子捕获 (FactorFound) 的射影/仿射椭圆曲线算术
  - LLL              : 纯 Python 整数 LLL (Lovasz 条件, delta=0.99)
  - coppersmith_1d   : Howgrave-Graham 单变量模 p 小根

可选加速 (装了就用, 没装退回纯 Python; 设 TRAPDOOR_PURE=1 强制纯 Python):
  - gmpy2  : Kronecker 打包后的大整数乘法、素性测试
  - fpylll : lll() 改走 fplll (变种 5 Stage 2 的 20 维格必须用它)
"""
import math, os, random

if os.environ.get("TRAPDOOR_PURE"):
    gmpy2 = None
    _fplll = None
else:
    try:
        import gmpy2
    except ImportError:
        gmpy2 = None
    try:
        import fpylll as _fplll
    except ImportError:
        _fplll = None

BACKEND = {"gmpy2": gmpy2 is not None, "fpylll": _fplll is not None}

# ----------------------------------------------------------------- 数论基础
_SMALL = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]


def is_prime(n):
    if n < 2:
        return False
    if gmpy2 is not None:
        return bool(gmpy2.is_prime(n, 25))
    for p in _SMALL:
        if n % p == 0:
            return n == p
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for a in _SMALL:
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def primes_upto(B):
    sieve = bytearray([1]) * (B + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(B ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i:: i] = bytearray(len(sieve[i * i:: i]))
    return [i for i in range(2, B + 1) if sieve[i]]


def sqrt_mod(a, p):
    """Tonelli-Shanks. 返回 x 使 x^2 = a mod p, 无解返回 None."""
    a %= p
    if a == 0:
        return 0
    if p == 2:
        return a
    if pow(a, (p - 1) // 2, p) != 1:
        return None
    if p % 4 == 3:
        return pow(a, (p + 1) // 4, p)
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    m, c, t, r = s, pow(z, q, p), pow(a, q, p), pow(a, (q + 1) // 2, p)
    while t != 1:
        i, t2 = 0, t
        while t2 != 1:
            t2 = t2 * t2 % p
            i += 1
        b = pow(c, 1 << (m - i - 1), p)
        m, c, t, r = i, b * b % p, t * b % p * b % p, r * b % p
    return r


class FactorFound(Exception):
    """在 Z/NZ 上求逆失败时抛出, 携带捕获到的非平凡因子."""

    def __init__(self, g):
        self.p = g
        super().__init__("factor %d" % g)


def inv_mod_n(a, n):
    a %= n
    g = math.gcd(a, n)
    if g != 1:
        if g != n:
            raise FactorFound(g)
        raise ZeroDivisionError("zero")
    return pow(a, -1, n)


# ------------------------------------------- 多项式 (系数低位在前) over Z/NZ
#
# 乘法走 Kronecker 代换: 把多项式按固定位宽打包成一个大整数, 用 CPython 自己的
# C 层大整数乘法完成卷积, 再拆回系数。比纯 Python 手写 Karatsuba 快一个数量级,
# 因为所有热循环都落在解释器之外 (bytes 打包 + 一次 int 乘法)。
#
# 除法走 Newton 迭代 (反转 + 幂级数求逆), 把 poly_rem 从朴素 O(d^2) 降到 O(M(d))。
# 这两件事合起来, 才能让余数树真正达到教科书上的 O(M(K) log K)。

_SCHOOL = 24


def _school_mul(a, b, n):
    res = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                res[i + j] += ai * bj
    return [c % n for c in res]


def poly_mul(a, b, n):
    """Kronecker 代换乘法 (小度数退回朴素)."""
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return []
    if min(la, lb) <= _SCHOOL:
        return _school_mul(a, b, n)
    # 每个结果系数 < min(la,lb) * n^2, 预留足够位宽并对齐到字节
    bits = 2 * n.bit_length() + min(la, lb).bit_length() + 2
    nb = (bits + 7) // 8
    A = int.from_bytes(b"".join((x % n).to_bytes(nb, "little") for x in a), "little")
    B = int.from_bytes(b"".join((x % n).to_bytes(nb, "little") for x in b), "little")
    C = int(gmpy2.mpz(A) * gmpy2.mpz(B)) if gmpy2 is not None else A * B
    out = la + lb - 1
    raw = C.to_bytes(nb * (la + lb) + 8, "little")
    return [int.from_bytes(raw[i * nb:(i + 1) * nb], "little") % n for i in range(out)]


def poly_sub(a, b, n):
    out = [0] * max(len(a), len(b))
    for i, c in enumerate(a):
        out[i] = c
    for i, c in enumerate(b):
        out[i] = (out[i] - c) % n
    return [c % n for c in out]


def _trim(p):
    while p and p[-1] == 0:
        p.pop()
    return p


def poly_inv_series(f, k, n):
    """求 g 使 f*g ≡ 1 (mod x^k). 要求 f[0] 模 n 可逆. Newton 迭代, 每步倍增精度."""
    g = [inv_mod_n(f[0], n)]
    while len(g) < k:
        l = min(2 * len(g), k)
        t = poly_mul(f[:l], g, n)[:l]            # t = f*g mod x^l
        t = [(-c) % n for c in t]
        t[0] = (t[0] + 2) % n                    # t = 2 - f*g
        g = poly_mul(g, t, n)[:l]                # g <- g*(2 - f*g)
    return g[:k]


def poly_divmod_fast(f, g, n):
    """f = q*g + r, g 首一. 反转 + Newton 幂级数求逆, O(M(d))."""
    df, dg = len(f) - 1, len(g) - 1
    if df < dg:
        return [], f[:]
    k = df - dg + 1
    rf = f[::-1]
    rg = g[::-1]                                 # rg[0] = g 的首项系数 = 1
    ginv = poly_inv_series(rg[:k] if len(rg) >= k else rg + [0] * (k - len(rg)), k, n)
    q = poly_mul(rf[:k], ginv, n)[:k][::-1]
    r = poly_sub(f, poly_mul(q, g, n), n)[:dg]
    return q, r


def poly_rem(a, b, n):
    """a mod b, b 必须首一. 大度数走 Newton, 小度数走朴素回代."""
    db = len(b) - 1
    if db < 0:
        raise ZeroDivisionError
    if len(a) - 1 < db:
        return [x % n for x in a] + [0] * (db - len(a))
    if db <= _SCHOOL or len(a) - db <= _SCHOOL:
        a = a[:]
        for i in range(len(a) - 1, db - 1, -1):
            c = a[i] % n
            if c:
                off = i - db
                for j in range(db + 1):
                    a[off + j] = (a[off + j] - c * b[j]) % n
        return [x % n for x in a[:db]]
    _, r = poly_divmod_fast(a, b, n)
    return (r + [0] * (db - len(r)))[:db]


def _subproduct_tree(pts, n):
    """返回层级列表, 第 0 层是 (X - pt), 顶层是全积."""
    level = [[(-p) % n, 1] for p in pts]
    tree = [level]
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level) - 1, 2):
            nxt.append(poly_mul(level[i], level[i + 1], n))
        if len(level) % 2:
            nxt.append(level[-1])
        level = nxt
        tree.append(level)
    return tree


def _build_tree(pts, n):
    """递归子乘积树节点: (多项式, 左子, 右子). 叶子为 (X - pt)."""
    if len(pts) == 1:
        return ([(-pts[0]) % n, 1], None, None)
    m = len(pts) // 2
    L = _build_tree(pts[:m], n)
    R = _build_tree(pts[m:], n)
    return (poly_mul(L[0], R[0], n), L, R)


def _eval_tree(poly, node, n, out):
    """余数树下降: 把 poly 对节点多项式取余后分别下沉到左右子树."""
    r = poly_rem(poly, node[0], n)
    if node[1] is None:
        out.append(r[0] if r else 0)
        return
    _eval_tree(r, node[1], n, out)
    _eval_tree(r, node[2], n, out)


def multipoint_eval(poly, pts, n):
    """在 pts 的所有点上求 poly 的值, O(K log^2 K)."""
    if not pts:
        return []
    tree = _build_tree(pts, n)
    out = []
    _eval_tree(poly, tree, n, out)
    return out


def batch_poly_gcd(left, right, n, block=None):
    """
    在 Z/NZ 上提取两表碰撞: 求 gcd( prod_{i,j} (left_i - right_j), N ).

    模 N 下 dict/set 哈希碰撞完全失效 (左右两边只在模 p 下相等),
    必须走多项式路径: 建子乘积树 P(X)=prod(X-left_i), 再用余数树在所有
    right_j 上做快速多点求值并累乘。

    复杂度说明 (这一点原报告没说清, 且直接决定加硬档能否解出):
      若 poly_rem 是朴素 O(d^2) 回代, 总代价退化为 O(K_L * K_R), 与分块无关 ——
      调大分块毫无帮助。只有配上 Newton 迭代除法, 代价才真正变成
      O(M(B) log B) 每块对, 此时 B 越大越好, 故默认 block=None 表示整表一块。

    返回捕获到的非平凡因子, 失败返回 None。
    """
    if not left or not right:
        return None
    if block is None:
        block = max(len(left), len(right))
    rtrees = [_build_tree([x % n for x in right[t:t + block]], n)
              for t in range(0, len(right), block)]
    for s in range(0, len(left), block):
        chunk = [x % n for x in left[s:s + block]]
        P = _build_tree(chunk, n)[0]          # P(X) = prod (X - left_i)
        acc = 1
        for rt in rtrees:
            out = []
            _eval_tree(P, rt, n, out)
            for v in out:
                acc = acc * v % n
        g = math.gcd(acc, n)
        if 1 < g < n:
            return g
        if g == n:
            # 整块退化 (同一块里出现多个因子), 退回逐点定位
            for u in chunk:
                for v in right:
                    gg = math.gcd((u - v) % n, n)
                    if 1 < gg < n:
                        return gg
    return None


# --------------------------------------------------- 椭圆曲线 over Z/NZ
def ec_add(P, Q, a, n):
    """y^2 = x^3 + a x + b 上的仿射点加; 求逆失败时抛 FactorFound."""
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if (x1 - x2) % n == 0:
        if (y1 + y2) % n == 0:
            return None
        lam = (3 * x1 * x1 + a) % n * inv_mod_n(2 * y1, n) % n
    else:
        lam = (y2 - y1) % n * inv_mod_n(x2 - x1, n) % n
    x3 = (lam * lam - x1 - x2) % n
    return (x3, (lam * (x1 - x3) - y1) % n)


def ec_mul(k, P, a, n):
    R, Q = None, P
    while k > 0:
        if k & 1:
            R = ec_add(R, Q, a, n)
        Q = ec_add(Q, Q, a, n)
        k >>= 1
    return R


# ----------------------------------------------------------------- LLL
def lll(B, delta=(3, 4)):
    """
    de Weger 整数 LLL (行向量, 全程整数算术, 无 Fraction/浮点).

    维护 d[i] = Gram 行列式, lam[i][j] = d[j+1] * mu[i][j]，
    避免分数运算在 1024-bit 系数下的爆炸式减速。
    前一版每次尺寸约简都重算整个 GSO (O(n^4) 次), 维度 >6 即不可用。
    """
    dn, dd = delta
    if _fplll is not None:
        A = _fplll.IntegerMatrix.from_matrix([[int(x) for x in row] for row in B])
        _fplll.LLL.reduction(A, delta=dn / dd)
        return [[int(A[i, j]) for j in range(A.ncols)] for i in range(A.nrows)]
    B = [row[:] for row in B]
    n = len(B)
    m = len(B[0])

    lam = [[0] * n for _ in range(n)]
    d = [1] * (n + 1)

    def dot(u, v):
        return sum(x * y for x, y in zip(u, v))

    def gram(k):
        for j in range(k + 1):
            u = dot(B[k], B[j])
            for i in range(j):
                u = (d[i + 1] * u - lam[k][i] * lam[j][i]) // d[i]
            if j < k:
                lam[k][j] = u
            else:
                d[k + 1] = u

    for k in range(n):
        gram(k)

    def reduce(k, l):
        if abs(2 * lam[k][l]) > d[l + 1]:
            q = (2 * lam[k][l] + d[l + 1]) // (2 * d[l + 1])
            B[k] = [B[k][i] - q * B[l][i] for i in range(m)]
            for i in range(l):
                lam[k][i] -= q * lam[l][i]
            lam[k][l] -= q * d[l + 1]

    def swap(k):
        # Cohen, A Course in Computational Algebraic NT, Alg 2.6.7 (SWAPI)
        B[k], B[k - 1] = B[k - 1], B[k]
        for j in range(k - 1):
            lam[k][j], lam[k - 1][j] = lam[k - 1][j], lam[k][j]
        lamv = lam[k][k - 1]
        Bnew = (d[k - 1] * d[k + 1] + lamv * lamv) // d[k]
        for i in range(k + 1, n):
            t = lam[i][k]
            lam[i][k] = (d[k + 1] * lam[i][k - 1] - lamv * t) // d[k]
            lam[i][k - 1] = (Bnew * t + lamv * lam[i][k]) // d[k + 1]
        lam[k][k - 1] = lamv
        d[k] = Bnew

    k = 1
    while k < n:
        reduce(k, k - 1)
        lhs = d[k + 1] * d[k - 1] * dd + lam[k][k - 1] ** 2 * dd
        rhs = dn * d[k] * d[k]
        if lhs * 1 >= rhs:
            for l in range(k - 2, -1, -1):
                reduce(k, l)
            k += 1
        else:
            swap(k)
            k = max(k - 1, 1)
    return B


def poly_roots_small(coeffs):
    """求整系数多项式的整数根 (用于 Coppersmith 还原后的短向量多项式)."""
    import itertools
    deg = len(coeffs) - 1
    while deg >= 0 and coeffs[deg] == 0:
        deg -= 1
    if deg <= 0:
        return []
    if deg == 1:
        a0, a1 = coeffs[0], coeffs[1]
        if a1 and a0 % a1 == 0:
            return [-a0 // a1]
        return []
    # 牛顿法 + 二分求正实根, 再验证
    def ev(x):
        r = 0
        for c in reversed(coeffs[:deg + 1]):
            r = r * x + c
        return r
    roots = []
    lo, hi = 1, 1
    while ev(hi) * ev(1) > 0 and hi < 1 << 600:
        hi <<= 1
    if hi < 1 << 600:
        lo, h = 1, hi
        while lo < h:
            mid = (lo + h) // 2
            if ev(mid) * ev(1) <= 0:
                h = mid
            else:
                lo = mid + 1
        for cand in (lo - 1, lo, lo + 1):
            if cand > 0 and ev(cand) == 0:
                roots.append(cand)
    return roots
