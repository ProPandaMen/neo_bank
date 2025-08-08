from database.base import SessionLocal
from sqlalchemy.orm import object_session


class BaseModel:
    @classmethod
    def create(cls, **kwargs):
        db = SessionLocal()
        obj = cls(**kwargs)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        db.close()
        return obj

    @classmethod
    def get(cls, **kwargs):
        db = SessionLocal()
        obj = db.query(cls).filter_by(**kwargs).first()
        db.close()
        return obj

    @classmethod
    def all(cls):
        db = SessionLocal()
        objs = db.query(cls).order_by(cls.created_at.desc()).all()
        db.close()
        return objs
    
    @classmethod
    def filter(cls, order_by=None, limit: int | None = None, offset: int | None = None, **kwargs):
        db = SessionLocal()
        try:
            q = db.query(cls).filter_by(**kwargs)
            if order_by is None and hasattr(cls, "created_at"):
                q = q.order_by(cls.created_at.desc())
            elif order_by is not None:
                if isinstance(order_by, (list, tuple)):
                    q = q.order_by(*order_by)
                else:
                    q = q.order_by(order_by)
            if offset:
                q = q.offset(offset)
            if limit:
                q = q.limit(limit)
            return q.all()
        finally:
            db.close()

    def save(self):
        sess = object_session(self) or SessionLocal()
        sess.add(self)
        sess.commit()
        sess.refresh(self)
        if not object_session(self):
            sess.close()
