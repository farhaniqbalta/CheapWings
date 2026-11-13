"""Shared pydantic TypeAdapters.

Building a TypeAdapter compiles a validation/serialization schema (milliseconds
each); the P4.12 profile showed thousands rebuilt per search. Reuse one per type.
"""

from functools import lru_cache

from pydantic import TypeAdapter

adapter = lru_cache(maxsize=None)(TypeAdapter)
