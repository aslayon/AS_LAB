import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# .env 로드 (비밀번호/접속정보는 코드에 두지 않고 환경변수로 관리)
load_dotenv()


def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "mabinogi_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        port=os.getenv("DB_PORT", "5432"),
        cursor_factory=RealDictCursor,
    )
    return conn
