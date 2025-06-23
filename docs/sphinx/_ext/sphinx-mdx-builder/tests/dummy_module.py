"""Dummy Python module for testing sphinx-mdx-builder.

This module contains various Python constructs to test the MDX generation.
"""

from enum import Enum
from typing import Any, Optional


def decorator_with_args(**kwargs):
    """A decorator that takes arguments to simulate @logger decorator."""

    def decorator(func):
        func.decorator_metadata = kwargs
        return func

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


@decorator_with_args(
    config={"log_level": "INFO", "name": "test_logger"},
    description="A test decorated logger function.",
)
def test_decorated_logger(init_context=None):
    """This is a test function with a decorator to replicate the colored_console_logger issue.

    This function simulates the dagster._loggers.colored_console_logger pattern
    where source links might be missing for decorated functions.

    Args:
        init_context: The initialization context (optional)

    Returns:
        str: A test logger message
    """
    return f"Test logger initialized with context: {init_context}"
