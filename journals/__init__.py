"""
Journals module initialization
Loading celery app so that task registration and discovery can work correctly.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
