#!/usr/bin/env python3
"""Validate Firebase configuration and credentials loading."""

from app.core.config import get_settings
from app.core.firebase import init_firebase, shutdown_firebase
from app.core.firebase_credentials import build_service_account_dict, resolve_firebase_credentials


def main() -> int:
    settings = get_settings()
    print("Firebase configuration check")
    print(f"  auth_enabled: {settings.firebase_auth_enabled}")
    print(f"  project_id: {settings.firebase_project_id}")
    print(f"  credentials_path: {settings.firebase_credentials_path}")
    print(f"  env_fields_configured: {settings.has_firebase_env_credentials()}")

    if not settings.firebase_auth_enabled:
        print("OK: Firebase auth is disabled.")
        return 0

    if not settings.firebase_project_id:
        print("ERROR: FIREBASE_PROJECT_ID is missing.")
        return 1

    service_account = build_service_account_dict(settings)
    if service_account:
        print("OK: Service account can be built from environment variables.")
    elif settings.firebase_credentials_path:
        print(f"INFO: Will try credentials file at {settings.firebase_credentials_path}")
    elif settings.firebase_credentials_json:
        print("INFO: Will use FIREBASE_CREDENTIALS_JSON.")
    else:
        print("ERROR: No Firebase credentials configured.")
        return 1

    try:
        cred, source = resolve_firebase_credentials(settings)
        print(f"OK: Credentials resolved from '{source}'.")
        init_firebase(settings)
        print("OK: Firebase Admin SDK initialized successfully.")
        shutdown_firebase()
        return 0
    except Exception as exc:
        print(f"ERROR: Firebase initialization failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
