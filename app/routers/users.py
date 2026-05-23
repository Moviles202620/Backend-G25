"""
Router: /users
Consumed by: StudentProfileScreen (View 1 — Sprint 2, branch Nicotorres7)

Endpoints:
  GET    /users/me              → loads authenticated user data into StudentProfileScreen
  PUT    /users/change-password → changes password from ChangePasswordScreen (via SettingsScreen)
  PUT    /users/me              → updates profile from EditProfileScreen and preferences from SettingsScreen
  POST   /users/me/carnet       → uploads carnet image to Supabase Storage, saves URL in DB
  DELETE /users/me/carnet       → removes carnet image from Supabase Storage and clears URL in DB
  POST   /users/me/rut          → uploads RUT document (PDF or image) to Supabase Storage, saves URL in DB
  DELETE /users/me/rut          → removes RUT document from Supabase Storage and clears URL in DB
  POST   /users/me/cedula       → uploads cedula document (PDF or image) to Supabase Storage, saves URL in DB
  DELETE /users/me/cedula       → removes cedula document from Supabase Storage and clears URL in DB

Feature classification (rubric):
  - GET  /users/me              → f (external service) + e (authentication)
  - PUT  /users/change-password → f (external service) + e (authentication)
  - PUT  /users/me              → f (external service)
  - POST /users/me/carnet       → Sprint 3: Caching — Coil image cache + Supabase Storage
  - POST /users/me/rut          → Sprint 4: PaymentDocuments — multi-threading + local storage + EVC
  - POST /users/me/cedula       → Sprint 4: PaymentDocuments — multi-threading + local storage + EVC

Note: PUT /users/me requires ALL fields (name, department, language, is_dark_mode).
The frontend must always send the full object even when updating a single field.
"""

import uuid
import httpx
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserOut, UserUpdateIn, ChangePasswordIn
from app.services.user_service import update_me, change_password

router = APIRouter(prefix="/users", tags=["users"])

# Isabella — Sprint 4: PaymentDocuments — allowed MIME types for document upload
ALLOWED_DOCUMENT_TYPES = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]


async def delete_from_supabase(file_url: str, bucket: str) -> None:
    """Delete a file from Supabase Storage given its public URL and bucket name."""
    try:
        filename = file_url.split(f"/{bucket}/")[-1]
        delete_url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket}/{filename}"
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        }
        async with httpx.AsyncClient() as client:
            await client.delete(delete_url, headers=headers)
    except Exception:
        pass


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user",
    description=(
        "Returns the profile of the authenticated user. "
        "Used by StudentProfileScreen to display name, department and application stats. "
        "Requires a valid Bearer token in the Authorization header."
    ),
)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put(
    "/change-password",
    summary="Change password",
    description=(
        "Changes the password of the authenticated user. "
        "Used by ChangePasswordScreen (accessed from SettingsScreen). "
        "Validates current_password against the stored hash before updating. "
        "confirm_password is validated at schema level."
    ),
)
def change_password_route(
    payload: ChangePasswordIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    change_password(db, current_user, payload.current_password, payload.new_password)
    return {"detail": "Password updated successfully"}


@router.put(
    "/me",
    response_model=UserOut,
    summary="Update profile",
    description=(
        "Updates the authenticated user's profile. Used by: "
        "EditProfileScreen (name, department, language) and "
        "SettingsScreen (is_dark_mode, language toggles in real time). "
        "All fields are required — send current values for fields that are not being changed."
    ),
)
def update_profile(
    payload: UserUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated_user = update_me(db, current_user, payload.name, payload.department, payload.language, payload.is_dark_mode)
    return updated_user


# Isabella — Sprint 3: Coil — carnet upload endpoint
# Uploads image to Supabase Storage bucket "Carnets" and saves public URL in users table.
# If user already has a carnet, the old file is deleted from Storage before uploading the new one.
# The URL is then loaded in StudentProfileScreen using Coil, which caches the image
# automatically in memory and disk — no repeated network calls for the same image.
@router.post(
    "/me/carnet",
    response_model=UserOut,
    summary="Upload carnet image",
    description=(
        "Uploads the student's carnet image to Supabase Storage. "
        "Deletes the previous carnet file if one exists. "
        "Stores the public URL in the user's profile_picture field. "
        "Used by StudentProfileScreen — image is displayed and cached by Coil on the client."
    ),
)
async def upload_carnet(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Only JPEG and PNG images are allowed")

    if current_user.profile_picture:
        await delete_from_supabase(current_user.profile_picture, "Carnets")

    extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"carnet_{current_user.id}_{uuid.uuid4().hex}.{extension}"
    file_bytes = await file.read()

    supabase_url = f"{settings.SUPABASE_URL}/storage/v1/object/Carnets/{filename}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "Content-Type": file.content_type,
        "x-upsert": "true"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(supabase_url, content=file_bytes, headers=headers)
        if response.status_code not in [200, 201]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload to Supabase Storage: {response.text}"
            )

    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/Carnets/{filename}"
    current_user.profile_picture = public_url
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete(
    "/me/carnet",
    response_model=UserOut,
    summary="Delete carnet image",
    description=(
        "Deletes the carnet image from Supabase Storage and clears the URL from the user's profile. "
        "Used by StudentProfileScreen when user selects 'Eliminar imagen'."
    ),
)
async def delete_carnet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.profile_picture:
        await delete_from_supabase(current_user.profile_picture, "Carnets")

    current_user.profile_picture = None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


# Isabella — Sprint 4: PaymentDocuments — RUT upload endpoint
# Uploads RUT document (PDF or image) to Supabase Storage bucket "Documents".
# Deletes the old file if one exists before uploading the new one.
# Saves the public URL in users.rut_url.
# Used by PaymentDocumentsScreen — part of the parallel coroutine upload strategy.
@router.post(
    "/me/rut",
    response_model=UserOut,
    summary="Upload RUT document",
    description=(
        "Uploads the student's RUT document (PDF or image) to Supabase Storage bucket Documents. "
        "Deletes the previous RUT file if one exists. "
        "Stores the public URL in the user's rut_url field. "
        "Used by PaymentDocumentsScreen as part of the parallel async upload strategy."
    ),
)
async def upload_rut(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG images and PDF files are allowed")

    if current_user.rut_url:
        await delete_from_supabase(current_user.rut_url, "Documents")

    extension = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"rut_{current_user.id}_{uuid.uuid4().hex}.{extension}"
    file_bytes = await file.read()

    supabase_url = f"{settings.SUPABASE_URL}/storage/v1/object/Documents/{filename}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "Content-Type": file.content_type,
        "x-upsert": "true"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(supabase_url, content=file_bytes, headers=headers)
        if response.status_code not in [200, 201]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload RUT to Supabase Storage: {response.text}"
            )

    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/Documents/{filename}"
    current_user.rut_url = public_url
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


# Isabella — Sprint 4: PaymentDocuments — RUT delete endpoint
@router.delete(
    "/me/rut",
    response_model=UserOut,
    summary="Delete RUT document",
    description=(
        "Deletes the RUT document from Supabase Storage and clears rut_url from the user's profile. "
        "Used by PaymentDocumentsScreen when user removes their RUT."
    ),
)
async def delete_rut(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.rut_url:
        await delete_from_supabase(current_user.rut_url, "Documents")

    current_user.rut_url = None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


# Isabella — Sprint 4: PaymentDocuments — cedula upload endpoint
# Uploads cedula document (PDF or image) to Supabase Storage bucket "Documents".
# Deletes the old file if one exists before uploading the new one.
# Saves the public URL in users.cedula_url.
# Used by PaymentDocumentsScreen — part of the parallel coroutine upload strategy.
@router.post(
    "/me/cedula",
    response_model=UserOut,
    summary="Upload cedula document",
    description=(
        "Uploads the student's cedula document (PDF or image) to Supabase Storage bucket Documents. "
        "Deletes the previous cedula file if one exists. "
        "Stores the public URL in the user's cedula_url field. "
        "Used by PaymentDocumentsScreen as part of the parallel async upload strategy."
    ),
)
async def upload_cedula(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG images and PDF files are allowed")

    if current_user.cedula_url:
        await delete_from_supabase(current_user.cedula_url, "Documents")

    extension = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"cedula_{current_user.id}_{uuid.uuid4().hex}.{extension}"
    file_bytes = await file.read()

    supabase_url = f"{settings.SUPABASE_URL}/storage/v1/object/Documents/{filename}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "Content-Type": file.content_type,
        "x-upsert": "true"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(supabase_url, content=file_bytes, headers=headers)
        if response.status_code not in [200, 201]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload cedula to Supabase Storage: {response.text}"
            )

    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/Documents/{filename}"
    current_user.cedula_url = public_url
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


# Isabella — Sprint 4: PaymentDocuments — cedula delete endpoint
@router.delete(
    "/me/cedula",
    response_model=UserOut,
    summary="Delete cedula document",
    description=(
        "Deletes the cedula document from Supabase Storage and clears cedula_url from the user's profile. "
        "Used by PaymentDocumentsScreen when user removes their cedula."
    ),
)
async def delete_cedula(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.cedula_url:
        await delete_from_supabase(current_user.cedula_url, "Documents")

    current_user.cedula_url = None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user