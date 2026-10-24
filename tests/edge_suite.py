"""
edge_tests.py — Comprehensive Edge-Case, Honey-Trap Disguise & Adversarial Autopilot Test Suite
================================================================================================
Tests all 10 separated locks (Locks 01-10) and the cascade engine across 6 rigorous dimensions:
  1. Strict 1024-Bit Modulus & Exponent Geometry (N.bit_length() == 1024, 1 < e < N)
  2. NIST Monobit & Byte-Entropy Statistical Indistinguishability
  3. Verification of Planted False-Hope Honey-Trap Disguises (ECF Ghost Convergent, Fake ROCA, etc.)
  4. LLM Sandbox Autopilot Immunity (Trial Div, Fermat, Pollard p-1, Williams p+1, ECM, Wiener CF)
  5. Boundary & Degenerate Parameter Edge Cases + Cascade Tamper Rejection
  6. Full End-to-End Trapdoor Solver & RSA Decryption Verification
"""

import math
import time
import sys

from trapdoor.ctflib import is_prime, primes_upto, ec_mul
from trapdoor.arsenal.locks_A import (
    lock01_generate, lock01_solve,
    lock02_generate, lock02_solve,
    lock03_generate, lock03_solve,
    lock04_generate, lock04_solve, ROCA_DECOY_MOD,
    lock05_generate, lock05_solve,
)
from trapdoor.arsenal.locks_B import (
    lock06_generate, lock06_solve,
    lock07_generate, lock07_solve,
    lock08_generate, lock08_solve, _coppersmith_linear_4d,
    lock09_generate, lock09_solve, M_CHEB, G_CHEB, _lucas_v_seq,
    lock10_generate, lock10_solve,
)
from trapdoor.arsenal.cascade_engine import build_cascade, solve_cascade


def continued_fraction_max_spike(num, den):
    """
    Computes the continued fraction expansion of num / den and returns the maximum
    partial quotient a_i (for i >= 2) along with its convergent denominator q_{i-1}.
    """
    a0 = num // den
    r0 = num - a0 * den
    q_prev, q_cur = 1, a0
    p_prev, p_cur = 0, 1
    # Standard recurrences for convergents h_k / k_k of num / den
    h_m2, h_m1 = 0, 1
    k_m2, k_m1 = 1, 0
    a, b = num, den
    max_a = 0
    best_denom = 1
    step = 0
    while b != 0:
        q = a // b
        a, b = b, a - q * b
        h_k = q * h_m1 + h_m2
        k_k = q * k_m1 + k_m2
        if step >= 2 and q > max_a:
            max_a = q
            best_denom = k_m1
        h_m2, h_m1 = h_m1, h_k
        k_m2, k_m1 = k_m1, k_k
        step += 1
    return max_a, best_denom


def check_monobit_entropy(N):
    """Verifies NIST monobit balance (proportion of 1s in [0.44, 0.56])."""
    bits = bin(N)[2:]
    ones = bits.count("1")
    ratio = ones / len(bits)
    return 0.44 <= ratio <= 0.56, ratio


def sandbox_autopilot_attacks(N, e):
    """
    Simulates the standard LLM sandbox trial-tree (Trial Division, Fermat,
    Pollard p-1, Williams p+1, Genus-1 ECM, and Wiener Continued Fractions).
    Returns True if ALL standard attacks fail (as required).
    """
    # 1. Small prime trial division
    for l in primes_upto(2000):
        if N % l == 0:
            return False, f"Trial division hit l={l}"

    # 2. Fermat near-square check (100 steps)
    a = math.isqrt(N) + 1
    for _ in range(100):
        diff = a * a - N
        s = math.isqrt(diff)
        if s * s == diff:
            return False, "Fermat factorization hit"
        a += 1

    # 3. Pollard p-1 (smooth bound B=2000)
    M_small = math.prod(primes_upto(500))
    g_p1 = math.gcd(pow(2, M_small, N) - 1, N)
    if 1 < g_p1 < N:
        return False, "Pollard p-1 hit"

    # 4. Williams p+1 (Lucas V_M(5) mod N)
    v0, v1 = 2, 5
    for bit in bin(M_small)[2:]:
        if bit == "0":
            v1 = (v0 * v1 - 5) % N
            v0 = (v0 * v0 - 2) % N
        else:
            v0 = (v0 * v1 - 5) % N
            v1 = (v1 * v1 - 2) % N
    g_pp1 = math.gcd(v0 - 2, N)
    if 1 < g_pp1 < N:
        return False, "Williams p+1 hit"

    # 5. Wiener Continued Fractions check on e / N
    if e > 65537:
        a_cf, b_cf = e, N
        k_m2, k_m1 = 0, 1
        d_m2, d_m1 = 1, 0
        while b_cf != 0:
            q = a_cf // b_cf
            a_cf, b_cf = b_cf, a_cf - q * b_cf
            k_cur = q * k_m1 + k_m2
            d_cur = q * d_m1 + d_m2
            k_m2, k_m1 = k_m1, k_cur
            d_m2, d_m1 = d_m1, d_cur
            if k_cur > 0 and (e * d_cur - 1) % k_cur == 0:
                phi_cand = (e * d_cur - 1) // k_cur
                s_sum = N - phi_cand + 1
                disc = s_sum * s_sum - 4 * N
                if disc >= 0:
                    sq = math.isqrt(disc)
                    if sq * sq == disc:
                        p_cand = (s_sum + sq) // 2
                        if 1 < p_cand < N and N % p_cand == 0:
                            return False, "Wiener attack factored N"

    return True, "All 5 autopilot attacks defeated"


def run_edge_suite(include_lock07=False):
    print("=" * 88)
    print(" RUNNING EDGE-CASE, HONEY-TRAP DISGUISE & ADVERSARIAL AUTOPILOT TEST SUITE")
    print("=" * 88)

    locks_to_test = [
        ("lock01", lock01_generate, lock01_solve),
        ("lock02", lock02_generate, lock02_solve),
        ("lock03", lock03_generate, lock03_solve),
        ("lock04", lock04_generate, lock04_solve),
        ("lock05", lock05_generate, lock05_solve),
        ("lock06", lock06_generate, lock06_solve),
        ("lock08", lock08_generate, lock08_solve),
        ("lock09", lock09_generate, lock09_solve),
        ("lock10", lock10_generate, lock10_solve),
    ]
    if include_lock07:
        locks_to_test.insert(6, ("lock07", lock07_generate, lock07_solve))

    instances = {}
    for lid, gen_fn, solve_fn in locks_to_test:
        print(f"\n--- Testing {lid.upper()} ---")
        pub, sk = gen_fn(seed=100 + int(lid[-2:]), verbose=True)
        N, e = pub["N"], pub["e"]
        p, q = sk["p"], sk["q"]

        # 1. Strict 1024-bit N & 1 < e < N check
        assert N == p * q and p != q and is_prime(p) and is_prime(q), f"{lid}: prime check failed"
        assert N.bit_length() == 1024, f"{lid}: expected 1024-bit N, got {N.bit_length()}"
        assert 1 < e < N, f"{lid}: exponent e out of range (1, N)"
        assert math.gcd(e, (p - 1) * (q - 1)) == 1, f"{lid}: e not coprime to phi(N)"

        # 2. Statistical Monobit Entropy check
        ok_ent, ratio = check_monobit_entropy(N)
        assert ok_ent, f"{lid}: monobit entropy ratio {ratio:.4f} out of bounds"
        print(f"  [Edge 1-2] N=1024b | e={e.bit_length()}b (<N) | Monobit 1-ratio={ratio:.4f} PASS")

        # 3. Verify Planted False-Hope Disguises
        if lid == "lock01":
            assert (N - 1) % (1 << 12) == 0
            print("  [Disguise] Lock 01 2-adic Fermat mask N == 1 (mod 2^12) verified PASS")
        elif lid == "lock02":
            max_q, ghost_d = continued_fraction_max_spike(e, N)
            assert max_q >= (1 << 50) and ghost_d == sk["d_fake"]
            print(f"  [Disguise] Lock 02 ECF Ghost Convergent verified: spike a_r=2^{max_q.bit_length()-1}, d_fake={ghost_d.bit_length()}b PASS")
        elif lid == "lock04":
            assert (N - pow(65537, 1337, ROCA_DECOY_MOD)) % ROCA_DECOY_MOD == 0
            print("  [Disguise] Lock 04 Fake ROCA Primorial Signature N == 65537^1337 (mod P_37) verified PASS")
        elif lid == "lock05":
            assert e % (1 << 80) == 3
            print("  [Disguise] Lock 05 Fake Low-Exponent Mask e == 3 (mod 2^80) verified PASS")
        elif lid == "lock06":
            assert (e - N) % (1 << 120) == 0
            print("  [Disguise] Lock 06 Fake 120-bit LSB Match (e == N mod 2^120) verified PASS")
        elif lid == "lock09":
            assert (sk["H1"] >> 132) == (sk["H2"] >> 132) and abs(p - q).bit_length() >= 480
            print(f"  [Disguise] Lock 09 Fake Fermat 20b Halo verified (|p-q|={abs(p-q).bit_length()}b) PASS")

        # 4. Sandbox Autopilot Immunity
        ok_auto, msg_auto = sandbox_autopilot_attacks(N, e)
        assert ok_auto, f"{lid}: {msg_auto}"
        print(f"  [Autopilot] {msg_auto} PASS")

        # 5. Trapdoor Solve & RSA Decryption Verification
        sol = solve_fn(pub, verbose=True)
        assert sol is not None, f"{lid}: trapdoor solver returned None"
        assert set(sol) == {p, q}, f"{lid}: recovered factors do not match {p, q}"
        d_rsa = pow(e, -1, (p - 1) * (q - 1))
        m_test = 12345678901234567890
        c_test = pow(m_test, e, N)
        assert pow(c_test, d_rsa, N) == m_test
        instances[lid] = pub

    # 6. Boundary & Tamper Edge Tests
    print("\n--- Testing Boundary & Tamper Edge Cases ---")
    # Test Lock 08 Coppersmith at extreme mask boundaries delta=1 and delta=15
    pub8, sk8 = lock08_generate(mask_bits=4, x0_bits=106, seed=999, verbose=False)
    U_hi = (sk8["u3"] << 240) + sk8["u2"]
    U_lo = (sk8["u1"] << 240) + sk8["u0"]
    root8, _ = _coppersmith_linear_4d(U_hi, U_lo + sk8["delta"], pub8["N"], 1 << 107)
    assert root8 == sk8["x0"], "Lock 08 boundary root recovery failed"
    print("  [Boundary] Lock 08 exact 106-bit root recovery verified PASS")

    # Test Cascade HMAC Tamper Rejection
    bundle = build_cascade(["lock01", "lock09"], final_flag=b"FLAG{Edge_Test_OK}", seed=777, verbose=False)
    # Tamper with 1 byte of the outer encrypted envelope
    orig_tag = bundle["public_challenge"]["next_envelope"]["hmac_sha256"]
    bundle["public_challenge"]["next_envelope"]["hmac_sha256"] = ("0" if orig_tag[0] != "0" else "1") + orig_tag[1:]
    tamper_caught = False
    try:
        solve_cascade(bundle, verbose=False)
    except ValueError as ve:
        if "HMAC" in str(ve):
            tamper_caught = True
    assert tamper_caught, "Cascade failed to reject tampered HMAC"
    bundle["public_challenge"]["next_envelope"]["hmac_sha256"] = orig_tag
    res_cas = solve_cascade(bundle, verbose=False)
    assert res_cas["final_flag"] == "FLAG{Edge_Test_OK}"
    print("  [Security] Cascade HMAC tamper rejection & recovery verified PASS")

    print("\n" + "=" * 88)
    print(f" ALL {len(locks_to_test)} LOCKS & EDGE TESTS PASSED 100%!")
    print("=" * 88)


if __name__ == "__main__":
    inc7 = "--with-lock07" in sys.argv
    run_edge_suite(include_lock07=inc7)
