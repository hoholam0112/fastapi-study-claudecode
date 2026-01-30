# Chapter 13: NoSQL 데이터베이스 (MongoDB + Redis)

> **선택 챕터**: 이 챕터는 MongoDB와 Redis가 별도로 실행 중이어야 합니다.
> Docker를 사용하면 간편하게 환경을 구성할 수 있습니다.

## 학습 목표

1. NoSQL 데이터베이스의 개념과 관계형 데이터베이스(RDBMS)와의 차이를 이해한다
2. MongoDB의 문서(Document) 기반 데이터 모델을 이해하고 활용할 수 있다
3. `motor` 비동기 드라이버를 사용하여 FastAPI에서 MongoDB를 연동할 수 있다
4. MongoDB의 기본 CRUD 작업 (`insert_one`, `find`, `find_one`, `update_one`, `delete_one`)을 수행할 수 있다
5. Redis를 활용한 캐싱(Caching) 기초를 이해하고, TTL 기반 캐시를 구현할 수 있다
6. 비동기 방식으로 NoSQL 데이터베이스를 연동하는 패턴을 익힌다

## 핵심 개념

### NoSQL vs RDBMS

| 특성 | RDBMS (예: PostgreSQL) | NoSQL (예: MongoDB) |
|------|----------------------|-------------------|
| 데이터 구조 | 테이블, 행, 열 (고정 스키마) | 문서, 컬렉션 (유연한 스키마) |
| 스키마 | 엄격한 스키마 필수 | 스키마 없이 유연한 저장 가능 |
| 관계 | JOIN을 통한 관계 표현 | 내장(Embedded) 문서 또는 참조(Reference) |
| 확장 | 주로 수직 확장 (Scale-up) | 수평 확장 용이 (Scale-out) |
| 쿼리 언어 | SQL | 각 DB 고유 쿼리 (MongoDB Query Language) |
| 적합한 사용 사례 | 정형 데이터, 트랜잭션 중심 | 비정형 데이터, 빠른 읽기/쓰기 |

### MongoDB 핵심 개념

```
RDBMS          ↔  MongoDB
─────────────────────────────
Database       ↔  Database
Table          ↔  Collection
Row            ↔  Document (BSON/JSON)
Column         ↔  Field
Primary Key    ↔  _id (ObjectId)
```

### Redis 캐싱 개념

Redis는 인메모리(In-Memory) 키-값(Key-Value) 저장소로, 주로 캐싱에 사용됩니다.

```
[클라이언트] → [FastAPI] → [Redis 캐시 확인]
                              ├── 캐시 히트(Hit) → 즉시 반환 (빠름)
                              └── 캐시 미스(Miss) → [MongoDB 조회] → Redis에 저장 → 반환
```

- **TTL (Time To Live)**: 캐시 데이터의 유효 시간 설정
- **캐시 무효화**: 데이터 변경 시 관련 캐시를 삭제하여 일관성 유지

## 파일 구조

```
ch13_nosql/
├── README.md      # 이 문서
└── main.py        # MongoDB + Redis 연동 FastAPI 애플리케이션
```

## 사전 준비

### 1. 패키지 설치

```bash
pip install fastapi uvicorn motor redis
```

| 패키지 | 설명 |
|--------|------|
| `motor` | MongoDB용 비동기 드라이버 (PyMongo 기반) |
| `redis` | Redis용 Python 클라이언트 (비동기 지원 포함) |

### 2. MongoDB 실행

MongoDB가 `localhost:27017`에서 실행 중이어야 합니다.

```bash
# Docker를 사용한 MongoDB 실행
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:7

# 인증 없이 간단히 실행 (학습용)
docker run -d --name mongodb -p 27017:27017 mongo:7
```

### 3. Redis 실행

Redis가 `localhost:6379`에서 실행 중이어야 합니다.

```bash
# Docker를 사용한 Redis 실행
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine
```

### 4. Docker Compose로 한번에 실행 (권장)

```yaml
# docker-compose.yml
version: "3.8"
services:
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  mongo_data:
```

```bash
docker compose up -d
```

## 코드 실행 방법

```bash
# MongoDB와 Redis가 실행 중인지 확인
docker ps

# ch13_nosql 디렉토리에서 실행
cd phase3_database/ch13_nosql

# 개발 서버 실행 (자동 리로드 활성화)
uvicorn main:app --reload

# 특정 포트로 실행
uvicorn main:app --reload --port 8013
```

서버가 실행되면 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 실습 포인트

### 1단계: MongoDB 기본 CRUD
- [ ] 게시글(Post) 생성 API 호출 (POST /posts/)
- [ ] 전체 게시글 목록 조회 (GET /posts/)
- [ ] 특정 게시글 조회 (GET /posts/{post_id})
- [ ] 게시글 수정 (PUT /posts/{post_id})
- [ ] 게시글 삭제 (DELETE /posts/{post_id})

### 2단계: Redis 캐싱 동작 확인
- [ ] 게시글 조회 시 첫 번째 요청(캐시 미스)과 두 번째 요청(캐시 히트)의 응답 비교
- [ ] 게시글 수정/삭제 후 캐시가 무효화되는지 확인
- [ ] TTL 만료 후 캐시가 자동 삭제되는지 확인

### 3단계: MongoDB 고유 기능 탐색
- [ ] ObjectId 기반의 문서 식별 방식 이해
- [ ] 스키마 없이 다양한 필드를 가진 문서 저장 시도
- [ ] `find()`에 필터 조건을 추가하여 검색 기능 구현

### 4단계: 심화 실습
- [ ] 태그(tags) 필드를 추가하고 태그 기반 검색 구현
- [ ] 댓글(comments)을 내장 문서(Embedded Document)로 설계
- [ ] Redis를 활용한 조회수(view count) 카운터 구현
- [ ] MongoDB 인덱스 생성을 통한 검색 성능 최적화

## 참고 자료

- [Motor (MongoDB 비동기 드라이버) 문서](https://motor.readthedocs.io/)
- [MongoDB 공식 문서](https://www.mongodb.com/docs/)
- [Redis 공식 문서](https://redis.io/docs/)
- [redis-py (Python Redis 클라이언트) 문서](https://redis-py.readthedocs.io/)
- [FastAPI + MongoDB 예제](https://www.mongodb.com/developer/languages/python/python-quickstart-fastapi/)
