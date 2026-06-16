"""Build Firebase service account credentials from settings."""

from pathlib import Path

from app.core.config import Settings


def build_service_account_dict(settings: Settings) -> dict[str, str] | None:
    """Build a Firebase service account dict from individual env variables."""
    required = (
        settings.firebase_project_id,
        settings.firebase_private_key,
        settings.firebase_client_email,
    )
    if not all(required):
        return None

    private_key = settings.firebase_private_key
    if "\\n" in private_key:
        private_key = private_key.replace("\\n", "\n")

    return {
        "type": "service_account",
        "project_id": settings.firebase_project_id,
        "private_key_id": settings.firebase_private_key_id or "",
        "private_key": private_key,
        "client_email": settings.firebase_client_email,
        "client_id": settings.firebase_client_id or "",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": settings.firebase_client_x509_cert_url or "",
        "universe_domain": "googleapis.com",
    }


def resolve_firebase_credentials(settings: Settings):
    """Resolve Firebase credentials from file, JSON string, or env fields."""
    import json

    from firebase_admin import credentials

    if settings.firebase_credentials_path:
        path = Path(settings.firebase_credentials_path)
        if path.is_file():
            return credentials.Certificate(str(path)), "file"

    if settings.firebase_credentials_json:
        return credentials.Certificate(json.loads(settings.firebase_credentials_json)), "env_json"

    service_account = build_service_account_dict(settings)
    if service_account:
        return credentials.Certificate(service_account), "env_fields"

    return credentials.ApplicationDefault(), "application_default"
