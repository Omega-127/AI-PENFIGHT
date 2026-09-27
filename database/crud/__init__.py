"""
AI Penfight - Database CRUD Module
Exports all entity repositories for clean import throughout the application.
"""

from database.crud.user import UserRepository
from database.crud.interaction import InteractionRepository
from database.crud.analysis import AnalysisRepository
from database.crud.feedback import FeedbackRepository
from database.crud.performance import PerformanceRepository
from database.crud.rollup import PerformanceRollupRepository

__all__ = [
    "UserRepository",
    "InteractionRepository",
    "AnalysisRepository",
    "FeedbackRepository",
    "PerformanceRepository",
    "PerformanceRollupRepository",
]
