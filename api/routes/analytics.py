"""Analytics and productivity statistics endpoints."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from sqlalchemy import func
from sqlmodel import select

from db import get_session
from logger import setup_logger
from models import Task

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = setup_logger("analytics")


@router.get("/tasks/daily")
def get_daily_task_stats(days: int = 30):
    """Get task completion stats for the last N days."""
    with get_session() as session:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get completed tasks grouped by day
        statement = (
            select(
                func.date(Task.completed_at).label("date"),
                func.count(Task.id).label("count"),
            )
            .where(Task.completed_at.is_not(None))
            .where(Task.completed_at >= start_date)
            .where(Task.parent_id.is_(None))
            .group_by(func.date(Task.completed_at))
            .order_by(func.date(Task.completed_at))
        )

        results = session.exec(statement).all()

        # Fill in missing days with 0
        date_counts = {str(r.date): r.count for r in results}
        daily_stats = []

        for i in range(days):
            date = (start_date + timedelta(days=i)).date()
            daily_stats.append({
                "date": str(date),
                "completed": date_counts.get(str(date), 0),
            })

        return daily_stats


@router.get("/tasks/weekly")
def get_weekly_task_stats(weeks: int = 12):
    """Get task completion stats for the last N weeks."""
    with get_session() as session:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(weeks=weeks)

        # Get completed tasks grouped by week
        statement = (
            select(
                func.strftime("%Y-%W", Task.completed_at).label("week"),
                func.count(Task.id).label("count"),
            )
            .where(Task.completed_at.is_not(None))
            .where(Task.completed_at >= start_date)
            .where(Task.parent_id.is_(None))
            .group_by(func.strftime("%Y-%W", Task.completed_at))
            .order_by(func.strftime("%Y-%W", Task.completed_at))
        )

        results = session.exec(statement).all()

        return [{"week": r.week, "completed": r.count} for r in results]


@router.get("/tasks/by-priority")
def get_tasks_by_priority():
    """Get task distribution by priority."""
    with get_session() as session:
        statement = (
            select(Task.priority, func.count(Task.id).label("count"))
            .where(Task.parent_id.is_(None))
            .group_by(Task.priority)
        )

        results = session.exec(statement).all()

        return {r.priority: r.count for r in results}


@router.get("/tasks/by-status")
def get_tasks_by_status():
    """Get task distribution by status."""
    with get_session() as session:
        statement = (
            select(Task.status, func.count(Task.id).label("count"))
            .where(Task.parent_id.is_(None))
            .group_by(Task.status)
        )

        results = session.exec(statement).all()

        return {r.status: r.count for r in results}


@router.get("/tasks/completion-rate")
def get_completion_rate():
    """Get overall task completion rate."""
    with get_session() as session:
        total = session.exec(
            select(func.count(Task.id)).where(Task.parent_id.is_(None))
        ).one()

        completed = session.exec(
            select(func.count(Task.id))
            .where(Task.status == "done")
            .where(Task.parent_id.is_(None))
        ).one()

        rate = (completed / total * 100) if total > 0 else 0

        return {
            "total": total,
            "completed": completed,
            "pending": total - completed,
            "completion_rate": round(rate, 1),
        }


@router.get("/tasks/average-completion-time")
def get_average_completion_time():
    """Get average time to complete tasks (in hours)."""
    with get_session() as session:
        # Get tasks that have both created_at and completed_at
        statement = select(Task).where(
            Task.completed_at.is_not(None),
            Task.parent_id.is_(None),
        )

        tasks = session.exec(statement).all()

        if not tasks:
            return {"average_hours": 0, "task_count": 0}

        total_hours = 0
        for task in tasks:
            if task.completed_at and task.created_at:
                delta = task.completed_at - task.created_at
                total_hours += delta.total_seconds() / 3600

        avg_hours = total_hours / len(tasks) if tasks else 0

        return {
            "average_hours": round(avg_hours, 1),
            "task_count": len(tasks),
        }


@router.get("/productivity/summary")
def get_productivity_summary():
    """Get a complete productivity summary."""
    with get_session() as session:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = today_start.replace(day=1)

        # Tasks completed today
        today_completed = session.exec(
            select(func.count(Task.id))
            .where(Task.completed_at >= today_start)
            .where(Task.parent_id.is_(None))
        ).one()

        # Tasks completed this week
        week_completed = session.exec(
            select(func.count(Task.id))
            .where(Task.completed_at >= week_start)
            .where(Task.parent_id.is_(None))
        ).one()

        # Tasks completed this month
        month_completed = session.exec(
            select(func.count(Task.id))
            .where(Task.completed_at >= month_start)
            .where(Task.parent_id.is_(None))
        ).one()

        # Total tasks
        total_tasks = session.exec(
            select(func.count(Task.id)).where(Task.parent_id.is_(None))
        ).one()

        # Pending tasks
        pending_tasks = session.exec(
            select(func.count(Task.id))
            .where(Task.status.in_(["todo", "doing"]))
            .where(Task.parent_id.is_(None))
        ).one()

        # Overdue tasks
        overdue_tasks = session.exec(
            select(func.count(Task.id))
            .where(Task.due_date < now)
            .where(Task.status.in_(["todo", "doing"]))
            .where(Task.parent_id.is_(None))
        ).one()

        # Completed tasks total
        completed_total = session.exec(
            select(func.count(Task.id))
            .where(Task.status == "done")
            .where(Task.parent_id.is_(None))
        ).one()

        # Calculate completion rate
        completion_rate = round((completed_total / total_tasks * 100), 1) if total_tasks > 0 else 0

        return {
            "today_completed": today_completed,
            "week_completed": week_completed,
            "month_completed": month_completed,
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "overdue": overdue_tasks,
            "completion_rate": completion_rate,
        }
