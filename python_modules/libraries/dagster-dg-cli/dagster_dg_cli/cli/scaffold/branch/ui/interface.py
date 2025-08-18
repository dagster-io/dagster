"""UI abstraction interface for scaffold branch command."""

from abc import ABC, abstractmethod
from typing import Optional


class ScaffoldUI(ABC):
    """Abstract UI interface for scaffold operations using reconciliation pattern."""
    
    @abstractmethod
    def render_state(self, state) -> None:
        """Render the complete UI state (reconciliation pattern).
        
        Args:
            state: ScaffoldState containing complete UI state
        """
        pass
    
    @abstractmethod
    def get_user_input(self, prompt: str, input_type: str = "text") -> str:
        """Get user input with specified prompt.
        
        Args:
            prompt: Text prompt to display to user
            input_type: Type of input expected (default: "text")
            
        Returns:
            User input as string
        """
        pass
    
    @abstractmethod
    def get_plan_approval(self, plan_content: str) -> tuple[bool, Optional[str]]:
        """Get user approval for a plan.
        
        Args:
            plan_content: The plan content to review
            
        Returns:
            Tuple of (approved, feedback) where approved indicates if the user
            approved the plan, and feedback contains refinement suggestions if not approved
        """
        pass
    
    @abstractmethod
    def confirm_action(self, message: str) -> bool:
        """Get user confirmation for an action.
        
        Args:
            message: Confirmation message to display
            
        Returns:
            True if user confirmed, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up UI resources (spinners, etc.)."""
        pass