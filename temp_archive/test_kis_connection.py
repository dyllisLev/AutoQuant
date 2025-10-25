import os
import sys
from dotenv import load_dotenv
from src.database.database import Database

load_dotenv()

print("=" * 80)
print("🔍 KIS PostgreSQL 연결 테스트")
print("=" * 80)

print("\n1️⃣ 환경 변수 확인:")
db_type = os.getenv('DB_TYPE')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')

print(f"   DB_TYPE: {db_type}")
print(f"   DB_HOST: {db_host}")
print(f"   DB_PORT: {db_port}")
print(f"   DB_NAME: {db_name}")
print(f"   DB_USER: {db_user}")
print(f"   DB_PASSWORD: {'설정됨' if os.getenv('DB_PASSWORD') else '미설정'}")

if not db_host or not db_user:
    print("\n❌ KIS DB 연결 정보가 불완전합니다")
    print("   .env 파일에 다음을 설정해야 합니다:")
    print("   - DB_TYPE=postgresql")
    print("   - DB_HOST=***REDACTED_HOST***")
    print("   - DB_PORT=5432")
    print("   - DB_NAME=kis_db")
    print("   - DB_USER=kis_user")
    print("   - DB_PASSWORD=kis_password")
    sys.exit(1)

print("\n2️⃣ Database 연결 시도:")
try:
    db = Database()
    print("   ✅ 연결 성공!")
except Exception as e:
    print(f"   ❌ 연결 실패: {str(e)}")
    print(f"   원인: {type(e).__name__}")
    sys.exit(1)

print("\n3️⃣ KIS 실제 주식 조회 시도:")
try:
    available_symbols = db.get_available_symbols_from_kis()
    print(f"   ✅ 조회 성공!")
    print(f"   조회된 주식 수: {len(available_symbols)}")
    print(f"   처음 10개: {available_symbols[:10]}")
    print(f"   마지막 10개: {available_symbols[-10:]}")
except Exception as e:
    print(f"   ❌ 조회 실패: {str(e)}")
    print(f"   원인: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ KIS DB 연결 및 데이터 조회 완료")
print("=" * 80)
