from abc import ABC, abstractmethod


class SQLClient(ABC):
    """An interface for a SQL client that can connect to a database and execute SQL queries."""

    @abstractmethod
    def connect_and_execute(self, sql: str) -> None:
        """Connect to the SQL database and execute the SQL query."""
        ...
