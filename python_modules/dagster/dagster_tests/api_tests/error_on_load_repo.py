"""
A target that errors on load.
"""
from dagster import In, Out, op

raise ValueError("User did something bad")
