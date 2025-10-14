"""
Workflows package for the Tableau Dashboard Generator.
Provides Langgraph-based workflow orchestration for dashboard generation.
"""

from .dashboard_workflow import DashboardGenerationWorkflow, WorkflowState

__all__ = [
    "DashboardGenerationWorkflow",
    "WorkflowState"
]