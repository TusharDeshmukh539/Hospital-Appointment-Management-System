# temp_test.py

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)

password = "Admin123"

hashed = hash_password(password)

print("HASH :", hashed)

print(
    "VERIFY:",
    verify_password(
        password,
        hashed,
    ),
)

token = create_access_token(
    user_id=1,
    role="ADMIN",
)

print(token)

print(
    decode_token(token)
)