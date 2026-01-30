"""
Chapter 10: 파일 업로드 (File Upload)

Form 데이터 처리, File/UploadFile 차이, 다중 파일 업로드,
파일 크기/타입 검증을 학습한다.

실행 방법:
    uvicorn main:app --reload

의존성:
    pip install fastapi uvicorn python-multipart
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

# ============================================================
# FastAPI 앱 생성
# ============================================================
app = FastAPI(
    title="Chapter 10: 파일 업로드",
    description="Form 데이터, File/UploadFile, 다중 업로드, 파일 검증 학습",
    version="1.0.0",
)

# ============================================================
# 설정 상수
# ============================================================
# 업로드 파일 저장 디렉토리 (현재 파일 기준 상대 경로)
UPLOAD_DIR = Path(__file__).parent / "uploads"
# 업로드 디렉토리가 없으면 자동 생성
UPLOAD_DIR.mkdir(exist_ok=True)

# 최대 파일 크기: 10MB (바이트 단위)
MAX_FILE_SIZE = 10 * 1024 * 1024

# 허용하는 이미지 MIME 타입 목록
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
}

# 허용하는 이미지 확장자 목록
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}


# ============================================================
# 유틸리티 함수
# ============================================================
def generate_unique_filename(original_filename: str) -> str:
    """
    원본 파일명을 기반으로 고유한 파일명을 생성한다.
    UUID를 접두사로 사용하여 파일명 충돌을 방지한다.

    예: "photo.jpg" → "a1b2c3d4-e5f6-..._photo.jpg"
    """
    unique_id = uuid.uuid4().hex[:12]
    # 파일명에서 위험한 문자 제거 (경로 탐색 방지)
    safe_name = os.path.basename(original_filename)
    return f"{unique_id}_{safe_name}"


def validate_file_size(file_size: int, max_size: int = MAX_FILE_SIZE) -> None:
    """
    파일 크기를 검증한다.
    최대 크기를 초과하면 HTTPException을 발생시킨다.
    """
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        file_size_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=(
                f"파일 크기가 너무 큽니다. "
                f"최대 {max_size_mb:.1f}MB까지 허용되며, "
                f"업로드된 파일은 {file_size_mb:.2f}MB입니다."
            ),
        )


def validate_image_type(filename: str, content_type: str | None) -> None:
    """
    이미지 파일인지 검증한다.
    MIME 타입과 확장자를 모두 확인한다.
    """
    # 1. MIME 타입 검증
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"허용되지 않는 파일 타입입니다: {content_type}. "
                f"허용 타입: {', '.join(sorted(ALLOWED_IMAGE_TYPES))}"
            ),
        )

    # 2. 확장자 검증 (MIME 타입과 이중으로 검증)
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=(
                f"허용되지 않는 파일 확장자입니다: {file_ext}. "
                f"허용 확장자: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
            ),
        )


async def save_upload_file(file: UploadFile) -> dict:
    """
    업로드된 파일을 디스크에 저장하고 파일 정보를 반환한다.
    청크 단위로 읽어서 메모리 효율적으로 저장한다.
    """
    # 고유한 파일명 생성
    unique_name = generate_unique_filename(file.filename or "unknown")
    file_path = UPLOAD_DIR / unique_name

    # 청크 단위로 파일 저장 (대용량 파일 대비)
    total_size = 0
    with open(file_path, "wb") as buffer:
        while True:
            # 1MB 단위로 읽기
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            total_size += len(chunk)

            # 저장 중에도 파일 크기 검증 (스트리밍 방식)
            validate_file_size(total_size)

            buffer.write(chunk)

    return {
        "original_filename": file.filename,
        "saved_filename": unique_name,
        "content_type": file.content_type,
        "size_bytes": total_size,
        "size_readable": _format_file_size(total_size),
        "saved_path": str(file_path),
    }


def _format_file_size(size_bytes: int) -> str:
    """바이트 크기를 사람이 읽기 쉬운 형식으로 변환한다."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


# ============================================================
# 1. Form() 데이터 받기 - 폼 로그인
# ============================================================
@app.post("/login", summary="폼 로그인", tags=["Form 데이터"])
async def form_login(
    username: str = Form(
        ...,
        min_length=3,
        max_length=50,
        description="사용자 이름 (3~50자)",
        examples=["admin"],
    ),
    password: str = Form(
        ...,
        min_length=6,
        description="비밀번호 (6자 이상)",
        examples=["secret123"],
    ),
):
    """
    HTML 폼 로그인 처리 엔드포인트.

    Form() 파라미터는 application/x-www-form-urlencoded 또는
    multipart/form-data로 전송된 데이터를 받는다.

    **주의**: 실제 서비스에서는 비밀번호를 평문으로 반환하지 않는다.
    이 예제는 학습 목적으로만 사용한다.
    """
    # 실제 서비스에서는 데이터베이스 조회 및 비밀번호 해시 비교가 필요하다
    if username == "admin" and password == "secret123":
        return {
            "message": "로그인 성공",
            "username": username,
            "token": "fake-jwt-token-for-demo",
        }
    else:
        raise HTTPException(
            status_code=401,
            detail="사용자 이름 또는 비밀번호가 올바르지 않습니다.",
        )


@app.post("/register", summary="폼 회원가입", tags=["Form 데이터"])
async def form_register(
    username: str = Form(..., min_length=3, max_length=50, description="사용자 이름"),
    email: str = Form(..., description="이메일 주소", examples=["user@example.com"]),
    password: str = Form(..., min_length=6, description="비밀번호"),
    password_confirm: str = Form(..., min_length=6, description="비밀번호 확인"),
    agree_terms: bool = Form(..., description="약관 동의 여부"),
):
    """
    회원가입 폼 처리 엔드포인트.
    여러 개의 Form 필드를 동시에 받는 예제이다.
    """
    # 비밀번호 일치 확인
    if password != password_confirm:
        raise HTTPException(
            status_code=400,
            detail="비밀번호와 비밀번호 확인이 일치하지 않습니다.",
        )

    # 약관 동의 확인
    if not agree_terms:
        raise HTTPException(
            status_code=400,
            detail="서비스 약관에 동의해야 합니다.",
        )

    return {
        "message": "회원가입이 완료되었습니다.",
        "user": {
            "username": username,
            "email": email,
        },
    }


# ============================================================
# 2. File(bytes) 업로드 - 작은 파일용
# ============================================================
@app.post("/upload/file-bytes", summary="File(bytes) 업로드", tags=["파일 업로드"])
async def upload_file_bytes(
    file: bytes = File(..., description="업로드할 파일 (바이트 형태)"),
):
    """
    File(bytes) 방식으로 파일을 업로드한다.

    **특징**:
    - 파일 전체 내용이 `bytes`로 메모리에 로드된다.
    - 파일명, MIME 타입 등의 메타데이터에 접근할 수 없다.
    - 작은 파일(설정 파일, 텍스트 등)에 적합하다.
    - 큰 파일에는 UploadFile 사용을 권장한다.
    """
    # 파일 크기 검증
    validate_file_size(len(file))

    return {
        "message": "File(bytes) 업로드 성공",
        "file_size_bytes": len(file),
        "file_size_readable": _format_file_size(len(file)),
        "note": "bytes 방식은 파일명, 타입 등 메타데이터를 알 수 없습니다.",
    }


# ============================================================
# 3. UploadFile 업로드 - 권장 방식
# ============================================================
@app.post("/upload/single", summary="UploadFile 단일 업로드", tags=["파일 업로드"])
async def upload_single_file(
    file: UploadFile = File(..., description="업로드할 파일"),
):
    """
    UploadFile 방식으로 단일 파일을 업로드한다.

    **특징**:
    - 파일명, MIME 타입, 크기 등 메타데이터에 접근 가능하다.
    - 일정 크기를 초과하면 디스크의 임시 파일로 저장된다 (메모리 효율적).
    - 비동기 read(), write(), seek(), close() 메서드를 제공한다.
    - 대부분의 파일 업로드 시나리오에서 권장되는 방식이다.
    """
    # 파일 크기 검증 (file.size는 Python 3.x + python-multipart에서 제공)
    if file.size is not None:
        validate_file_size(file.size)

    # 파일 저장
    file_info = await save_upload_file(file)

    return {
        "message": "UploadFile 단일 업로드 성공",
        "file_info": file_info,
    }


# ============================================================
# 4. 다중 파일 업로드
# ============================================================
@app.post("/upload/multiple", summary="다중 파일 업로드", tags=["파일 업로드"])
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="업로드할 파일 목록"),
):
    """
    여러 개의 파일을 동시에 업로드한다.
    List[UploadFile] 타입 힌트를 사용하면 다중 파일을 받을 수 있다.

    curl 사용 예시:
        curl -X POST http://localhost:8000/upload/multiple \\
          -F "files=@image1.png" \\
          -F "files=@image2.jpg" \\
          -F "files=@document.pdf"
    """
    # 업로드 파일 개수 제한 (최대 5개)
    max_files = 5
    if len(files) > max_files:
        raise HTTPException(
            status_code=400,
            detail=f"한 번에 최대 {max_files}개의 파일만 업로드할 수 있습니다. "
            f"현재 {len(files)}개가 선택되었습니다.",
        )

    # 각 파일을 순차적으로 저장
    results = []
    total_size = 0
    for idx, file in enumerate(files, start=1):
        try:
            file_info = await save_upload_file(file)
            results.append(
                {
                    "index": idx,
                    "status": "성공",
                    **file_info,
                }
            )
            total_size += file_info["size_bytes"]
        except HTTPException as e:
            # 개별 파일 오류 시에도 나머지 파일은 계속 처리
            results.append(
                {
                    "index": idx,
                    "status": "실패",
                    "original_filename": file.filename,
                    "error": e.detail,
                }
            )

    return {
        "message": f"다중 파일 업로드 완료: {len(files)}개",
        "total_size_readable": _format_file_size(total_size),
        "files": results,
    }


# ============================================================
# 5. 파일 타입 검증 - 이미지만 허용
# ============================================================
@app.post("/upload/image", summary="이미지 파일 업로드", tags=["파일 업로드"])
async def upload_image(
    file: UploadFile = File(..., description="업로드할 이미지 파일"),
):
    """
    이미지 파일만 허용하는 업로드 엔드포인트.
    MIME 타입과 확장자를 모두 검증하여 이미지 파일만 받는다.

    허용 타입: JPEG, PNG, GIF, WebP, SVG
    """
    # 이미지 타입 검증 (MIME 타입 + 확장자 이중 검증)
    validate_image_type(file.filename or "", file.content_type)

    # 파일 크기 검증
    if file.size is not None:
        validate_file_size(file.size)

    # 매직 바이트(파일 시그니처) 검증 - 가장 신뢰할 수 있는 방법
    header = await file.read(16)
    await file.seek(0)  # 읽기 위치를 처음으로 되돌린다

    # 주요 이미지 포맷의 매직 바이트
    image_signatures = {
        b"\xff\xd8\xff": "JPEG",
        b"\x89PNG\r\n\x1a\n": "PNG",
        b"GIF87a": "GIF",
        b"GIF89a": "GIF",
        b"RIFF": "WebP (RIFF 컨테이너)",
    }

    detected_format = None
    for signature, format_name in image_signatures.items():
        if header.startswith(signature):
            detected_format = format_name
            break

    # SVG는 텍스트 기반이므로 별도 처리 (XML 시작 태그 확인)
    if detected_format is None:
        try:
            header_text = header.decode("utf-8", errors="ignore")
            if "<svg" in header_text.lower() or "<?xml" in header_text.lower():
                detected_format = "SVG"
        except (UnicodeDecodeError, ValueError):
            pass

    if detected_format is None:
        raise HTTPException(
            status_code=415,
            detail="파일의 실제 내용이 이미지 형식이 아닙니다. "
            "확장자나 MIME 타입이 위조되었을 수 있습니다.",
        )

    # 파일 저장
    file_info = await save_upload_file(file)

    return {
        "message": "이미지 업로드 성공",
        "detected_format": detected_format,
        "file_info": file_info,
    }


# ============================================================
# 6. 파일 + 폼 데이터 동시 전송
# ============================================================
@app.post("/upload/profile", summary="프로필 업로드 (파일 + 폼)", tags=["파일 업로드"])
async def upload_profile(
    username: str = Form(
        ...,
        min_length=2,
        max_length=30,
        description="사용자 이름",
        examples=["홍길동"],
    ),
    bio: str = Form(
        default="",
        max_length=200,
        description="자기소개 (선택, 최대 200자)",
        examples=["안녕하세요, 개발자입니다."],
    ),
    avatar: UploadFile = File(..., description="프로필 이미지"),
):
    """
    파일과 폼 데이터를 동시에 전송받는 엔드포인트.

    프로필 이미지(avatar)와 사용자 정보(username, bio)를 함께 받는다.
    이 패턴은 실무에서 매우 자주 사용된다.

    **주의**: File과 Form을 같이 쓸 때 Content-Type은 반드시
    multipart/form-data여야 한다.
    """
    # 아바타 이미지 타입 검증
    validate_image_type(avatar.filename or "", avatar.content_type)

    # 아바타 파일 크기 제한 (프로필 이미지는 5MB로 제한)
    profile_max_size = 5 * 1024 * 1024
    if avatar.size is not None and avatar.size > profile_max_size:
        raise HTTPException(
            status_code=413,
            detail=f"프로필 이미지는 최대 5MB까지 허용됩니다. "
            f"업로드된 파일: {_format_file_size(avatar.size)}",
        )

    # 아바타 파일 저장
    avatar_info = await save_upload_file(avatar)

    return {
        "message": "프로필 업로드 성공",
        "profile": {
            "username": username,
            "bio": bio if bio else "(미입력)",
            "avatar": avatar_info,
        },
    }


@app.post(
    "/upload/post",
    summary="게시글 작성 (다중 파일 + 폼)",
    tags=["파일 업로드"],
)
async def upload_post(
    title: str = Form(..., min_length=1, max_length=100, description="게시글 제목"),
    content: str = Form(..., min_length=1, description="게시글 내용"),
    category: str = Form(default="일반", description="카테고리"),
    attachments: List[UploadFile] = File(
        default=[],
        description="첨부 파일 목록 (선택, 최대 3개)",
    ),
):
    """
    게시글 작성 엔드포인트.
    제목, 내용 등 폼 데이터와 다중 첨부 파일을 동시에 받는다.

    첨부 파일이 없어도 게시글을 작성할 수 있다.
    """
    # 첨부 파일 개수 제한
    max_attachments = 3
    if len(attachments) > max_attachments:
        raise HTTPException(
            status_code=400,
            detail=f"첨부 파일은 최대 {max_attachments}개까지 허용됩니다.",
        )

    # 첨부 파일 저장
    saved_files = []
    for file in attachments:
        # 파일명이 빈 문자열이면 파일이 선택되지 않은 것 (빈 폼 필드)
        if file.filename:
            file_info = await save_upload_file(file)
            saved_files.append(file_info)

    return {
        "message": "게시글 작성 성공",
        "post": {
            "title": title,
            "content": content,
            "category": category,
            "attachment_count": len(saved_files),
            "attachments": saved_files,
        },
    }


# ============================================================
# 유틸리티 엔드포인트
# ============================================================
@app.get("/", summary="루트 엔드포인트", tags=["유틸리티"])
async def root():
    """기본 루트 엔드포인트. API 정보를 반환한다."""
    return {
        "message": "Chapter 10: 파일 업로드 학습",
        "docs": "http://localhost:8000/docs 에서 Swagger UI를 통해 테스트하세요.",
        "endpoints": {
            "Form 데이터": ["/login", "/register"],
            "파일 업로드": [
                "/upload/file-bytes",
                "/upload/single",
                "/upload/multiple",
                "/upload/image",
            ],
            "파일 + 폼": ["/upload/profile", "/upload/post"],
        },
    }


@app.get("/uploads", summary="업로드된 파일 목록", tags=["유틸리티"])
async def list_uploaded_files():
    """
    uploads 디렉토리에 저장된 파일 목록을 반환한다.
    실제 서비스에서는 데이터베이스에서 파일 정보를 조회하는 것이 일반적이다.
    """
    files = []
    if UPLOAD_DIR.exists():
        for file_path in sorted(UPLOAD_DIR.iterdir()):
            if file_path.is_file():
                stat = file_path.stat()
                files.append(
                    {
                        "filename": file_path.name,
                        "size_bytes": stat.st_size,
                        "size_readable": _format_file_size(stat.st_size),
                    }
                )

    return {
        "upload_directory": str(UPLOAD_DIR),
        "total_files": len(files),
        "files": files,
    }


@app.delete("/uploads", summary="업로드된 파일 전체 삭제", tags=["유틸리티"])
async def clear_uploaded_files():
    """
    uploads 디렉토리의 모든 파일을 삭제한다.
    학습 및 테스트 후 정리 용도로 사용한다.
    """
    deleted_count = 0
    if UPLOAD_DIR.exists():
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.is_file():
                file_path.unlink()
                deleted_count += 1

    return {
        "message": f"업로드된 파일 {deleted_count}개를 삭제했습니다.",
    }
