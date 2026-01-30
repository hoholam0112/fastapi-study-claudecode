# Chapter 10: 파일 업로드 (File Upload)

## 학습 목표

- HTML Form 데이터를 FastAPI에서 받아 처리하는 방법을 익힌다.
- `File(bytes)`과 `UploadFile`의 차이를 이해하고, 상황에 맞게 사용할 수 있다.
- 다중 파일 업로드를 구현할 수 있다.
- 파일 크기 및 타입(MIME type) 검증 로직을 작성할 수 있다.
- 파일과 폼 데이터를 동시에 전송받는 API를 구현할 수 있다.

---

## 핵심 개념

### 1. Form 데이터

HTML `<form>` 태그에서 전송하는 데이터를 FastAPI에서 받으려면 `Form()`을 사용한다. JSON 본문(`Body`)과는 인코딩 방식이 다르다.

| 구분 | Content-Type | FastAPI 파라미터 |
|------|-------------|-----------------|
| JSON 본문 | `application/json` | `Body()` |
| Form 데이터 | `application/x-www-form-urlencoded` | `Form()` |
| 파일 업로드 | `multipart/form-data` | `File()` / `UploadFile` |

> **주의**: `Form()`을 사용하려면 `python-multipart` 패키지가 필요하다. FastAPI 설치 시 자동으로 포함된다.

### 2. File vs UploadFile

| 특성 | `File(bytes)` | `UploadFile` |
|------|--------------|-------------|
| 데이터 형태 | `bytes` (전체 내용이 메모리에 로드) | 파일 객체 (스풀 파일 사용) |
| 메모리 사용 | 파일 전체가 메모리에 올라감 | 일정 크기 초과 시 디스크에 임시 저장 |
| 적합한 용도 | 작은 파일 (수 KB) | 큰 파일 (이미지, 동영상 등) |
| 파일 정보 | 내용만 접근 가능 | `filename`, `content_type`, `size` 접근 가능 |
| 비동기 메서드 | 없음 | `read()`, `write()`, `seek()`, `close()` |

### 3. UploadFile 주요 속성 및 메서드

```python
# 속성
file.filename       # 원본 파일명 (예: "photo.jpg")
file.content_type   # MIME 타입 (예: "image/jpeg")
file.size           # 파일 크기 (바이트)

# 비동기 메서드
await file.read()           # 전체 내용 읽기
await file.read(1024)       # 1024 바이트만 읽기
await file.seek(0)          # 읽기 위치를 처음으로 이동
await file.write(data)      # 데이터 쓰기
await file.close()          # 파일 닫기
```

### 4. 다중 파일 업로드

```python
from typing import List
from fastapi import UploadFile

@app.post("/files/")
async def upload_files(files: List[UploadFile]):
    for file in files:
        contents = await file.read()
        # 파일 처리 로직
```

### 5. 파일 검증 전략

| 검증 항목 | 방법 | 주의사항 |
|-----------|------|---------|
| 파일 크기 | `file.size` 또는 `len(await file.read())` | 읽은 후 `seek(0)` 필요 |
| MIME 타입 | `file.content_type` 확인 | 클라이언트가 조작 가능하므로 보조적으로 사용 |
| 확장자 | `file.filename`에서 추출 | 확장자만으로는 불충분 |
| 매직 바이트 | 파일 헤더 바이트 확인 | 가장 신뢰할 수 있는 방법 |

---

## 코드 실행 방법

### 1. 의존성 설치

```bash
pip install fastapi uvicorn python-multipart
```

### 2. 업로드 디렉토리 생성

```bash
cd /Users/zeroman0112/Projects/fastapi-study/phase2_core/ch10_file_upload
mkdir -p uploads
```

### 3. 서버 실행

```bash
cd /Users/zeroman0112/Projects/fastapi-study/phase2_core/ch10_file_upload
uvicorn main:app --reload
```

### 4. API 테스트

```bash
# 폼 로그인 테스트
curl -X POST http://localhost:8000/login \
  -d "username=admin&password=secret123"

# 단일 파일 업로드 (bytes)
curl -X POST http://localhost:8000/upload/file-bytes \
  -F "file=@test_image.png"

# 단일 파일 업로드 (UploadFile)
curl -X POST http://localhost:8000/upload/single \
  -F "file=@test_image.png"

# 다중 파일 업로드
curl -X POST http://localhost:8000/upload/multiple \
  -F "files=@image1.png" \
  -F "files=@image2.jpg"

# 이미지 전용 업로드 (타입 검증)
curl -X POST http://localhost:8000/upload/image \
  -F "file=@photo.jpg"

# 파일 + 폼 데이터 동시 전송
curl -X POST http://localhost:8000/upload/profile \
  -F "username=홍길동" \
  -F "bio=안녕하세요" \
  -F "avatar=@profile.jpg"

# Swagger UI에서 테스트 (파일 업로드 UI 제공)
open http://localhost:8000/docs
```

---

## 실습 포인트

1. **Swagger UI 활용**: `http://localhost:8000/docs`에서 파일 업로드 API를 테스트해보자. FastAPI가 자동으로 파일 선택 UI를 생성해준다.

2. **File(bytes) vs UploadFile 비교**: 같은 파일을 `/upload/file-bytes`와 `/upload/single`에 각각 업로드하고, 응답 데이터의 차이를 비교한다. UploadFile이 더 많은 정보를 제공하는 것을 확인한다.

3. **파일 타입 검증 테스트**: `/upload/image` 엔드포인트에 이미지가 아닌 파일(예: `.txt`, `.pdf`)을 업로드하여 검증이 올바르게 작동하는지 확인한다.

4. **대용량 파일 테스트**: 큰 파일을 업로드하여 `MAX_FILE_SIZE` 제한이 작동하는지 확인한다. 에러 메시지가 적절한지 검토한다.

5. **동시 전송 확인**: `/upload/profile` 엔드포인트로 파일과 폼 데이터를 함께 보내고, 서버에서 두 가지 데이터를 모두 올바르게 수신하는지 확인한다.

6. **업로드된 파일 확인**: `uploads/` 디렉토리에 파일이 실제로 저장되었는지 확인한다. 파일명이 UUID로 변환된 것을 관찰한다.
