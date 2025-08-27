"""Dummy Python module for testing sphinx-mdx-builder.

This module contains various Python constructs to test the MDX generation.
"""

from enum import Enum
from typing import Any, Optional


class LoggerDefinition:
    """A mock LoggerDefinition class that simulates Dagster's LoggerDefinition."""

    def __init__(self, logger_fn, config_schema=None, description=None):
        self._logger_fn = logger_fn
        self.config_schema = config_schema
        self.description = description

    @property
    def logger_fn(self):
        """Access the underlying logger function."""
        return self._logger_fn


def logger(config_schema=None, description=None):
    """A decorator that simulates Dagster's @logger decorator.

    This returns a LoggerDefinition object instead of the function directly,
    which is the key difference that causes source link issues.
    """

    def decorator(func):
        return LoggerDefinition(
            logger_fn=func, config_schema=config_schema, description=description
        )

    return decorator


class GenericWrapper:
    """A generic wrapper class that demonstrates common wrapping patterns."""

    def __init__(self, func, pattern_name="func"):
        # Store the function using different attribute patterns
        if pattern_name == "func":
            self.func = func
        elif pattern_name == "function":
            self.function = func
        elif pattern_name == "wrapped":
            self.wrapped = func
        elif pattern_name == "callback":
            self.callback = func
        else:
            # Default to func
            self.func = func
        self.pattern_name = pattern_name


def generic_wrapper(pattern_name="func"):
    """A decorator that creates various types of function wrappers."""

    def decorator(func):
        return GenericWrapper(func, pattern_name)

    return decorator


class Color(Enum):
    """Color enumeration for testing enum documentation."""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class Vehicle:
    """Base vehicle class.

    This is a base class that demonstrates class documentation
    with attributes and methods.

    Attributes:
        make: The vehicle manufacturer
        model: The vehicle model
        year: The manufacturing year
    """

    def __init__(self, make: str, model: str, year: int):
        """Initialize a new vehicle.

        Args:
            make: The vehicle manufacturer
            model: The vehicle model
            year: The manufacturing year
        """
        self.make = make
        self.model = model
        self.year = year

    def start_engine(self) -> bool:
        """Start the vehicle engine.

        Returns:
            True if engine started successfully, False otherwise
        """
        return True

    def get_info(self) -> dict[str, Any]:
        """Get vehicle information.

        Returns:
            Dictionary containing vehicle details
        """
        return {"make": self.make, "model": self.model, "year": self.year}


class Car(Vehicle):
    """Car class extending Vehicle.

    A specific type of vehicle with additional car-specific features.

    Attributes:
        doors: Number of doors
        color: Car color from Color enum
    """

    def __init__(self, make: str, model: str, year: int, doors: int, color: Color):
        """Initialize a new car.

        Args:
            make: The car manufacturer
            model: The car model
            year: The manufacturing year
            doors: Number of doors
            color: Car color
        """
        super().__init__(make, model, year)
        self.doors = doors
        self.color = color

    def honk_horn(self) -> str:
        """Make the car honk.

        Returns:
            The sound of the horn
        """
        return "Beep beep!"


def calculate_fuel_efficiency(distance: float, fuel_used: float) -> float:
    """Calculate fuel efficiency.

    Args:
        distance: Distance traveled in miles
        fuel_used: Amount of fuel used in gallons

    Returns:
        Miles per gallon

    Raises:
        ValueError: If fuel_used is zero or negative
    """
    if fuel_used <= 0:
        raise ValueError("Fuel used must be positive")
    return distance / fuel_used


def find_cars_by_color(cars: list[Car], color: Color) -> list[Car]:
    """Find all cars with a specific color.

    Args:
        cars: List of cars to search
        color: Color to search for

    Returns:
        List of cars matching the specified color
    """
    return [car for car in cars if car.color == color]


def get_car_summary(car: Optional[Car] = None) -> str:
    """Get a summary of a car.

    Args:
        car: Car to summarize, None for default message

    Returns:
        String summary of the car
    """
    if car is None:
        return "No car provided"

    return f"{car.year} {car.make} {car.model} ({car.color.value}, {car.doors} doors)"


# Module-level constants
DEFAULT_CAR_COLOR = Color.BLUE
MAX_VEHICLE_AGE = 50

# Example usage data
EXAMPLE_CARS = [
    Car("Toyota", "Camry", 2020, 4, Color.BLUE),
    Car("Honda", "Civic", 2019, 4, Color.RED),
    Car("Ford", "Mustang", 2021, 2, Color.RED),
]


@logger(
    config_schema={"log_level": "INFO", "name": "test_logger"},
    description="A test decorated logger function.",
)
def test_dagster_style_logger(init_context=None):
    """This is a test function with a decorator to replicate the colored_console_logger issue.

    This function simulates the dagster._loggers.colored_console_logger pattern
    where source links might be missing for decorated functions.

    Args:
        init_context: The initialization context (optional)

    Returns:
        str: A test logger message
    """
    return f"Test logger initialized with context: {init_context}"


@generic_wrapper(pattern_name="func")
def test_func_wrapper(param1, param2="default"):
    """A function wrapped using the 'func' attribute pattern.

    This tests the most common wrapper pattern where the function
    is stored in a 'func' attribute.
    """
    return f"Function called with {param1} and {param2}"


@generic_wrapper(pattern_name="function")
def test_function_wrapper(data):
    """A function wrapped using the 'function' attribute pattern.

    This tests an alternative naming convention for storing functions.
    """
    return f"Processing data: {data}"


@generic_wrapper(pattern_name="callback")
def test_callback_wrapper():
    """A function wrapped using the 'callback' attribute pattern.

    This tests callback-style wrappers common in event systems.
    """
    return "Callback executed"
