"""
cascade_engine.py - Universal Pluggable Cryptographic Lock Registry & Multi-Layer Cascade Engine
================================================================================================

Provides:
1. LOCK_REGISTRY: A unified registry of all 10 separated mathematical trapdoor locks (Locks 01-10).
   Each lock can be run standalone (`generate_single_lock` / `solve_single_lock`) or composed into
   an arbitrary multi-layer Matryoshka cascade (`build_cascade` / `solve_cascade`).
2. Zero-Leakage Key Derivation Envelope:
   Every layer exposes ONLY standard RSA parameters `(N, e, c)`.
   The secret key `K_{i}` of layer `i` is derived deterministically from the recovered unsorted
   prime set `{p_i, q_i}` of layer `i`:
       p_lo, p_hi = min(p_i, q_i), max(p_i, q_i)
       K_{i} = SHA256("CASCADE_V3_KEY|" || layer_id || "|" || str(p_lo) || "|" || str(p_hi))
   and decrypts the next inner layer's payload via authenticated SHA256-CTR stream cipher + HMAC-SHA256.
"""

import hashlib
import hmac
import json
import time
from typing import Dict, Any, List, Optional

from trapdoor.arsenal.locks_A import (
    lock01_generate, lock01_solve,
    lock02_generate, lock02_solve,
    lock03_generate, lock03_solve,
    lock04_generate, lock04_solve,
    lock05_generate, lock05_solve,
)
from trapdoor.arsenal.locks_B import (
    lock06_generate, lock06_solve,
    lock07_generate, lock07_solve,
    lock08_generate, lock08_solve,
    lock09_generate, lock09_solve,
    lock10_generate, lock10_solve,
)


LOCK_REGISTRY: Dict[str, Dict[str, Any]] = {
    "lock01": {
        "id": "lock01",
        "name": "Phi_6(p) Cyclotomic Ring Z_N[zeta_7] Galois-Frobenius Torus T_6 + 2-Adic Fermat Decoy",
        "surface": "(N, e=65537, c)",
        "algebraic_group": "T_6(F_p) subset (Z_N[x]/(Phi_7(x)))^* of order p^2 - p + 1",
        "trapdoor_type": "Projective Mobius Torus Entanglement d2*(N-3) = d1*(2N+5) (mod C_6) + Fake N=1 (mod 2^12)",
        "generate": lock01_generate,
        "solve": lock01_solve,
    },
    "lock02": {
        "id": "lock02",
        "name": "Phi_4(p) Projective Redei Conic P^1_Delta(Z_N[i]) + ECF Ghost Convergent Honey-Trap",
        "surface": "(N, e, c)",
        "algebraic_group": "C_Delta(F_p^2) of order Phi_4(p) = p^2 + 1 with Delta = 1 + 2i",
        "trapdoor_type": "Twisted Bilinear Redei d2*(e+3N) = d1*(2e+5N) (mod C_4) + Legendre ECF Ghost d_fake (196b)",
        "generate": lock02_generate,
        "solve": lock02_solve,
    },
    "lock03": {
        "id": "lock03",
        "name": "Phi_8(p) Octic Cyclotomic Torus P^1_t(R_4) over Z_N[t]/(t^4-2t^2+5)",
        "surface": "(N, e, c)",
        "algebraic_group": "T_8(F_p) of order Phi_8(p) = p^4 + 1 (332b x 692b unbalanced 1024b N)",
        "trapdoor_type": "Octic Shifted Entanglement d2*(e+7N) = d1*(3e+11N) (mod C_8) + Subfield Adjoint Batch Inverse",
        "generate": lock03_generate,
        "solve": lock03_solve,
    },
    "lock04": {
        "id": "lock04",
        "name": "Discriminant D = -7 (j = -3375) Conductor f=2 CM Curve + Fake ROCA Primorial Honey-Trap",
        "surface": "(N, e=65537, c)",
        "algebraic_group": "E_{-7}(F_p): y^2 = x^3 - 35*w^2*x - 98*w^3 (only 2 twists over F_p)",
        "trapdoor_type": "Projective Mobius CM d2*(N-2) = d1*(2N+3) (mod C_{-7}) + Fake ROCA N = 65537^1337 (mod P_37)",
        "generate": lock04_generate,
        "solve": lock04_solve,
    },
    "lock05": {
        "id": "lock05",
        "name": "Genus-2 Hyperelliptic Curve Jac(y^2 = x^5 + 8) + Fake Low-Exponent Mask (e = 3 mod 2^80)",
        "surface": "(N, e, c)",
        "algebraic_group": "Jac(C)(F_p) of exponent p^2 + 1 via Cantor Mumford Divisors",
        "trapdoor_type": "Quadratic Self-Referential Jacobian d2*(e+N^2) = d1*(2e+N) (mod C_jac) + Mumford Discriminant",
        "generate": lock05_generate,
        "solve": lock05_solve,
    },
    "lock06": {
        "id": "lock06",
        "name": "12D Non-Commutative Quaternion Algebra H_{-1,-1}(R_3) + Fake 120b LSB Match (e = N mod 2^120)",
        "surface": "(N, e, c)",
        "algebraic_group": "H(R_3)^* / R_3^* where R_3 = Z_N[t]/(t^3 - 2)",
        "trapdoor_type": "Hilbert-90 & Skolem-Noether d2*(e-2N) = d1*(3e+4N) (mod C_6) + Fake 120-Bit LSB Match",
        "generate": lock06_generate,
        "solve": lock06_solve,
    },
    "lock07": {
        "id": "lock07",
        "name": "Prime-Order Companion Matrix Cubic Lucas Sequence SL_3(Z/NZ) Dual-Trace Lock",
        "surface": "(N, e, c)",
        "algebraic_group": "F_p[M_{P,Q}]^* / F_p^* of 1024-bit PRIME order M_3 = p^2 + p + 1 (0% smoothness)",
        "trapdoor_type": "Twisted Bilinear Matrix Exponent d2*(e+2N) = d1*(3e+5N) (mod M_3) + Dual-Trace Tr(A)+3Tr(A^2)",
        "generate": lock07_generate,
        "solve": lock07_solve,
    },
    "lock08": {
        "id": "lock08",
        "name": "Two-Stage 4D Cubic Orthogonal Lattice + Base-2^240 Dyadic Coppersmith",
        "surface": "(N, e, c)",
        "algebraic_group": "4D Orthogonal Lattice L^perp subset Z^4 + 4D Linear Divisor Lattice",
        "trapdoor_type": "2-Stage Cascade: 4D LLL on e + Base-2^240 Folded Coppersmith (m=2, t=2, 106b root)",
        "generate": lock08_generate,
        "solve": lock08_solve,
    },
    "lock09": {
        "id": "lock09",
        "name": "Symmetric Chebyshev / Lucas-V Product-to-Sum SETUP + Fake Fermat 20b Halo",
        "surface": "(N, e=65537, c)",
        "algebraic_group": "Chebyshev Polynomial Ring T_n / Lucas V_n mod Phi_6(2^180)",
        "trapdoor_type": "V_a(7)*V_b(7) = V_{a+b}(7) + V_{|a-b|}(7) mod M + Fake Fermat 20b MSB Match (|p-q|~2^491)",
        "generate": lock09_generate,
        "solve": lock09_solve,
    },
    "lock10": {
        "id": "lock10",
        "name": "Phi_12(p) Dodecic Cyclotomic Ring Z_N[zeta_13] 4-Term Frobenius Torus",
        "surface": "(N, e, c)",
        "algebraic_group": "T_12(F_p) subset (Z_N[x]/(Phi_13(x)))^* of order Phi_12(p) = p^4 - p^2 + 1",
        "trapdoor_type": "Dodecic Galois-Twisted d2*(e+4N) = d1*(5e+9N) (mod C_12) + 4-Term Projection Psi_12",
        "generate": lock10_generate,
        "solve": lock10_solve,
    },
}


def _derive_cascade_key(layer_id: str, p: int, q: int) -> bytes:
    p_lo, p_hi = (p, q) if p < q else (q, p)
    material = f"CASCADE_V3_KEY|{layer_id}|{p_lo}|{p_hi}".encode("utf-8")
    return hashlib.sha256(material).digest()


def _stream_xor(key: bytes, nonce: bytes, data: bytes) -> bytes:
    out = bytearray(len(data))
    block_idx = 0
    offset = 0
    while offset < len(data):
        ks = hashlib.sha256(key + nonce + block_idx.to_bytes(8, "big")).digest()
        chunk_len = min(32, len(data) - offset)
        for i in range(chunk_len):
            out[offset + i] = data[offset + i] ^ ks[i]
        offset += chunk_len
        block_idx += 1
    return bytes(out)


def _encrypt_envelope(key: bytes, plaintext_dict: Dict[str, Any]) -> Dict[str, str]:
    raw = json.dumps(plaintext_dict, sort_keys=True).encode("utf-8")
    nonce = hashlib.sha256(key + b"NONCE_V3" + raw[:32]).digest()[:16]
    ct = _stream_xor(key, nonce, raw)
    tag = hmac.new(key, nonce + ct, hashlib.sha256).hexdigest()
    return {
        "nonce": nonce.hex(),
        "ciphertext": ct.hex(),
        "hmac_sha256": tag,
    }


def _decrypt_envelope(key: bytes, envelope: Dict[str, str]) -> Dict[str, Any]:
    nonce = bytes.fromhex(envelope["nonce"])
    ct = bytes.fromhex(envelope["ciphertext"])
    expected_tag = hmac.new(key, nonce + ct, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_tag, envelope["hmac_sha256"]):
        raise ValueError("Cascade envelope HMAC verification failed (wrong prime factors or corrupted state).")
    raw = _stream_xor(key, nonce, ct)
    return json.loads(raw.decode("utf-8"))


def generate_single_lock(
    lock_id: str,
    flag_bytes: bytes = b"FLAG{single_lock_test}",
    seed: Optional[int] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    if lock_id not in LOCK_REGISTRY:
        raise KeyError(f"Unknown lock_id '{lock_id}'. Available: {sorted(LOCK_REGISTRY.keys())}")
    entry = LOCK_REGISTRY[lock_id]
    t0 = time.time()
    pub, sk = entry["generate"](seed=seed, verbose=verbose)
    gen_time = time.time() - t0

    N = int(pub["N"])
    e = int(pub["e"])
    m_int = int.from_bytes(flag_bytes, "big")
    if m_int >= N:
        raise ValueError("Plaintext flag_bytes integer exceeds modulus N.")
    c = pow(m_int, e, N)

    pub_with_c = dict(pub)
    pub_with_c["c"] = c
    return {
        "lock_id": lock_id,
        "pub": pub_with_c,
        "priv": sk,
        "gen_time_sec": round(gen_time, 4),
    }


def solve_single_lock(
    lock_id: str,
    pub: Dict[str, int],
    verbose: bool = False,
) -> Dict[str, Any]:
    if lock_id not in LOCK_REGISTRY:
        raise KeyError(f"Unknown lock_id '{lock_id}'. Available: {sorted(LOCK_REGISTRY.keys())}")
    entry = LOCK_REGISTRY[lock_id]
    t0 = time.time()
    res = entry["solve"](pub, verbose=verbose)
    solve_time = time.time() - t0
    if res is None:
        raise RuntimeError(f"Solver for {lock_id} failed to factor N.")
    p, q = int(res[0]), int(res[1])
    N = int(pub["N"])
    e = int(pub["e"])
    c = int(pub.get("c", 0))
    phi = (p - 1) * (q - 1)
    d = pow(e, -1, phi)
    m_int = pow(c, d, N)
    blen = (m_int.bit_length() + 7) // 8
    pt_bytes = m_int.to_bytes(max(1, blen), "big")
    return {
        "p": p,
        "q": q,
        "d": d,
        "plaintext_bytes": pt_bytes,
        "solve_time_sec": round(solve_time, 4),
    }


def build_cascade(
    lock_sequence: List[str],
    final_flag: bytes = b"FLAG{Matryoshka_10_Locks_Arsenal_Mastered}",
    base_seed: int = 20260501,
    seed: Optional[int] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    if seed is not None:
        base_seed = seed
    if not lock_sequence:
        raise ValueError("lock_sequence must contain at least one lock_id.")
    for lid in lock_sequence:
        if lid not in LOCK_REGISTRY:
            raise KeyError(f"Unknown lock_id '{lid}' in sequence.")

    layers_raw: List[Dict[str, Any]] = []
    total_layers = len(lock_sequence)

    for idx, lid in enumerate(lock_sequence):
        is_last = (idx == total_layers - 1)
        layer_flag = (
            final_flag
            if is_last
            else f"STEP_{idx + 1}_OF_{total_layers}_UNLOCKED[{lid}]".encode("utf-8")
        )
        layer_seed = base_seed + idx * 1009
        gen_data = generate_single_lock(lid, flag_bytes=layer_flag, seed=layer_seed, verbose=verbose)
        layers_raw.append({
            "layer_index": idx,
            "lock_id": lid,
            "pub": gen_data["pub"],
            "priv": gen_data["priv"],
            "gen_time_sec": gen_data["gen_time_sec"],
        })

    current_payload: Dict[str, Any] = {
        "layer_index": total_layers - 1,
        "lock_id": layers_raw[-1]["lock_id"],
        "pub": layers_raw[-1]["pub"],
        "next_envelope": None,
    }

    for idx in range(total_layers - 2, -1, -1):
        outer_layer = layers_raw[idx]
        key = _derive_cascade_key(
            outer_layer["lock_id"],
            outer_layer["priv"]["p"],
            outer_layer["priv"]["q"],
        )
        encrypted_next = _encrypt_envelope(key, current_payload)
        current_payload = {
            "layer_index": idx,
            "lock_id": outer_layer["lock_id"],
            "pub": outer_layer["pub"],
            "next_envelope": encrypted_next,
        }

    return {
        "cascade_version": "3.0",
        "total_layers": total_layers,
        "lock_sequence": lock_sequence,
        "public_challenge": current_payload,
        "generation_metrics": [
            {
                "layer_index": item["layer_index"],
                "lock_id": item["lock_id"],
                "N_bits": item["pub"]["N"].bit_length(),
                "e_bits": item["pub"]["e"].bit_length(),
                "gen_time_sec": item["gen_time_sec"],
            }
            for item in layers_raw
        ],
    }


def solve_cascade(cascade_bundle: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    current = cascade_bundle["public_challenge"]
    trace: List[Dict[str, Any]] = []
    t_start = time.time()

    while current is not None:
        lid = current["lock_id"]
        pub = current["pub"]
        layer_idx = current["layer_index"]

        solved = solve_single_lock(lid, pub, verbose=verbose)
        p, q = solved["p"], solved["q"]
        assert p * q == pub["N"], f"Layer {layer_idx} ({lid}) factorization check failed!"

        msg_bytes = solved["plaintext_bytes"]
        trace.append({
            "layer_index": layer_idx,
            "lock_id": lid,
            "p_bits": p.bit_length(),
            "q_bits": q.bit_length(),
            "solve_time_sec": solved["solve_time_sec"],
            "recovered_message": msg_bytes.decode("utf-8", errors="replace"),
        })

        next_env = current.get("next_envelope")
        if next_env is None:
            break

        key = _derive_cascade_key(lid, p, q)
        current = _decrypt_envelope(key, next_env)

    total_solve_time = round(time.time() - t_start, 4)
    return {
        "total_layers_solved": len(trace),
        "total_solve_time_sec": total_solve_time,
        "final_flag": trace[-1]["recovered_message"] if trace else "",
        "layer_trace": trace,
    }
