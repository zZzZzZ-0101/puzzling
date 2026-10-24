"""
puzzle_gen.py — 三层级联陷门 puzzle 生成器

[Legacy] V2.1 格式 (XOR keystream 封装), 仅为复现已发布的 challenges/tri-cascade 而保留。
新题请用 trapdoor/v4.py (HMAC 信封, 统一 LOCK_REGISTRY)。

结构 (真级联, 非 XOR 胶水):
    Layer A  变种 6  隐藏共享基 M = 3^186 + d1, 残数不回绕
             -> 解出 p_A -> phi(N_A) -> RSA 解密 c_A -> seed_B
    Layer B  变种 9  纯素数阶复乘曲线跨模自指碰撞 (0% 平滑度)
             seed_B 解封 Layer B 的公开参数 (不解 A 就读不到 N_B)
             -> 解出 p_B -> RSA 解密 c_B -> seed_C
    Layer C  变种 7  三次 Pell 曲面双轨交叉指数碰撞
             seed_C 解封 Layer C 的公开参数
             -> 解出 p_C -> RSA 解密 c_C -> FLAG

每层的"下一层解封密钥"是该层 RSA 密文的明文, 所以层与层之间是密码学意义上的
严格依赖, 而不是把三道独立题装进一个压缩包。
"""
import json, hashlib, random, time, argparse, sys, os

from trapdoor.variants import variant6, variant7, variant9

FLAG = b"flag{tri_cascade_CM_prime_order_torus_and_hidden_shared_base}"


def keystream(seed_int, nbytes):
    out, ctr = b"", 0
    s = str(seed_int).encode()
    while len(out) < nbytes:
        out += hashlib.sha256(s + b"|" + str(ctr).encode()).digest()
        ctr += 1
    return out[:nbytes]


def mask(obj, seed_int):
    """把一层的公开参数序列化后用 seed 派生的流掩码, 输出 hex."""
    raw = json.dumps(obj, sort_keys=True).encode()
    ks = keystream(seed_int, len(raw))
    return bytes(a ^ b for a, b in zip(raw, ks)).hex()


def rsa_enc(m_int, e, N):
    assert 1 < m_int < N
    return pow(m_int, e, N)


def build(layerB_bits=16, seed=None, verbose=True):
    if seed is not None:
        random.seed(seed)
    t0 = time.time()

    # ---------------- Layer C (最内层, 先造, 因为要被上层封起来)
    seed_C = random.getrandbits(256) | (1 << 255)
    N_C, e_C, a_C, skC = variant7.generate(1 << 13, seed=random.randrange(1 << 30),
                                           verbose=False)
    phiC = (skC["p"] - 1) * (skC["q"] - 1)
    flag_int = int.from_bytes(FLAG, "big")
    assert flag_int < N_C
    c_C = rsa_enc(flag_int, e_C, N_C)
    layerC_pub = {"N": str(N_C), "e": str(e_C), "a": a_C, "c": str(c_C),
                  "K_bound": 1 << 13}
    blobC = mask(layerC_pub, seed_C)
    if verbose:
        print("  [Layer C] 变种 7 三次 Pell  N=%d bit  已封" % N_C.bit_length())

    # ---------------- Layer B
    seed_B = random.getrandbits(256) | (1 << 255)
    N_B, e_B, skB = variant9.generate(1 << layerB_bits,
                                      seed=random.randrange(1 << 30), verbose=False)
    c_B = rsa_enc(seed_C, e_B, N_B)
    layerB_pub = {"N": str(N_B), "e": str(e_B), "c": str(c_B),
                  "K_bound": 1 << layerB_bits, "blobC": blobC}
    blobB = mask(layerB_pub, seed_B)
    if verbose:
        print("  [Layer B] 变种 9 纯素数阶 CM  N=%d bit  K=2^%d  已封"
              % (N_B.bit_length(), layerB_bits))

    # ---------------- Layer A (最外层, 明文公开)
    N_A, e_A, skA = variant6.generate(d1_bits=16, seed=random.randrange(1 << 30),
                                      verbose=False)
    c_A = rsa_enc(seed_B, e_A, N_A)
    challenge = {
        "title": "Tri-Cascade Trapdoor Challenge",
        "layerA": {"N": str(N_A), "e": str(e_A), "c": str(c_A)},
        "blobB": blobB,
        "note": "Each layer's RSA plaintext unmasks the next layer. Start at layerA.",
    }
    solution = {
        "flag": FLAG.decode(),
        "A": {"p": str(skA["p"]), "d1": skA["d1"], "d2": skA["d2"]},
        "B": {"p": str(skB["p"]), "M_p": str(skB["M_p"]),
              "d1": skB["d1"], "d2": skB["d2"]},
        "C": {"p": str(skC["p"]), "d1": skC["d1"], "d2": skC["d2"]},
        "seed_B": str(seed_B), "seed_C": str(seed_C),
    }
    if verbose:
        print("  [Layer A] 变种 6 隐藏共享基  N=%d bit  明文公开" % N_A.bit_length())
        print("  生成完毕 %.1fs" % (time.time() - t0))
    return challenge, solution


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bbits", type=int, default=16, help="Layer B 的 K_bound = 2^bbits")
    ap.add_argument("--seed", type=int, default=1023)
    ap.add_argument("--outdir", default=os.path.join("challenges", "tri-cascade"))
    a = ap.parse_args()
    ch, so = build(layerB_bits=a.bbits, seed=a.seed)
    os.makedirs(a.outdir, exist_ok=True)
    json.dump(ch, open(os.path.join(a.outdir, "challenge.json"), "w"), indent=1)
    json.dump(so, open(os.path.join(a.outdir, "solution.json"), "w"), indent=1)
    print("写出 %s/challenge.json (公开卷面) 与 solution.json (出题人私有)" % a.outdir)
