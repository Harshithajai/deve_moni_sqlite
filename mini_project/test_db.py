from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

url = os.getenv("DATABASE_URL")

print("DATABASE_URL:", url)

try:
    engine = create_engine(url, pool_pre_ping=True)

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("DATABASE CONNECTION SUCCESSFUL!")
        print(result.fetchone())

except Exception as e:
    print("DATABASE CONNECTION FAILED!")
    print(type(e).__name__)
    print(e)