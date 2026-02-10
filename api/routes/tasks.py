from datetime import datetime, timezone
from typing import Any, cast

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import asc, desc, func, or_
from sqlmodel import select

from db import get_session
from exceptions import TaskNotFoundException
from logger import setup_logger
from models import (
    VALID_PRIORITY,
    VALID_STATUS,
    BulkDeletePayload,
    Task,
    TaskCreate,
    TaskOut,
    TaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = setup_logger("tasks")

TASK_COLUMNS = cast(Any, Task).__table__.c


def task_to_out(task: Task, subtasks: list[Task] = None) -> TaskOut:
    return TaskOut(
        id=task.id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=task.status,
        due_date=task.due_date,
        tags=task.tags,
        parent_id=task.parent_id,
        recurrence=task.recurrence,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        subtasks=[task_to_out(st) for st in (subtasks or [])]
    )


SORT_MAP = {
    "created_at": asc(TASK_COLUMNS.created_at),
    "-created_at": desc(TASK_COLUMNS.created_at),
    "updated_at": asc(TASK_COLUMNS.updated_at),
    "-updated_at": desc(TASK_COLUMNS.updated_at),
    "priority": asc(TASK_COLUMNS.priority),
    "-priority": desc(TASK_COLUMNS.priority),
    "status": asc(TASK_COLUMNS.status),
    "-status": desc(TASK_COLUMNS.status),
    "title": asc(TASK_COLUMNS.title),
    "-title": desc(TASK_COLUMNS.title),
}


@router.get("", response_model=list[TaskOut])
def list_tasks(
    q: str | None = Query(None, max_length=200),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    tags: str | None = Query(None, max_length=200),
    sort: str = Query("-created_at"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_subtasks: bool = Query(True),
):
    stmt = select(Task).where(TASK_COLUMNS.parent_id.is_(None))

    if q:
        stmt = stmt.where(TASK_COLUMNS.title.ilike(f"%{q}%"))
    if status:
        if status not in VALID_STATUS:
            raise HTTPException(400, f"Invalid status. Must be one of: {VALID_STATUS}")
        stmt = stmt.where(TASK_COLUMNS.status == status)
    if priority:
        if priority not in VALID_PRIORITY:
            raise HTTPException(400, f"Invalid priority. Must be one of: {VALID_PRIORITY}")
        stmt = stmt.where(TASK_COLUMNS.priority == priority)
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        tag_conditions = [TASK_COLUMNS.tags.ilike(f"%{tag}%") for tag in tag_list]
        stmt = stmt.where(or_(*tag_conditions))

    if sort not in SORT_MAP:
        raise HTTPException(400, f"Invalid sort. Must be one of: {list(SORT_MAP.keys())}")

    stmt = stmt.order_by(SORT_MAP[sort]).offset(offset).limit(limit)

    with get_session() as session:
        tasks = list(session.exec(stmt))

        if include_subtasks:
            task_ids = [t.id for t in tasks]
            all_subtasks = list(session.exec(
                select(Task).where(Task.parent_id.in_(task_ids))
            ))
            subtasks_map = {}
            for st in all_subtasks:
                subtasks_map.setdefault(st.parent_id, []).append(st)

            return [task_to_out(t, subtasks_map.get(t.id, [])) for t in tasks]

        return [task_to_out(t) for t in tasks]


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    with get_session() as session:
        if payload.parent_id:
            parent = session.get(Task, payload.parent_id)
            if not parent:
                raise HTTPException(400, f"Parent task {payload.parent_id} not found")

        task = Task(
            title=payload.title.strip(),
            description=payload.description.strip() if payload.description else None,
            priority=payload.priority,
            status="todo",
            parent_id=payload.parent_id,
            due_date=payload.due_date,
            tags=payload.tags,
            recurrence=payload.recurrence,
        )

        session.add(task)
        session.commit()
        session.refresh(task)
        logger.info(f"Created task #{task.id}: {task.title}")
        return task_to_out(task)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int):
    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            raise TaskNotFoundException(task_id)

        subtasks = list(session.exec(select(Task).where(Task.parent_id == task_id)))
        return task_to_out(task, subtasks)


@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate):
    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            raise TaskNotFoundException(task_id)

        if payload.title is not None:
            task.title = payload.title.strip()
        if payload.description is not None:
            task.description = payload.description.strip() if payload.description else None
        if payload.priority is not None:
            task.priority = payload.priority
        if payload.status is not None:
            old_status = task.status
            task.status = payload.status

            if payload.status == "done" and old_status != "done":
                task.completed_at = datetime.now(timezone.utc)
            elif payload.status != "done" and old_status == "done":
                task.completed_at = None
        if payload.due_date is not None:
            task.due_date = payload.due_date
        if payload.tags is not None:
            task.tags = payload.tags
        if payload.recurrence is not None:
            task.recurrence = payload.recurrence

        task.updated_at = datetime.now(timezone.utc)
        session.add(task)
        session.commit()
        session.refresh(task)

        subtasks = list(session.exec(select(Task).where(Task.parent_id == task_id)))
        logger.info(f"Updated task #{task.id}")
        return task_to_out(task, subtasks)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            raise TaskNotFoundException(task_id)

        subtasks = list(session.exec(select(Task).where(Task.parent_id == task_id)))
        for st in subtasks:
            session.delete(st)

        session.delete(task)
        session.commit()
        logger.info(f"Deleted task #{task_id} and {len(subtasks)} subtasks")


@router.post("/bulk-delete", status_code=status.HTTP_204_NO_CONTENT)
def bulk_delete_tasks(payload: BulkDeletePayload):
    with get_session() as session:
        tasks = session.exec(select(Task).where(Task.id.in_(payload.ids))).all()

        for task in tasks:
            subtasks = list(session.exec(select(Task).where(Task.parent_id == task.id)))
            for st in subtasks:
                session.delete(st)
            session.delete(task)

        session.commit()
        logger.info(f"Bulk deleted {len(tasks)} tasks")


@router.get("/stats/summary", response_model=dict)
def get_stats():
    with get_session() as session:
        total = session.exec(select(func.count(Task.id)).where(Task.parent_id.is_(None))).one()

        by_status = {}
        for s in VALID_STATUS:
            count = session.exec(
                select(func.count(Task.id)).where(Task.status == s, Task.parent_id.is_(None))
            ).one()
            by_status[s] = count

        by_priority = {}
        for p in VALID_PRIORITY:
            count = session.exec(
                select(func.count(Task.id)).where(Task.priority == p, Task.parent_id.is_(None))
            ).one()
            by_priority[p] = count

        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
        }


@router.get("/tags/all", response_model=list[str])
def get_all_tags():
    with get_session() as session:
        tags_results = list(session.exec(
            select(Task.tags).where(Task.tags.is_not(None), Task.tags != "")
        ))

        unique_tags = set()
        for tags_str in tags_results:
            if tags_str:
                unique_tags.update(t.strip() for t in tags_str.split(",") if t.strip())

        return sorted(unique_tags)
