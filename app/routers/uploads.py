from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.auth import require_role
from app.config import settings
from app.models import User
from app.storage import upload_file

router = APIRouter(prefix="/uploads", tags=["uploads"])


def _check_size_and_type(upload: UploadFile, size: int) -> str:
    ct = (upload.content_type or "").lower()
    if ct.startswith("image/"):
        if size > settings.MAX_IMAGE_BYTES:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Изображение больше 5 МБ")
        if ct not in ("image/jpeg", "image/png", "image/jpg"):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Поддерживаются JPG/PNG")
        return "image"
    if ct.startswith("video/"):
        if size > settings.MAX_VIDEO_BYTES:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Видео больше 30 МБ")
        if ct != "video/mp4":
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Поддерживается MP4")
        return "video"
    if ct in ("text/html", "application/xhtml+xml"):
        if size > settings.MAX_HTML_BYTES:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "HTML больше 1 МБ")
        return "html"
    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Неподдерживаемый тип файла")


@router.post("")
async def upload(
    file: UploadFile = File(...),  # noqa: B008
    _: User = Depends(require_role("advertiser")),  # noqa: B008
):
    data = await file.read()
    _check_size_and_type(file, len(data))
    url = upload_file(data, file.filename or "file", file.content_type or "")
    return {"url": url}
