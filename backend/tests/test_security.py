from app.core.security import hash_password, verify_password


def test_argon2id_hash_and_verify_password() -> None:
    password = "CorrectHorseBatteryStaple!"
    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != password
    assert first_hash != second_hash
    assert first_hash.startswith("$argon2id$")
    assert verify_password(password, first_hash)
    assert not verify_password("wrong-password", first_hash)
    assert not verify_password(password, "not-a-valid-hash")
