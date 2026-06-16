"""Authentication domain models."""

from pydantic import BaseModel, Field


class FirebaseUser(BaseModel):
    """Authenticated Firebase user extracted from a verified ID token."""

    uid: str = Field(..., description="Firebase user ID")
    email: str | None = None
    email_verified: bool = False
    name: str | None = None
    picture: str | None = None
