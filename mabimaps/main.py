# uvicorn main:app --reload
from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi import Path
from dotenv import load_dotenv
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional
import shutil
import os
from pathlib import Path as SysPath
from PIL import Image, UnidentifiedImageError

# .env 로드 (PORT/CORS 등 런타임 설정)
load_dotenv()

from database import get_db_connection
from models import ReportData, MarkerLocation

app = FastAPI()

# --- 업로드 이미지 검증 ---
# 요구사항: .jpg, .png, .webp 외에는 절대 거부
ALLOWED_IMAGE_EXTS = {".jpg", ".png", ".webp"}
ALLOWED_IMAGE_TYPES = {"jpeg", "png", "webp"}  # Pillow 포맷명

def _validate_image_upload(upload: UploadFile) -> str:
    """
    업로드된 이미지의 확장자/내용을 검증하고
    저장에 사용할 안전한 확장자를 반환한다.
    - Python 3.13에서 imghdr가 제거되어 Pillow(Image.verify) 기반으로 검사한다.
    """
    if not upload or not upload.filename:
        raise HTTPException(status_code=400, detail="image 파일이 필요합니다.")

    ext = SysPath(upload.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(
            status_code=415,
            detail="허용되지 않는 이미지 확장자입니다. (.jpg, .png, .webp 만 허용)",
        )

    # Pillow로 실제 이미지 포맷 검사 (손상/위장 방지)
    upload.file.seek(0)
    try:
        img = Image.open(upload.file)
        img.verify()  # 파일 손상/위조 검증
        fmt = (img.format or "").lower()
    except UnidentifiedImageError:
        raise HTTPException(status_code=415, detail="이미지 파일이 아니거나 손상된 파일입니다.")
    except Exception:
        raise HTTPException(status_code=415, detail="이미지 파일이 아니거나 손상된 파일입니다.")
    finally:
        upload.file.seek(0)

    if fmt not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="허용되지 않는 이미지 포맷입니다. (jpg/png/webp만 허용)")

    # 저장 확장자 통일
    if fmt == "jpeg":
        return ".jpg"
    return f".{fmt}"

# --- 경로 설정 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# CORS (배포용 권장 설정)
# 기본값은 동일 origin만 허용(가장 안전).
# 외부 도메인에서 프론트를 호스팅하는 경우, .env에서 CORS_ALLOW_ORIGINS에 허용할 origin을 넣어 사용.
# 예: CORS_ALLOW_ORIGINS=https://example.com,https://www.example.com
cors_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
allow_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()] if cors_origins_env else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,  # 빈 리스트면 CORS 비활성(= cross-site 브라우저 호출 차단)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def read_root():
    return FileResponse("index.html")


# 브라우저가 기본적으로 요청하는 리소스(콘솔 404 방지)
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    # 프로젝트 내에 별도 파비콘이 없으면 빈 204로 응답
    raise HTTPException(status_code=204)


@app.get("/robots.txt", include_in_schema=False)
def robots():
    # 크롤링 제어가 필요 없으므로 빈 204로 응답(콘솔 404 방지)
    raise HTTPException(status_code=204)


@app.get("/manifest.json", include_in_schema=False)
def manifest():
    # PWA 미사용. 콘솔 404 방지용으로 빈 204 응답.
    raise HTTPException(status_code=204)


@app.get("/apple-touch-icon.png", include_in_schema=False)
def apple_touch_icon():
    # iOS/Safari 기본 요청. 콘솔 404 방지용으로 빈 204 응답.
    raise HTTPException(status_code=204)


# Leaflet 기본 타일 경로가 남아있거나(혹은 이전 캐시) 브라우저가 요청할 수 있음.
# CRS.Simple 쓰는 현재 프로젝트에서는 사용하지 않으므로 204로 흡수.
@app.get("/{z}/{x}/{y}.png", include_in_schema=False)
def swallow_tile_png(z: str, x: str, y: str):
    raise HTTPException(status_code=204)


@app.get("/items/search")
def search_items_for_autocomplete(name: str, exact: bool = False):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if exact:
                query = "SELECT item_name FROM items WHERE LOWER(item_name) = LOWER(%s);"
                cur.execute(query, (name,))
            else:
                query = "SELECT item_name FROM items WHERE item_name ILIKE %s LIMIT 10;"
                cur.execute(query, (f"%{name}%",))

            results = cur.fetchall()
            if exact:
                return {"exists": len(results) > 0}
            return [row["item_name"] for row in results]
    finally:
        conn.close()


@app.get("/items/resolve")
def resolve_item_id(name: str):
    """
    아이템 이름으로 items.id 조회 (정확히 일치, 대소문자 무시).
    프론트에서 자동완성으로 고른 이름을 id로 "바인딩"하는 용도.
    """
    name = (name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name 파라미터가 필요합니다.")

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, item_name, image_url FROM items WHERE LOWER(item_name) = LOWER(%s) LIMIT 1;", (name,))
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다. (정확한 이름을 선택해주세요)")
            return row
    finally:
        conn.close()


@app.get("/search_sources")
def search_item_sources(name: str):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT i.item_name, i.image_url, s.price_value, s.price_type,
                       m.id as marker_id, m.name, m.description,
                       m.image_url as marker_image_url, ST_Y(m.geom) as lat, ST_X(m.geom) as lng
                FROM items i
                JOIN item_sources s ON i.id = s.item_id
                JOIN markers m ON s.marker_id = m.id
                WHERE i.item_name LIKE %s;
            """
            cur.execute(query, (f"%{name}%",))
            return cur.fetchall()
    finally:
        conn.close()


@app.get("/search")
def search_map_entities(keyword: str):
    """
    통합 검색.
    - marker_reports 신고 누적 5회 이상인 마커는 결과에서 제외.
    """
    keyword = keyword.strip()
    if not keyword:
        return []

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT *
                FROM (
                    SELECT
                        m.id AS marker_id,
                        m.name AS name,
                        m.category AS category,
                        m.area_id AS area_id,
                        ST_Y(m.geom) AS lat,
                        ST_X(m.geom) AS lng,
                        NULL::text AS item_name,
                        'marker' AS result_type
                    FROM markers m
                    LEFT JOIN (
                        SELECT marker_id, COUNT(*) AS report_count
                        FROM marker_reports
                        GROUP BY marker_id
                    ) mr ON mr.marker_id = m.id
                    WHERE m.name ILIKE %s
                      AND m.category = 'NPC'
                      AND COALESCE(mr.report_count, 0) < 5

                    UNION ALL

                    SELECT
                        m.id AS marker_id,
                        m.name AS name,
                        m.category AS category,
                        m.area_id AS area_id,
                        ST_Y(m.geom) AS lat,
                        ST_X(m.geom) AS lng,
                        i.item_name AS item_name,
                        'item' AS result_type
                    FROM items i
                    JOIN item_sources s ON i.id = s.item_id
                    JOIN markers m ON s.marker_id = m.id
                    LEFT JOIN (
                        SELECT marker_id, COUNT(*) AS report_count
                        FROM marker_reports
                        GROUP BY marker_id
                    ) mr ON mr.marker_id = m.id
                    WHERE i.item_name ILIKE %s
                      AND COALESCE(mr.report_count, 0) < 5
                ) search_results
                ORDER BY name, item_name NULLS FIRST
                LIMIT 20;
            """
            search_term = f"%{keyword}%"
            cur.execute(query, (search_term, search_term))
            return cur.fetchall()
    finally:
        conn.close()


@app.get("/markers")
def get_markers(area: Optional[str] = None):
    """
    마커 목록 조회.
    - marker_reports 신고 누적이 5회 이상인 마커는 반환하지 않음(숨김 처리).
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT m.id, m.name, m.category, m.description, m.image_url, m.area_id,
                       ST_X(m.geom) as lng, ST_Y(m.geom) as lat
                FROM markers m
                LEFT JOIN (
                    SELECT marker_id, COUNT(*) AS report_count
                    FROM marker_reports
                    GROUP BY marker_id
                ) mr ON mr.marker_id = m.id
            """
            params = []
            where = ["COALESCE(mr.report_count, 0) < 5"]
            if area is not None:
                where.append("m.area_id = %s")
                params.append(area)

            query += " WHERE " + " AND ".join(where)
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()


@app.get("/markers/{marker_id}/items")
def get_marker_items(marker_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT i.item_name, i.image_url, s.price_value, s.price_type, s.acquisition_condition, s.id as source_id
                FROM item_sources s
                JOIN items i ON s.item_id = i.id
                WHERE s.marker_id = %s AND s.dislike_count < 5;
            """
            cur.execute(query, (marker_id,))
            return cur.fetchall()
    finally:
        conn.close()


@app.get("/maps/config")
def get_map_config():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, img_path, bounds, view_config, parent_id, zones, area_for_markers FROM maps;")
            rows = cur.fetchall()
            return {
                row["id"]: {
                    "img": row["img_path"],
                    "bounds": row["bounds"],
                    "view": row["view_config"],
                    "parent": row["parent_id"],
                    "zones": row["zones"],
                    "areaForMarkers": row["area_for_markers"],
                }
                for row in rows
            }
    finally:
        conn.close()


@app.post("/item-sources/{source_id}/dislike")
def dislike_item_source(source_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM item_sources WHERE id = %s;", (source_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="해당 아이템 소스를 찾을 수 없습니다.")

            cur.execute(
                "UPDATE item_sources SET dislike_count = dislike_count + 1 WHERE id = %s;",
                (source_id,),
            )
            conn.commit()
            return {"status": "success", "message": "해당 아이템 정보에 대한 신고가 접수되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        print(f"Dislike 처리 중 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=f"신고 처리 중 오류가 발생했습니다: {e}")
    finally:
        conn.close()


@app.post("/markers/{marker_id}/report")
def report_marker(marker_id: int = Path(..., description="markers.id")):
    """
    마커 신고(=마커 자체에 대한 '싫어요/신고').
    - marker_reports에 row를 추가
    - 신고 누적 5회 이상인 마커는 GET /markers 에서 숨김 처리됨
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM markers WHERE id = %s;", (marker_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="마커를 찾을 수 없습니다.")

            cur.execute("INSERT INTO marker_reports (marker_id) VALUES (%s) RETURNING id;", (marker_id,))
            report_row = cur.fetchone()

            cur.execute("SELECT COUNT(*) AS report_count FROM marker_reports WHERE marker_id = %s;", (marker_id,))
            count_row = cur.fetchone()
            report_count = int(count_row["report_count"]) if count_row and count_row.get("report_count") is not None else 0

            conn.commit()
            return {
                "status": "success",
                "message": "마커 신고가 접수되었습니다.",
                "marker_id": marker_id,
                "report_id": report_row["id"] if report_row else None,
                "report_count": report_count,
                "hidden": report_count >= 5,
            }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"marker report 처리 중 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=f"마커 신고 처리 중 오류가 발생했습니다: {e}")
    finally:
        conn.close()


@app.post("/report-marker")
def create_marker_report(
    name: str = Form(...),
    category: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    area_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                INSERT INTO markers (name, category, description, area_id, geom)
                VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                RETURNING id;
            """
            # 클라이언트에서 보내는 area_id(=currentMapId)를 그대로 markers.area_id에 저장
            cur.execute(query, (name, category, description, area_id, lng, lat))
            marker_id_row = cur.fetchone()
            if not marker_id_row:
                raise HTTPException(status_code=500, detail="Failed to create marker and retrieve ID.")

            marker_id = marker_id_row["id"]
            image_url = None

            if image and image.filename:
                upload_dir = os.path.join(STATIC_DIR, "images", "markers")
                os.makedirs(upload_dir, exist_ok=True)

                file_extension = _validate_image_upload(image)
                image_filename = f"{marker_id}{file_extension}"
                image_path = os.path.join(upload_dir, image_filename)

                with open(image_path, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)

                image_url = f"/static/images/markers/{image_filename}"
                cur.execute("UPDATE markers SET image_url = %s WHERE id = %s;", (image_url, marker_id))

            conn.commit()
            return {
                "status": "success",
                "message": "새로운 마커가 성공적으로 등록되었습니다.",
                "marker_id": marker_id,
                "image_url": image_url,
                "area_id": area_id,
            }
    except Exception as e:
        conn.rollback()
        print(f"마커 등록 중 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=f"마커 등록 처리 중 오류 발생: {e}")
    finally:
        conn.close()


@app.post("/items/master")
def create_item_master(
    itemName: str = Form(...),
    image: Optional[UploadFile] = File(None),
):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM items WHERE item_name = %s;", (itemName,))
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="이미 등록된 아이템입니다.")

            cur.execute(
                "INSERT INTO items (item_name) VALUES (%s) RETURNING id;",
                (itemName,),
            )
            item_id_row = cur.fetchone()
            if not item_id_row:
                raise HTTPException(status_code=500, detail="아이템 생성 후 ID를 가져오지 못했습니다.")

            item_id = item_id_row["id"]
            image_url = None

            if image and image.filename:
                upload_dir = os.path.join(STATIC_DIR, "images", "items")
                os.makedirs(upload_dir, exist_ok=True)

                file_extension = _validate_image_upload(image)
                image_filename = f"{item_id}{file_extension}"
                image_path = os.path.join(upload_dir, image_filename)

                with open(image_path, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)

                image_url = f"/static/images/items/{image_filename}"
                cur.execute(
                    "UPDATE items SET image_url = %s WHERE id = %s;",
                    (image_url, item_id),
                )

            conn.commit()
            return {
                "status": "success",
                "message": "새로운 아이템이 성공적으로 등록되었습니다.",
                "item_id": item_id,
                "image_url": image_url,
            }
    except Exception as e:
        conn.rollback()
        if isinstance(e, psycopg2.Error):
            print(f"데이터베이스 에러: {e}")
            raise HTTPException(status_code=409, detail=f"데이터베이스 처리 중 오류 발생: {e}")
        print(f"아이템 마스터 등록 중 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=f"아이템 마스터 등록 처리 중 오류 발생: {e}")
    finally:
        conn.close()


@app.post("/items/{item_id}/image")
def update_item_image(
    item_id: int = Path(..., description="items.id"),
    image: UploadFile = File(...),
):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM items WHERE id = %s;", (item_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")

            if not image or not image.filename:
                raise HTTPException(status_code=400, detail="image 파일이 필요합니다.")

            upload_dir = os.path.join(STATIC_DIR, "images", "items")
            os.makedirs(upload_dir, exist_ok=True)

            file_extension = _validate_image_upload(image)
            image_filename = f"{item_id}{file_extension}"
            image_path = os.path.join(upload_dir, image_filename)

            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            image_url = f"/static/images/items/{image_filename}"
            cur.execute("UPDATE items SET image_url = %s WHERE id = %s;", (image_url, item_id))

            conn.commit()
            return {
                "status": "success",
                "message": "아이템 이미지가 업데이트되었습니다.",
                "item_id": item_id,
                "image_url": image_url,
            }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"아이템 이미지 업데이트 중 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=f"아이템 이미지 업데이트 처리 중 오류 발생: {e}")
    finally:
        conn.close()


@app.patch("/items/{item_id}/name")
def update_item_name(
    item_id: int = Path(..., description="items.id"),
    new_name: str = Form(...),
):
    """
    아이템 이름 변경.
    - 프론트에서 '기존 이름 자동완성 → /items/resolve로 id 바인딩' 후 item_id를 사용
    - new_name으로 items.item_name 업데이트
    - 새 이름이 이미 존재하면 409(중복 방지)
    """
    new_name = (new_name or "").strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="new_name이 비어있습니다.")

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM items WHERE id = %s;", (item_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")

            # 중복 이름 방지
            cur.execute("SELECT id FROM items WHERE LOWER(item_name) = LOWER(%s) AND id <> %s;", (new_name, item_id))
            if cur.fetchone() is not None:
                raise HTTPException(status_code=409, detail="이미 존재하는 아이템 이름입니다.")

            cur.execute("UPDATE items SET item_name = %s WHERE id = %s RETURNING id, item_name, image_url;", (new_name, item_id))
            updated = cur.fetchone()
            conn.commit()

            return {
                "status": "success",
                "message": "아이템 이름이 업데이트되었습니다.",
                "item": updated,
            }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"아이템 이름 업데이트 중 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=f"아이템 이름 업데이트 처리 중 오류 발생: {e}")
    finally:
        conn.close()


@app.post("/markers/{marker_id}/image")
def update_marker_image(
    marker_id: int = Path(..., description="markers.id"),
    image: UploadFile = File(...),
):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM markers WHERE id = %s;", (marker_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="마커를 찾을 수 없습니다.")

            if not image or not image.filename:
                raise HTTPException(status_code=400, detail="image 파일이 필요합니다.")

            upload_dir = os.path.join(STATIC_DIR, "images", "markers")
            os.makedirs(upload_dir, exist_ok=True)

            file_extension = _validate_image_upload(image)
            image_filename = f"{marker_id}{file_extension}"
            image_path = os.path.join(upload_dir, image_filename)

            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            image_url = f"/static/images/markers/{image_filename}"
            cur.execute("UPDATE markers SET image_url = %s WHERE id = %s;", (image_url, marker_id))

            conn.commit()
            return {
                "status": "success",
                "message": "마커 이미지가 업데이트되었습니다.",
                "marker_id": marker_id,
                "image_url": image_url,
            }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"마커 이미지 업데이트 중 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=f"마커 이미지 업데이트 처리 중 오류 발생: {e}")
    finally:
        conn.close()


@app.post("/report")
def receive_report(
    itemName: str = Form(...),
    acquireMethod: str = Form(...),
    acquisition_condition: Optional[str] = Form(None),
    price_value: Optional[int] = Form(None),
    price_type: Optional[str] = Form(None),
    lat: Optional[float] = Form(None),
    lng: Optional[float] = Form(None),
    markerId: Optional[int] = Form(None),
    area_id: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, image_url FROM items WHERE item_name = %s;", (itemName,))
            item_row = cur.fetchone()
            item_id = None

            if item_row:
                item_id = item_row["id"]
                if not item_row["image_url"] and image and image.filename:
                    upload_dir = os.path.join(STATIC_DIR, "images", "items")
                    os.makedirs(upload_dir, exist_ok=True)
                    file_extension = _validate_image_upload(image)
                    image_filename = f"{item_id}{file_extension}"
                    image_path = os.path.join(upload_dir, image_filename)
                    with open(image_path, "wb") as buffer:
                        shutil.copyfileobj(image.file, buffer)
                    image_url = f"/static/images/items/{image_filename}"
                    cur.execute("UPDATE items SET image_url = %s WHERE id = %s;", (image_url, item_id))
            else:
                cur.execute("INSERT INTO items (item_name) VALUES (%s) RETURNING id;", (itemName,))
                item_id_row = cur.fetchone()
                if not item_id_row:
                    raise HTTPException(status_code=500, detail="Failed to create item and retrieve ID.")
                item_id = item_id_row["id"]

                if image and image.filename:
                    upload_dir = os.path.join(STATIC_DIR, "images", "items")
                    os.makedirs(upload_dir, exist_ok=True)
                    file_extension = _validate_image_upload(image)
                    image_filename = f"{item_id}{file_extension}"
                    image_path = os.path.join(upload_dir, image_filename)
                    with open(image_path, "wb") as buffer:
                        shutil.copyfileobj(image.file, buffer)
                    image_url = f"/static/images/items/{image_filename}"
                    cur.execute("UPDATE items SET image_url = %s WHERE id = %s;", (image_url, item_id))

            actual_marker_id = markerId
            if actual_marker_id is None and lat is not None and lng is not None:
                marker_name = f"{itemName} 획득처 (제보)"
                marker_desc = f"사용자 제보: '{itemName}' 획득 가능"
                cur.execute(
                    """
                    INSERT INTO markers (name, description, category, area_id, geom)
                    VALUES (%s, %s, '제보', %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                    RETURNING id;
                    """,
                    (marker_name, marker_desc, area_id, lng, lat),
                )
                marker_id_row = cur.fetchone()
                if not marker_id_row:
                    raise HTTPException(status_code=500, detail="Failed to create marker and retrieve ID.")
                actual_marker_id = marker_id_row["id"]

            if actual_marker_id is None:
                raise HTTPException(status_code=400, detail="마커 ID 또는 좌표가 필요합니다.")

            final_condition = acquireMethod
            if acquisition_condition:
                final_condition += f": {acquisition_condition}"

            cur.execute(
                """
                INSERT INTO item_sources (item_id, marker_id, price_value, price_type, acquisition_condition)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (item_id, marker_id) DO UPDATE
                SET price_value = EXCLUDED.price_value,
                    price_type = EXCLUDED.price_type,
                    acquisition_condition = EXCLUDED.acquisition_condition;
                """,
                (item_id, actual_marker_id, price_value, price_type, final_condition),
            )
            conn.commit()
            return {"status": "success", "message": "제보가 성공적으로 처리되었습니다."}
    except Exception as e:
        conn.rollback()
        print(f"An error occurred in /report endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.patch("/markers/{marker_id}/location")
async def update_marker_location(marker_id: int, loc: MarkerLocation):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM markers WHERE id = %s;", (marker_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="마커를 찾을 수 없습니다.")

            cur.execute(
                """
                UPDATE markers
                SET geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                WHERE id = %s
                RETURNING id, ST_Y(geom) AS lat, ST_X(geom) AS lng;
                """,
                (loc.lng, loc.lat, marker_id),
            )
            updated = cur.fetchone()
            conn.commit()

            return {
                "status": "success",
                "marker_id": updated["id"],
                "lat": updated["lat"],
                "lng": updated["lng"],
            }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        print(f"마커 위치 수정 중 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=f"마커 위치 수정 중 오류 발생: {e}")
    finally:
        conn.close()


@app.post("/maps")
async def create_map(
    id: str = Form(...),
    bounds: str = Form(...),
    parent_id: Optional[str] = Form(None),
    area_for_markers: Optional[str] = Form(None),
    view_config: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
):
    """
    새 맵 생성:
    - image 업로드가 있으면 static/maps/ 에 저장하고 img_path 생성
    - maps 테이블에 레코드 INSERT
    bounds/view_config는 프론트에서 JSON.stringify(...)된 문자열로 받는다.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM maps WHERE id = %s;", (id,))
            if cur.fetchone() is not None:
                raise HTTPException(status_code=409, detail="이미 존재하는 map id 입니다.")

            img_path = None
            if image and image.filename:
                upload_dir = os.path.join(STATIC_DIR, "maps")
                os.makedirs(upload_dir, exist_ok=True)

                ext = _validate_image_upload(image)
                safe_filename = f"{id}{ext}"
                file_path = os.path.join(upload_dir, safe_filename)

                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)

                img_path = f"/static/maps/{safe_filename}"
            else:
                raise HTTPException(status_code=400, detail="새 맵 생성에는 image 파일이 필요합니다.")

            # zones는 기본 null로
            cur.execute(
                """
                INSERT INTO maps (id, img_path, bounds, view_config, parent_id, zones, area_for_markers)
                VALUES (%s, %s, %s::jsonb, %s::jsonb, %s, NULL, %s)
                RETURNING id, img_path;
                """,
                (id, img_path, bounds, view_config, parent_id, area_for_markers),
            )
            row = cur.fetchone()
            conn.commit()
            return {"status": "success", "map": row}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"/maps 생성 중 에러: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.patch("/maps/{map_id}/zones")
async def append_map_zone(
    map_id: str,
    bounds: str = Form(...),
    target: str = Form(...),
):
    """
    기존 맵(map_id)의 zones(JSONB)에 새 이동영역을 append.
    zones 포맷은 maps.csv와 동일: [{"bounds": [[y,x],[y,x]], "target":"..."}]
    bounds는 프론트에서 JSON.stringify([[y1,x1],[y2,x2]]) 로 전달.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, zones FROM maps WHERE id = %s;", (map_id,))
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="map_id를 찾을 수 없습니다.")

            # target 맵 존재 확인(선택적이지만 안전)
            cur.execute("SELECT id FROM maps WHERE id = %s;", (target,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="target map_id를 찾을 수 없습니다.")

            import json

            # bounds는 JSON 문자열로 들어오므로 파싱 후 안전하게 jsonb로 캐스팅
            try:
                parsed_bounds = json.loads(bounds)
            except Exception:
                raise HTTPException(status_code=400, detail="bounds JSON 파싱에 실패했습니다.")

            new_zone_obj = {"bounds": parsed_bounds, "target": target}
            new_zone_json = json.dumps(new_zone_obj, ensure_ascii=False)

            # zones가 NULL이면 새 배열로 시작, 아니면 배열에 append
            cur.execute(
                """
                UPDATE maps
                SET zones = CASE
                    WHEN zones IS NULL THEN jsonb_build_array(%s::jsonb)
                    ELSE (zones || jsonb_build_array(%s::jsonb))
                END
                WHERE id = %s
                RETURNING id, zones;
                """,
                (new_zone_json, new_zone_json, map_id),
            )
            updated = cur.fetchone()
            conn.commit()
            return {"status": "success", "map_id": updated["id"], "zones": updated["zones"]}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"/maps/{map_id}/zones append 중 에러: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.patch("/maps/{map_id}/image")
async def update_map_image(
    map_id: str,
    image: UploadFile = File(...),
):
    """
    현재 맵(map_id)의 이미지 교체:
    - static/maps/ 에 {map_id}.{ext} 로 저장
    - maps.img_path 갱신
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM maps WHERE id = %s;", (map_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="map_id를 찾을 수 없습니다.")

            if not image or not image.filename:
                raise HTTPException(status_code=400, detail="image 파일이 필요합니다.")

            upload_dir = os.path.join(STATIC_DIR, "maps")
            os.makedirs(upload_dir, exist_ok=True)

            ext = _validate_image_upload(image)
            safe_filename = f"{map_id}{ext}"
            file_path = os.path.join(upload_dir, safe_filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            img_path = f"/static/maps/{safe_filename}"
            cur.execute("UPDATE maps SET img_path = %s WHERE id = %s RETURNING id, img_path;", (img_path, map_id))
            updated = cur.fetchone()
            conn.commit()

            return {
                "status": "success",
                "message": "맵 이미지가 업데이트되었습니다.",
                "map": updated,
                "image_url": img_path,
            }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"/maps/{map_id}/image 업데이트 중 에러: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
