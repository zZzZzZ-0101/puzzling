"""
puzzle_solve.py — 三层级联 puzzle 的参考解题器

只读 challenge.json (公开卷面), 不碰 solution.json。
每层: 分解 N -> 得 phi -> RSA 解密 -> 用明文解封下一层。
"""
import json, hashlib, time, sys
from ctflib import is_prime
import variant6, variant7, variant9
from puzzle_gen import keystream


def unmask(hexblob, seed_int):
    raw = bytes.fromhex(hexblob)
    ks = keystream(seed_int, len(raw))
    return json.loads(bytes(a ^ b for a, b in zip(raw, ks)).decode())


def rsa_dec(c, e, p, q):
    phi = (p - 1) * (q - 1)
    return pow(c, pow(e, -1, phi), p * q)


def main():
    ch = json.load(open("challenge.json"))
    T0 = time.time()

    # ---------------- Layer A : 变种 6
    A = ch["layerA"]
    N_A, e_A, c_A = int(A["N"]), int(A["e"]), int(A["c"])
    t0 = time.time()
    r = variant6.solve(N_A, d1_bits=16, verbose=False)
    if not r:
        print("Layer A 失败"); return 1
    pA, qA = r[0], r[1]
    assert pA * qA == N_A and is_prime(pA) and is_prime(qA)
    seed_B = rsa_dec(c_A, e_A, pA, qA)
    print("[Layer A] %.1fs  分解 N_A 成功 (d1=%d d2=%d), 解出 seed_B"
          % (time.time() - t0, r[2], r[3]), flush=True)

    # ---------------- Layer B : 变种 9
    B = unmask(ch["blobB"], seed_B)
    N_B, e_B, c_B, KB = int(B["N"]), int(B["e"]), int(B["c"]), B["K_bound"]
    print("[Layer B] 解封成功, N_B=%d bit, K_bound=2^%d"
          % (N_B.bit_length(), KB.bit_length() - 1), flush=True)
    t0 = time.time()
    r = variant9.solve(N_B, K_bound=KB, verbose=True)
    if not r:
        print("Layer B 失败"); return 1
    pB, qB = r
    assert pB * qB == N_B and is_prime(pB) and is_prime(qB)
    seed_C = rsa_dec(c_B, e_B, pB, qB)
    print("[Layer B] %.1fs  分解 N_B 成功, 解出 seed_C" % (time.time() - t0), flush=True)

    # ---------------- Layer C : 变种 7
    C = unmask(B["blobC"], seed_C)
    N_C, e_C, a_C, c_C, KC = (int(C["N"]), int(C["e"]), C["a"],
                              int(C["c"]), C["K_bound"])
    print("[Layer C] 解封成功, N_C=%d bit" % N_C.bit_length(), flush=True)
    t0 = time.time()
    r = variant7.solve(N_C, e_C, a_C, K_bound=KC, verbose=False)
    if not r:
        print("Layer C 失败"); return 1
    pC, qC = r
    assert pC * qC == N_C and is_prime(pC) and is_prime(qC)
    m = rsa_dec(c_C, e_C, pC, qC)
    flag = m.to_bytes((m.bit_length() + 7) // 8, "big")
    print("[Layer C] %.1fs  分解 N_C 成功" % (time.time() - t0), flush=True)
    print()
    print("FLAG = %s" % flag.decode(errors="replace"))
    print("总耗时 %.1fs" % (time.time() - T0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
