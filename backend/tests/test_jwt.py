from datetime import timedelta

import jwt
import pytest

from app.core.security import (
    TokenExpiredError,
    TokenInvalidError,
    create_access_token,
    create_refresh_token,
    decode_token,
    require_token_type,
)


def test_access_and_refresh_tokens_have_required_distinct_claims() -> None:
    access_token = create_access_token(user_id=12, username="zhangsan", role="USER")
    refresh_token = create_refresh_token(user_id=12, username="zhangsan", role="USER")

    access = decode_token(access_token)
    refresh = decode_token(refresh_token)

    for payload, token_type in ((access, "access"), (refresh, "refresh")):
        assert payload["sub"] == "12"
        assert payload["username"] == "zhangsan"
        assert payload["role"] == "USER"
        assert payload["type"] == token_type
        assert isinstance(payload["jti"], str) and payload["jti"]
        assert isinstance(payload["iat"], int)
        assert isinstance(payload["exp"], int)
    assert access["jti"] != refresh["jti"]


def test_expired_invalid_and_wrong_type_tokens_are_rejected() -> None:
    expired_token = create_access_token(
        user_id=12,
        username="zhangsan",
        role="USER",
        expires_delta=timedelta(seconds=-1),
    )
    with pytest.raises(TokenExpiredError):
        decode_token(expired_token)

    with pytest.raises(TokenInvalidError):
        decode_token("not.a.jwt")

    forged = jwt.encode(
        {
            "sub": "12",
            "username": "zhangsan",
            "role": "USER",
            "type": "access",
            "jti": "forged-jti",
            "iat": 1_788_307_200,
            "exp": 4_788_307_200,
        },
        "a-different-signing-key-that-is-not-configured",
        algorithm="HS256",
    )
    with pytest.raises(TokenInvalidError):
        decode_token(forged)

    refresh = decode_token(create_refresh_token(user_id=12, username="zhangsan", role="USER"))
    with pytest.raises(TokenInvalidError):
        require_token_type(refresh, "access")
