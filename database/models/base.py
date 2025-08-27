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
    def all(cls, order_by=None):
        db = SessionLocal()
        q = db.query(cls)
        if order_by is None and hasattr(cls, "created_at"):
            q = q.order_by(cls.created_at.desc())
        elif order_by is None and hasattr(cls, "id"):
            q = q.order_by(cls.id.desc())
        elif order_by is not None:
            q = q.order_by(*order_by) if isinstance(order_by, (list, tuple)) else q.order_by(order_by)
        objs = q.all()
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
                q = q.order_by(*order_by) if isinstance(order_by, (list, tuple)) else q.order_by(order_by)
            if offset:
                q = q.offset(offset)
            if limit:
                q = q.limit(limit)
            return q.all()
        finally:
            db.close()

    @classmethod
    def filter_ex(cls, where=None, order_by=None, limit=None, offset=None, for_update=False, skip_locked=False, db=None):
        owns = db is None
        db = db or SessionLocal()
        try:
            q = db.query(cls)
            if where:
                if isinstance(where, (list, tuple)):
                    for cond in where:
                        q = q.filter(cond)
                else:
                    q = q.filter(where)
            if order_by is None and hasattr(cls, "created_at"):
                q = q.order_by(cls.created_at.desc())
            elif order_by is not None:
                q = q.order_by(*order_by) if isinstance(order_by, (list, tuple)) else q.order_by(order_by)
            if for_update:
                q = q.with_for_update(skip_locked=skip_locked)
            if offset:
                q = q.offset(offset)
            if limit:
                q = q.limit(limit)
            return q.all()
        finally:
            if owns:
                db.close()

    def delete(self):
        sess = object_session(self) or SessionLocal()
        sess.delete(self)
        sess.commit()
        if not object_session(self):
            sess.close()

    @classmethod
    def delete_where(cls, where=None):
        db = SessionLocal()
        try:
            q = db.query(cls)
            if where:
                if isinstance(where, (list, tuple)):
                    for cond in where:
                        q = q.filter(cond)
                else:
                    q = q.filter(where)
            q.delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()
            
    def save(self):
        sess = object_session(self) or SessionLocal()
        sess.add(self)
        sess.commit()
        sess.refresh(self)
        if not object_session(self):
            sess.close()
