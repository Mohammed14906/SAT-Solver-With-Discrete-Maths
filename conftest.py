"""
conftest.py
Adds the sat_solver root to sys.path so tests can import local modules
regardless of which directory pytest is invoked from.
"""
import sys
import os

# Ensure the sat_solver package root is on the path
sys.path.insert(0, os.path.dirname(__file__))
