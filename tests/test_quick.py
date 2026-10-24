"""
Quick end-to-end checks for every registered lock and the cascade engine.

Each lock runs at a small search bound with a fixed seed, so the whole file
finishes in a few minutes. Run with:  python3 -m pytest -q tests/test_quick.py
"""

import json

import pytest

from trapdoor.ctflib import BACKEND
from trapdoor.arsenal.cascade_engine import (
    LOCK_REGISTRY,
    build_cascade,
    generate_single_lock,
    solve_cascade,
    solve_single_lock,
)

SMALL = {
    "variant5": {"mask_bits": 1},
    "variant6": {"d1_bits": 8},
    "variant7": {"K_bound": 1 << 9},
    "variant9": {"K_bound": 1 << 9},
    "lock08": {},
}


@pytest.mark.parametrize("lock_id", sorted(LOCK_REGISTRY))
def test_lock_roundtrip(lock_id):
    if lock_id == "variant5" and not BACKEND["fpylll"]:
        pytest.skip("variant5 needs fpylll")
    flag = f"FLAG{{quick_{lock_id}}}".encode()
    gen = generate_single_lock(lock_id, flag_bytes=flag, seed=4242,
                               **SMALL.get(lock_id, {"K_bound": 1 << 9}))
    assert set(gen["pub"]) == {"N", "e", "c"}
    assert gen["pub"]["N"].bit_length() >= 1023
    sol = solve_single_lock(lock_id, gen["pub"], **gen["params"])
    assert {sol["p"], sol["q"]} == {gen["priv"]["p"], gen["priv"]["q"]}
    assert sol["plaintext_bytes"] == flag


def test_cascade_public_surface_and_roundtrip():
    bundle = build_cascade(["lock09", "lock01", "lock02"], final_flag=b"FLAG{quick_cascade}", seed=99,
                           layer_params=[{"K_bound": 1 << 9}] * 3)
    public = bundle["public"]
    text = json.dumps(public)
    assert "lock" not in text and "K_bound" not in text
    layer = public["challenge"]
    assert set(layer) == {"N", "e", "c", "next"}
    assert set(layer["next"]) == {"nonce", "ciphertext", "hmac_sha256"}

    with pytest.raises(ValueError):
        solve_cascade(public)  # the reference solver needs the private manifest

    res = solve_cascade(public, bundle["private"])
    assert res["final_flag"] == "FLAG{quick_cascade}"
    assert [t["lock_id"] for t in res["layer_trace"]] == ["lock09", "lock01", "lock02"]
