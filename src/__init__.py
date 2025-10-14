"""
Tableau Dashboard Generator - AI-Powered Dashboard Creation
==========================================================

A production-grade application that uses AI to automatically generate Tableau dashboards
from uploaded data. Features include:

- AI-powered data analysis and visualization recommendations
- Meta-prompting for intelligent dashboard design
- Automatic Tableau workbook (.twb/.twbx) generation
- Langgraph workflow orchestration
- Streamlit web interface
- Comprehensive logging and error handling

Usage:
    streamlit run main.py

Components:
    - models: Data models and schemas
    - ai_engine: AI analysis and meta-prompting
    - tableau_engine: Tableau workbook generation
    - workflows: Langgraph workflow orchestration
    - ui: Streamlit web interface
    - utils: Configuration, logging, and utilities
"""

__version__ = "1.0.0"
__author__ = "AI Dashboard Generator Team"
__description__ = "AI-powered automatic Tableau dashboard generation"

# Package imports
from .models import *
from .utils import get_config, get_logger, init_default_logging
from .ai_engine import TableauDashboardAnalyzer
from .tableau_engine import TableauWorkbookGenerator
from .workflows import DashboardGenerationWorkflow
from .ui import StreamlitApp

__all__ = [
    # Version info
    "__version__",
    "__author__", 
    "__description__",
    
    # Core components
    "TableauDashboardAnalyzer",
    "TableauWorkbookGenerator", 
    "DashboardGenerationWorkflow",
    "StreamlitApp",
    
    # Utilities
    "get_config",
    "get_logger",
    "init_default_logging"
]