import json
import tempfile
import unittest
from pathlib import Path

from auth import (
    CredentialFileError,
    hash_password,
    load_teacher_credentials,
    verify_password,
    verify_teacher_credentials,
)


class TeacherCredentialTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.credentials_path = Path(self.temp_dir.name) / "teachers.json"
        self.password_hash = hash_password("a-long-teacher-password")
        self.credentials_path.write_text(
            json.dumps(
                {
                    "teachers": [
                        {
                            "username": "teacher",
                            "password_hash": self.password_hash,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_password_hash_verifies_without_storing_plaintext(self):
        self.assertNotIn("a-long-teacher-password", self.password_hash)
        self.assertTrue(verify_password("a-long-teacher-password", self.password_hash))
        self.assertFalse(verify_password("wrong-password", self.password_hash))

    def test_teacher_credentials_are_read_from_json(self):
        credentials = load_teacher_credentials(self.credentials_path)
        self.assertEqual(credentials, {"teacher": self.password_hash})
        self.assertTrue(
            verify_teacher_credentials(
                "teacher", "a-long-teacher-password", self.credentials_path
            )
        )
        self.assertFalse(
            verify_teacher_credentials("student", "any-password", self.credentials_path)
        )

    def test_missing_credential_file_is_an_explicit_error(self):
        missing_path = Path(self.temp_dir.name) / "missing.json"
        with self.assertRaises(CredentialFileError):
            load_teacher_credentials(missing_path)

    def test_invalid_credential_file_is_an_explicit_error(self):
        self.credentials_path.write_text('{"teachers": "invalid"}', encoding="utf-8")
        with self.assertRaises(CredentialFileError):
            load_teacher_credentials(self.credentials_path)


if __name__ == "__main__":
    unittest.main()
