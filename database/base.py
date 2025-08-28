from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

from config import LOCAL_DATABASE_URL, DOCKER_DATABASE_URL


Base = declarative_base()

_engine = None
SessionLocal = None


def _with_timeout(url: str) -> str:
    return url if "connect_timeout=" in url else url + ("&" if "?" in url else "?") + "connect_timeout=3"


def init_engine():
    global _engine, SessionLocal
    urls = [LOCAL_DATABASE_URL, DOCKER_DATABASE_URL]
    last_err = None
    for raw in urls:
        url = _with_timeout(raw)
        try:
            eng = create_engine(url, pool_pre_ping=True)
            with eng.connect() as c:
                c.execute(text("select 1"))
            _engine = eng
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
            return
        except SQLAlchemyError as e:
            last_err = e
            continue
    raise RuntimeError(f"DB unavailable: {last_err}")


init_engine()
