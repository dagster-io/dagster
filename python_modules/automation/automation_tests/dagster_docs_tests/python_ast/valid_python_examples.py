"""Docstring fixtures with valid Python code blocks."""

from dagster._annotations import public


@public
class ValidPythonFixtures:
    """Fixtures for testing valid Python syntax in docstrings."""

    @public
    def simple_python_function(self):
        """Example with simple Python function.

        Examples:
            Basic Python function:

            .. code-block:: python

                def hello_world():
                    return "Hello, World!"

                result = hello_world()
                print(result)
        """
        pass

    @public
    def python_with_imports_and_classes(self):
        """Example with Python imports and classes.

        Examples:
            Python with imports and class definition:

            .. code-block:: python

                from typing import List, Optional
                import json

                class DataProcessor:
                    def __init__(self, config: dict):
                        self.config = config

                    def process(self, data: List[dict]) -> Optional[dict]:
                        if not data:
                            return None

                        processed = []
                        for item in data:
                            processed.append({
                                'id': item.get('id'),
                                'value': item.get('value', 0) * 2
                            })

                        return {
                            'count': len(processed),
                            'items': processed
                        }
        """
        pass

    @public
    def python_with_decorators_and_async(self):
        """Example with Python decorators and async functions.

        Examples:
            Advanced Python with decorators and async:

            .. code-block:: python

                import asyncio
                from functools import wraps

                def retry(max_attempts: int = 3):
                    def decorator(func):
                        @wraps(func)
                        async def wrapper(*args, **kwargs):
                            for attempt in range(max_attempts):
                                try:
                                    return await func(*args, **kwargs)
                                except Exception as e:
                                    if attempt == max_attempts - 1:
                                        raise
                                    await asyncio.sleep(2 ** attempt)
                        return wrapper
                    return decorator

                @retry(max_attempts=5)
                async def fetch_data(url: str) -> dict:
                    # Simulated async data fetching
                    await asyncio.sleep(1)
                    return {"url": url, "data": "fetched"}
        """
        pass
