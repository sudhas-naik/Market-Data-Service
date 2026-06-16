"""Tests for Firebase credentials resolution."""

from unittest.mock import patch

from app.core.config import Settings
from app.core.firebase_credentials import build_service_account_dict, resolve_firebase_credentials


def test_build_service_account_from_env_fields():
    settings = Settings(
        firebase_project_id="test-project",
        firebase_private_key_id="key-id",
        firebase_private_key="-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----\\n",
        firebase_client_email="firebase@test-project.iam.gserviceaccount.com",
        firebase_client_id="123",
        firebase_client_x509_cert_url="https://example.com/cert",
    )

    result = build_service_account_dict(settings)
    assert result is not None
    assert result["project_id"] == "test-project"
    assert result["client_email"] == "firebase@test-project.iam.gserviceaccount.com"
    assert "\nabc\n" in result["private_key"]


def test_resolve_credentials_prefers_env_fields_when_no_file():
    settings = Settings.model_construct(
        firebase_project_id="test-project",
        firebase_private_key="-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----\\n",
        firebase_client_email="firebase@test-project.iam.gserviceaccount.com",
        firebase_credentials_path="./missing-file.json",
        firebase_credentials_json=None,
        firebase_private_key_id=None,
        firebase_client_id=None,
        firebase_client_x509_cert_url=None,
    )

    with patch("firebase_admin.credentials.Certificate") as mock_certificate:
        mock_certificate.return_value = object()
        _, source = resolve_firebase_credentials(settings)

    assert source == "env_fields"
    mock_certificate.assert_called_once()
