import getpass
import json
from pathlib import Path

from auth import CredentialFileError, hash_password, load_teacher_credentials


CREDENTIALS_FILE = Path(__file__).with_name("teachers.json")


def main() -> None:
    username = input("Teacher username: ").strip()
    if not username:
        raise SystemExit("Username cannot be empty.")

    password = getpass.getpass("Teacher password (12+ characters): ")
    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters.")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match.")

    if CREDENTIALS_FILE.exists():
        credentials = load_teacher_credentials(CREDENTIALS_FILE)
    else:
        credentials = {}

    if username in credentials:
        raise SystemExit("That teacher username already exists.")

    credentials[username] = hash_password(password)
    data = {
        "teachers": [
            {"username": teacher_name, "password_hash": password_hash}
            for teacher_name, password_hash in sorted(credentials.items())
        ]
    }
    CREDENTIALS_FILE.write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Added teacher '{username}' to {CREDENTIALS_FILE.name}.")


if __name__ == "__main__":
    try:
        main()
    except CredentialFileError as error:
        raise SystemExit(str(error)) from error
