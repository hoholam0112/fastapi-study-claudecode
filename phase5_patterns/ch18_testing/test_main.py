"""
Chapter 18: FastAPI 테스트 - 테스트 모듈

FastAPI의 TestClient와 pytest를 사용하여
아이템 CRUD API의 각 엔드포인트를 검증한다.

실행 방법:
    pytest test_main.py -v
"""

import pytest
from fastapi.testclient import TestClient

from main import app, get_db

# ============================================================
# pytest fixture 정의
# fixture는 테스트 함수에 필요한 사전 설정을 제공한다.
# 여러 테스트에서 공통으로 사용하는 객체를 한 곳에서 관리할 수 있다.
# ============================================================


@pytest.fixture
def test_db():
    """
    테스트 전용 인메모리 데이터베이스를 생성하는 fixture.

    각 테스트마다 새로운 빈 딕셔너리를 생성하므로
    테스트 간 데이터 격리가 보장된다.
    """
    return {}


@pytest.fixture
def client(test_db):
    """
    TestClient를 생성하는 fixture.

    의존성 오버라이드를 통해 테스트 전용 DB를 주입하고,
    테스트 완료 후 오버라이드를 정리한다.
    이를 통해 각 테스트가 독립적인 환경에서 실행된다.
    """
    # 의존성 오버라이드: get_db가 호출될 때 test_db를 반환하도록 교체
    def override_get_db():
        return test_db

    app.dependency_overrides[get_db] = override_get_db

    # TestClient를 생성하여 테스트에 제공
    with TestClient(app) as c:
        yield c

    # 테스트 종료 후 오버라이드 정리 (다른 테스트에 영향을 주지 않도록)
    app.dependency_overrides.clear()


# ============================================================
# 아이템 생성 테스트 (POST /items/)
# ============================================================
class TestCreateItem:
    """아이템 생성 엔드포인트 테스트 그룹"""

    def test_create_item(self, client):
        """
        정상적인 아이템 생성 테스트.

        201 Created 상태 코드와 함께
        생성된 아이템 데이터가 올바르게 반환되는지 확인한다.
        """
        # Given: 생성할 아이템 데이터
        item_data = {
            "name": "테스트 아이템",
            "description": "테스트용 설명입니다",
            "price": 15000.0,
        }

        # When: POST 요청으로 아이템 생성
        response = client.post("/items/", json=item_data)

        # Then: 201 상태 코드와 올바른 응답 데이터 확인
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == item_data["name"]
        assert data["description"] == item_data["description"]
        assert data["price"] == item_data["price"]
        assert "id" in data  # 자동 생성된 ID가 포함되어야 함

    def test_create_item_without_description(self, client):
        """
        설명(description) 없이 아이템을 생성하는 테스트.

        description은 선택 필드이므로 없어도 정상 생성되어야 한다.
        """
        item_data = {"name": "설명 없는 아이템", "price": 5000.0}

        response = client.post("/items/", json=item_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "설명 없는 아이템"
        assert data["description"] is None

    def test_create_item_invalid_price(self, client):
        """
        유효하지 않은 가격(0 이하)으로 아이템 생성 시도.

        Pydantic 유효성 검증에 의해 422 에러가 반환되어야 한다.
        """
        item_data = {"name": "잘못된 아이템", "price": -100.0}

        response = client.post("/items/", json=item_data)

        # 유효성 검증 실패 시 422 Unprocessable Entity 반환
        assert response.status_code == 422


# ============================================================
# 아이템 목록 조회 테스트 (GET /items/)
# ============================================================
class TestReadItems:
    """아이템 목록 조회 엔드포인트 테스트 그룹"""

    def test_read_items_empty(self, client):
        """
        아이템이 없을 때 빈 목록 반환 테스트.

        초기 상태에서는 빈 리스트가 반환되어야 한다.
        """
        response = client.get("/items/")

        assert response.status_code == 200
        assert response.json() == []

    def test_read_items(self, client):
        """
        아이템 생성 후 목록 조회 테스트.

        생성한 아이템들이 목록에 포함되어 있어야 한다.
        """
        # 아이템 2개 생성
        client.post("/items/", json={"name": "아이템 A", "price": 1000.0})
        client.post("/items/", json={"name": "아이템 B", "price": 2000.0})

        # 목록 조회
        response = client.get("/items/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # 생성한 아이템 이름들이 목록에 포함되어 있는지 확인
        names = [item["name"] for item in data]
        assert "아이템 A" in names
        assert "아이템 B" in names


# ============================================================
# 단일 아이템 조회 테스트 (GET /items/{item_id})
# ============================================================
class TestReadItem:
    """단일 아이템 조회 엔드포인트 테스트 그룹"""

    def test_read_item(self, client):
        """
        존재하는 아이템의 개별 조회 테스트.

        생성한 아이템을 ID로 정확히 조회할 수 있어야 한다.
        """
        # 아이템 생성
        create_response = client.post(
            "/items/", json={"name": "조회용 아이템", "price": 3000.0}
        )
        created_item = create_response.json()
        item_id = created_item["id"]

        # ID로 아이템 조회
        response = client.get(f"/items/{item_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert data["name"] == "조회용 아이템"
        assert data["price"] == 3000.0

    def test_read_item_not_found(self, client):
        """
        존재하지 않는 아이템 조회 시 404 에러 테스트.

        없는 ID로 조회하면 404 Not Found가 반환되어야 한다.
        """
        # 존재하지 않는 ID(99999)로 조회 시도
        response = client.get("/items/99999")

        assert response.status_code == 404
        data = response.json()
        assert "찾을 수 없습니다" in data["detail"]


# ============================================================
# 아이템 삭제 테스트 (DELETE /items/{item_id})
# ============================================================
class TestDeleteItem:
    """아이템 삭제 엔드포인트 테스트 그룹"""

    def test_delete_item(self, client):
        """
        아이템 삭제 테스트.

        생성한 아이템을 삭제한 후,
        다시 조회하면 404가 반환되어야 한다.
        """
        # 아이템 생성
        create_response = client.post(
            "/items/", json={"name": "삭제할 아이템", "price": 7000.0}
        )
        item_id = create_response.json()["id"]

        # 아이템 삭제
        delete_response = client.delete(f"/items/{item_id}")
        assert delete_response.status_code == 200
        assert "삭제되었습니다" in delete_response.json()["message"]

        # 삭제된 아이템 재조회 시 404 확인
        get_response = client.get(f"/items/{item_id}")
        assert get_response.status_code == 404

    def test_delete_item_not_found(self, client):
        """
        존재하지 않는 아이템 삭제 시 404 에러 테스트.

        없는 ID로 삭제를 시도하면 404 Not Found가 반환되어야 한다.
        """
        response = client.delete("/items/99999")

        assert response.status_code == 404


# ============================================================
# 의존성 오버라이드 테스트
#
# 의존성 오버라이드는 테스트에서 핵심적인 기법이다.
# 실제 데이터베이스나 외부 서비스 대신
# 테스트 전용 모의 객체(mock)를 주입하여 테스트를 격리할 수 있다.
# ============================================================
class TestDependencyOverride:
    """의존성 오버라이드 패턴 테스트 그룹"""

    def test_with_pre_populated_db(self):
        """
        미리 데이터가 채워진 DB를 주입하는 의존성 오버라이드 테스트.

        테스트 시작 전에 특정 데이터가 존재하는 상태를
        의존성 오버라이드로 구성할 수 있다.
        """
        # 미리 채워진 테스트용 DB 생성
        pre_populated_db = {
            1: {
                "id": 1,
                "name": "사전 등록 아이템",
                "description": "오버라이드로 주입된 아이템",
                "price": 9900.0,
            },
            2: {
                "id": 2,
                "name": "두 번째 아이템",
                "description": None,
                "price": 4500.0,
            },
        }

        # 의존성 오버라이드 적용
        def override_get_db():
            return pre_populated_db

        app.dependency_overrides[get_db] = override_get_db

        # 오버라이드된 DB로 테스트 수행
        with TestClient(app) as client:
            # 목록 조회 - 미리 등록된 2개의 아이템이 반환되어야 함
            response = client.get("/items/")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

            # 특정 아이템 조회
            response = client.get("/items/1")
            assert response.status_code == 200
            assert response.json()["name"] == "사전 등록 아이템"

        # 오버라이드 정리
        app.dependency_overrides.clear()

    def test_override_isolation(self):
        """
        의존성 오버라이드가 다른 테스트에 영향을 주지 않는지 확인하는 테스트.

        오버라이드를 적용한 후 반드시 정리(clear)해야
        다른 테스트에 영향을 주지 않는다.
        """
        # 빈 DB로 오버라이드
        empty_db: dict = {}

        def override_get_db():
            return empty_db

        app.dependency_overrides[get_db] = override_get_db

        with TestClient(app) as client:
            response = client.get("/items/")
            assert response.status_code == 200
            assert response.json() == []

        # 정리 후 오버라이드가 비어 있는지 확인
        app.dependency_overrides.clear()
        assert len(app.dependency_overrides) == 0
