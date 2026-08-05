import os
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shopsense.database")

MYSQL_URL = os.getenv("MYSQL_DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/shopsense_db")
FALLBACK_SQLITE_URL = "sqlite:///./shopsense_fallback.db"

def get_engine():
    """Attempt MySQL connection; fallback gracefully to SQLite if MySQL is unavailable."""
    try:
        engine = create_engine(MYSQL_URL, pool_pre_ping=True, connect_args={"connect_timeout": 3})
        # Test connection
        with engine.connect() as conn:
            logger.info("Successfully connected to MySQL Database!")
        return engine
    except Exception as e:
        logger.warning(f"Could not connect to MySQL database ({e}). Falling back to local SQLite database for preview.")
        
        # Self-healing: if SQLite database file exists with outdated schema, reset fallback DB
        sqlite_file = "./shopsense_fallback.db"
        engine = create_engine(FALLBACK_SQLITE_URL, connect_args={"check_same_thread": False})
        
        try:
            inspector = inspect(engine)
            if "vendors" in inspector.get_table_names():
                columns = [c["name"] for c in inspector.get_columns("vendors")]
                if "status" not in columns:
                    logger.info("Detected outdated SQLite fallback schema. Refreshing fallback DB...")
                    engine.dispose()
                    if os.path.exists(sqlite_file):
                        os.remove(sqlite_file)
                    engine = create_engine(FALLBACK_SQLITE_URL, connect_args={"check_same_thread": False})
        except Exception:
            pass

        return engine

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
