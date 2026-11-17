import hashlib
import hmac
import json
import secrets
from pathlib import Path


PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 310_000


class CredentialFileError(Exception):
    """Raised when the teacher credential file is missing or invalid."""


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty.")

    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return (
        f"{PASSWORD_HASH_ALGORITHM}${PASSWORD_HASH_ITERATIONS}"
        f"${salt.hex()}${digest.hex()}"
    )


def _parse_password_hash(encoded_hash: str) -> tuple[int, bytes, bytes]:
    try:
        algorithm, iterations_text, salt_text, digest_text = encoded_hash.split("$")
        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_text)
        digest = bytes.fromhex(digest_text)
    except (ValueError, TypeError) as error:
        raise CredentialFileError("A teacher password hash is invalid.") from error

    if (
        algorithm != PASSWORD_HASH_ALGORITHM
        or not 100_000 <= iterations <= 2_000_000
        or len(salt) != 16
        or len(digest) != hashlib.sha256().digest_size
    ):
        raise CredentialFileError("A teacher password hash is invalid.")

    return iterations, salt, digest


def load_teacher_credentials(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise CredentialFileError(
            "Teacher credentials are not configured. Run create_teacher.py."
        ) from error
    except (OSError, json.JSONDecodeError) as error:
        raise CredentialFileError("The teacher credential file cannot be read.") from error

    teachers = data.get("teachers") if isinstance(data, dict) else None
    if not isinstance(teachers, list):
        raise CredentialFileError("The teacher credential file has an invalid format.")

    credentials = {}
    for teacher in teachers:
        if not isinstance(teacher, dict):
            raise CredentialFileError("A teacher entry has an invalid format.")

        username = teacher.get("username")
        password_hash = teacher.get("password_hash")
        if (
            not isinstance(username, str)
            or not username.strip()
            or not isinstance(password_hash, str)
            or username in credentials
        ):
            raise CredentialFileError("A teacher entry has an invalid format.")

        _parse_password_hash(password_hash)
        credentials[username] = password_hash

    return credentials


def verify_password(password: str, encoded_hash: str) -> bool:
    iterations, salt, expected_digest = _parse_password_hash(encoded_hash)
    actual_digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(actual_digest, expected_digest)


def verify_teacher_credentials(username: str, password: str, path: Path) -> bool:
    credentials = load_teacher_credentials(path)
    password_hash = credentials.get(username)
    if password_hash is None:
        return False
    return verify_password(password, password_hash)
