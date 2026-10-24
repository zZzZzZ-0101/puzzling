"""
variant_locks.py - V2.1 variants 5/6/7/9 behind the arsenal lock interface
==========================================================================

Every lock in LOCK_REGISTRY follows the same contract:

    generate(seed=None, verbose=True, **params) -> (pub, sk)
        pub = {"N": N, "e": e}            # the only public values
        sk  = {"p": p, "q": q, ..., "params": {...}}
    solve(pub, verbose=True, **params) -> (p, q) or None

`sk["params"]` holds the search bounds the reference solver needs. They are
solver knowledge, never part of the published challenge.
"""

from trapdoor.ctflib import BACKEND, primes_upto
from trapdoor.variants import variant5, variant6, variant7, variant9


# ---------------------------------------------------------------- variant 9
def v9_generate(K_bound=1 << 15, seed=None, verbose=True):
    N, e, sk = variant9.generate(K_bound, seed=seed, verbose=verbose)
    sk["params"] = {"K_bound": K_bound}
    return {"N": N, "e": e}, sk


def v9_solve(pub, verbose=True, K_bound=1 << 15):
    return variant9.solve(int(pub["N"]), K_bound=K_bound, verbose=verbose)


# ---------------------------------------------------------------- variant 7
def v7_generate(K_bound=1 << 13, seed=None, verbose=True):
    N, e, a, sk = variant7.generate(K_bound, seed=seed, verbose=verbose)
    # `a` is the least cubic non-residue mod p. It used to be published; it is
    # now withheld, so the solver has to search for it.
    sk["a"] = a
    sk["params"] = {"K_bound": K_bound}
    return {"N": N, "e": e}, sk


def v7_solve(pub, verbose=True, K_bound=1 << 13, a_bound=64):
    N, e = int(pub["N"]), int(pub["e"])
    # The least non-residue is always prime, and with the right `a` the first
    # base point almost always hits, so two trials per candidate are enough.
    for a in primes_upto(a_bound):
        res = variant7.solve(N, e, a, K_bound=K_bound, max_trial=2, verbose=verbose)
        if res:
            return res
    return None


# ---------------------------------------------------------------- variant 6
def v6_generate(d1_bits=16, seed=None, verbose=True):
    N, e, sk = variant6.generate(d1_bits=d1_bits, seed=seed, verbose=verbose)
    sk["params"] = {"d1_bits": d1_bits}
    return {"N": N, "e": e}, sk


def v6_solve(pub, verbose=True, d1_bits=16):
    res = variant6.solve(int(pub["N"]), d1_bits=d1_bits, verbose=verbose)
    return (res[0], res[1]) if res else None


# ---------------------------------------------------------------- variant 5
def v5_generate(mask_bits=4, x0_bits=104, seed=None, verbose=True):
    N, e, sk = variant5.generate(mask_bits=mask_bits, x0_bits=x0_bits, seed=seed, verbose=verbose)
    sk["params"] = {"mask_bits": mask_bits, "x0_bits": x0_bits}
    return {"N": N, "e": e}, sk


def v5_solve(pub, verbose=True, mask_bits=4, x0_bits=104):
    if not BACKEND["fpylll"]:
        # 20-dim lattices with ~2^2500 entries: pure-Python LLL takes hours per delta.
        raise RuntimeError("variant5 needs fpylll (pip install fpylll cysignals)")
    res = variant5.solve(int(pub["N"]), int(pub["e"]), mask_bits=mask_bits,
                         x0_bits=x0_bits, verbose=verbose)
    return (res[0], res[1]) if res else None
