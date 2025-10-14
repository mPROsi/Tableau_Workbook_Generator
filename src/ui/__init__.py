"""
UI package for the Tableau Dashboard Generator.
Provides Streamlit-based web interface for dashboard generation.
"""

from .streamlit_app import StreamlitApp, main

__all__ = [
    "StreamlitApp",
    "main"
]