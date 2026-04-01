import os
import json
import csv

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# .env 로드 (없어도 기본값으로 동작)
load_dotenv()

# 1. DB 연결 정보 (환경변수 사용)
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "mabinogi_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
    )

# 2. maps.csv 파일에서 데이터를 읽어와 DB에 마이그레이션합니다.
def migrate():
    print("맵 설정 데이터베이스 마이그레이션을 시작합니다 (from maps.csv)...")
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 3. 테이블 생성 (기존에 있다면 삭제 후 재생성)
        print("   - 기존 maps 테이블 삭제...")
        cur.execute("DROP TABLE IF EXISTS maps;")
        
        print("   - 새로운 maps 테이블 생성...")
        cur.execute("""
            CREATE TABLE maps (
                id VARCHAR(50) PRIMARY KEY,
                img_path VARCHAR(255),
                bounds JSONB,
                view_config JSONB,
                parent_id VARCHAR(50),
                zones JSONB,
                area_for_markers VARCHAR(50)
            );
        """)

        # 4. maps.csv 데이터 삽입
        print("   - maps.csv 파일 읽는 중...")
        with open('maps.csv', mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            print("   - 맵 설정 데이터 삽입 중...")
            for row in reader:
                # NULL 문자열을 None으로 변환
                parent_id = row['parent_id'] if row['parent_id'] and row['parent_id'] != 'NULL' else None
                area_for_markers = row['area_for_markers'] if row['area_for_markers'] and row['area_for_markers'] != 'NULL' else None
                
                # JSON 문자열을 파싱
                try:
                    bounds_json = json.loads(row['bounds']) if row['bounds'] else None
                    view_config_json = json.loads(row['view_config']) if row['view_config'] and row['view_config'] != 'null' else None
                    zones_json = json.loads(row['zones']) if row['zones'] and row['zones'] != 'null' else None
                except json.JSONDecodeError as e:
                    print(f"   - WARNING: ID '{row['id']}'의 JSON 파싱 오류: {e}. 해당 row를 건너뜁니다.")
                    continue

                cur.execute("""
                    INSERT INTO maps (id, img_path, bounds, view_config, parent_id, zones, area_for_markers)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (
                    row['id'],
                    row['img_path'],
                    psycopg2.extras.Json(bounds_json),
                    psycopg2.extras.Json(view_config_json),
                    parent_id,
                    psycopg2.extras.Json(zones_json),
                    area_for_markers
                ))
        
        conn.commit()
        print("마이그레이션 성공!")

    except Exception as e:
        conn.rollback()
        print(f"마이그레이션 실패: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
