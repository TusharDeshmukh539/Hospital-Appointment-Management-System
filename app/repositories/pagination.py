from sqlalchemy import func, select
from sqlalchemy.orm import Session


def paginate(db: Session, query, page: int, size: int):
    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    total = db.scalar(count_query) or 0
    rows = db.scalars(query.offset((page - 1) * size).limit(size)).unique().all()
    return list(rows), total


def apply_order(column, sort_order: str):
    """Return the column ordered ascending or descending."""
    return column.desc() if sort_order == "desc" else column.asc()
