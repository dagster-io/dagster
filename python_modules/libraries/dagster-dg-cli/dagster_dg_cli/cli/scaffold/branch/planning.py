"""Dynamic planning system for scaffold branch command.

This module implements the Dynamic Planning System that generates human-readable
implementation plans before code execution, enables plan review and refinement,
and provides bidirectional communication with Claude for interactive sessions.
"""

from pathlib import Path
from typing import Any, Optional

import click
from dagster_dg_core.context import DgContext
from dagster_shared.record import record

from dagster_dg_cli.cli.scaffold.branch.claude.client import ClaudeClient
from dagster_dg_cli.cli.scaffold.branch.claude.diagnostics import ClaudeDiagnostics


@record
class PlanStep:
    """Individual step in a generated implementation plan.

    Attributes:
        title: Brief description of the step
        description: Detailed explanation of what this step accomplishes
        files_to_analyze: List of files that should be analyzed for this step
        files_to_modify: List of files that will be created/modified in this step
        dependencies: List of step IDs that must be completed before this step
        estimated_complexity: Rough complexity estimate (low, medium, high)
    """

    id: str
    title: str
    description: str
    files_to_analyze: list[str]
    files_to_modify: list[str]
    dependencies: list[str]
    estimated_complexity: str


@record
class Plan:
    """Structured representation of a generated implementation plan.

    Attributes:
        title: High-level title describing what the plan accomplishes
        summary: Brief summary of the overall approach
        steps: List of individual steps to execute
        risks: List of potential risks and mitigation strategies
        prerequisites: List of requirements before starting implementation
        success_criteria: List of criteria to verify successful completion
        metadata: Additional metadata about plan generation
    """

    title: str
    summary: str
    steps: list[PlanStep]
    risks: list[str]
    prerequisites: list[str]
    success_criteria: list[str]
    metadata: dict[str, Any]


@record
class PlanningContext:
    """Context information for plan generation.

    Attributes:
        user_input: Original user request
        dg_context: Dagster project context
        codebase_patterns: Detected patterns from codebase analysis
        existing_components: List of available components
        project_structure: Overview of project file structure
    """

    user_input: str
    dg_context: DgContext
    codebase_patterns: dict[str, Any]
    existing_components: list[str]
    project_structure: dict[str, Any]


class PlanRenderer:
    """Formats plans into readable markdown output."""

    def render_plan(self, plan: Plan) -> str:
        """Render a plan as readable markdown.

        Args:
            plan: The plan to render

        Returns:
            Markdown-formatted string representation of the plan
        """
        lines = []
        lines.append(f"# {plan.title}")
        lines.append("")
        lines.append(f"**Summary:** {plan.summary}")
        lines.append("")

        if plan.prerequisites:
            lines.append("## Prerequisites")
            lines.append("")
            for prereq in plan.prerequisites:
                lines.append(f"- {prereq}")
            lines.append("")

        lines.append("## Implementation Steps")
        lines.append("")

        for i, step in enumerate(plan.steps, 1):
            lines.append(f"### Step {i}: {step.title}")
            lines.append("")
            lines.append(f"**Complexity:** {step.estimated_complexity}")
            lines.append("")
            lines.append(step.description)
            lines.append("")

            if step.files_to_analyze:
                lines.append("**Files to Analyze:**")
                for file_path in step.files_to_analyze:
                    lines.append(f"- {file_path}")
                lines.append("")

            if step.files_to_modify:
                lines.append("**Files to Create/Modify:**")
                for file_path in step.files_to_modify:
                    lines.append(f"- {file_path}")
                lines.append("")

            if step.dependencies:
                lines.append("**Dependencies:**")
                for dep_id in step.dependencies:
                    # Find the step title for this dependency
                    dep_step = next((s for s in plan.steps if s.id == dep_id), None)
                    if dep_step:
                        lines.append(f"- Step: {dep_step.title}")
                    else:
                        lines.append(f"- Step ID: {dep_id}")
                lines.append("")

        if plan.success_criteria:
            lines.append("## Success Criteria")
            lines.append("")
            for criterion in plan.success_criteria:
                lines.append(f"- {criterion}")
            lines.append("")

        if plan.risks:
            lines.append("## Potential Risks")
            lines.append("")
            for risk in plan.risks:
                lines.append(f"- {risk}")
            lines.append("")

        return "\n".join(lines)


class PlanGenerator:
    """Main orchestrator for plan generation and refinement."""

    def __init__(self, claude_client: ClaudeClient, diagnostics: ClaudeDiagnostics):
        """Initialize the plan generator.

        Args:
            claude_client: Client for AI interactions
            diagnostics: Diagnostics service for logging
        """
        self.claude_client = claude_client
        self.diagnostics = diagnostics
        self.renderer = PlanRenderer()

    def generate_initial_plan(self, context: PlanningContext) -> Plan:
        """Generate initial implementation plan from user input.

        Args:
            context: Planning context with user input and project information

        Returns:
            Generated implementation plan

        Raises:
            Exception: If plan generation fails
        """
        self.diagnostics.info(
            "planning_generation_start",
            "Starting initial plan generation",
            {
                "user_input_length": len(context.user_input),
                "available_components": len(context.existing_components),
            },
        )

        prompt = self._load_planning_prompt("initial_plan.md", context)

        from dagster_dg_cli.cli.scaffold.branch.constants import ALLOWED_COMMANDS_PLANNING

        allowed_tools = ALLOWED_COMMANDS_PLANNING.copy()

        # Use Claude to generate structured plan
        from dagster_dg_cli.cli.scaffold.branch.claude.client import NullOutputChannel

        messages = self.claude_client.invoke(
            prompt=prompt,
            allowed_tools=allowed_tools,
            output_channel=NullOutputChannel(),
            disallowed_tools=["Bash(python:*)", "WebSearch", "WebFetch"],
            verbose=False,
        )

        # Parse the response to extract plan structure
        # For now, create a basic plan - full parsing will be implemented later
        plan = Plan(
            title=f"Implementation Plan: {context.user_input}",
            summary="Generated implementation plan based on user requirements",
            steps=[
                PlanStep(
                    id="step_1",
                    title="Analyze Requirements",
                    description="Review user requirements and identify necessary components",
                    files_to_analyze=[],
                    files_to_modify=[],
                    dependencies=[],
                    estimated_complexity="low",
                ),
            ],
            risks=[],
            prerequisites=[],
            success_criteria=[],
            metadata={
                "generation_method": "initial_claude_generation",
                "messages_count": len(messages),
            },
        )

        self.diagnostics.info(
            "planning_generation_completed",
            "Initial plan generation completed",
            {
                "plan_title": plan.title,
                "steps_count": len(plan.steps),
            },
        )

        return plan

    def refine_plan(self, current_plan: Plan, user_feedback: str) -> Plan:
        """Refine existing plan based on user feedback.

        Args:
            current_plan: The current plan to refine
            user_feedback: User feedback for plan improvements

        Returns:
            Refined implementation plan
        """
        self.diagnostics.info(
            "planning_refinement_start",
            "Starting plan refinement",
            {
                "current_steps_count": len(current_plan.steps),
                "feedback_length": len(user_feedback),
            },
        )

        # Create refinement context
        refinement_context = {
            "current_plan": self.renderer.render_plan(current_plan),
            "user_feedback": user_feedback,
        }

        prompt = self._load_planning_prompt("plan_refinement.md", refinement_context)

        from dagster_dg_cli.cli.scaffold.branch.constants import ALLOWED_COMMANDS_PLANNING

        allowed_tools = ALLOWED_COMMANDS_PLANNING.copy()

        from dagster_dg_cli.cli.scaffold.branch.claude.client import NullOutputChannel

        messages = self.claude_client.invoke(
            prompt=prompt,
            allowed_tools=allowed_tools,
            output_channel=NullOutputChannel(),
            disallowed_tools=["Bash(python:*)", "WebSearch", "WebFetch"],
            verbose=False,
        )

        # For now, return the current plan with updated metadata
        # Full refinement parsing will be implemented later
        refined_plan = current_plan.replace(
            metadata={
                **current_plan.metadata,
                "refinement_method": "claude_refinement",
                "refinement_messages": len(messages),
                "user_feedback": user_feedback,
            }
        )

        self.diagnostics.info(
            "planning_refinement_completed",
            "Plan refinement completed",
            {
                "refined_steps_count": len(refined_plan.steps),
            },
        )

        return refined_plan

    def _load_planning_prompt(self, prompt_filename: str, context: Any) -> str:
        """Load a planning prompt template and inject context.

        Args:
            prompt_filename: The name of the prompt file (e.g., 'initial_plan.md')
            context: The context to inject into the prompt

        Returns:
            The formatted prompt string
        """
        prompt_path = Path(__file__).parent / "prompts" / "planning" / prompt_filename

        if not prompt_path.exists():
            # Fallback to basic prompt if template doesn't exist yet
            if prompt_filename == "initial_plan.md":
                return self._get_basic_initial_plan_prompt(context)
            elif prompt_filename == "plan_refinement.md":
                return self._get_basic_refinement_prompt(context)
            else:
                raise FileNotFoundError(f"Planning prompt template not found: {prompt_filename}")

        template = prompt_path.read_text()

        if isinstance(context, PlanningContext):
            return template.format(
                user_input=context.user_input,
                project_structure=context.project_structure,
                existing_components=", ".join(context.existing_components),
                codebase_patterns=context.codebase_patterns,
            )
        elif isinstance(context, dict):
            return template.format(**context)
        else:
            return template.format(context=context)

    def _get_basic_initial_plan_prompt(self, context: PlanningContext) -> str:
        """Get basic initial planning prompt when template doesn't exist yet."""
        return f"""
You are tasked with creating a detailed implementation plan for a Dagster project request.

User Request: {context.user_input}

Available Components: {", ".join(context.existing_components)}

Please generate a structured implementation plan that includes:
1. Clear steps to accomplish the user's goal
2. Files that need to be analyzed or modified
3. Prerequisites and dependencies
4. Success criteria for completion

Focus on being specific about what files to examine and what changes to make.
Prefer using existing Dagster components and patterns where possible.

Generate a comprehensive plan that someone could follow to implement this request.
"""

    def _get_basic_refinement_prompt(self, context: dict[str, Any]) -> str:
        """Get basic refinement prompt when template doesn't exist yet."""
        return f"""
You are refining an implementation plan based on user feedback.

Current Plan:
{context.get("current_plan", "")}

User Feedback:
{context.get("user_feedback", "")}

Please generate an updated implementation plan that addresses the user's feedback.
Maintain the same structure but incorporate the requested changes.
"""


def get_user_plan_approval(plan: Plan, renderer: PlanRenderer) -> tuple[bool, Optional[str]]:
    """Get user approval for a generated plan.

    Args:
        plan: The plan to review
        renderer: Renderer for formatting the plan

    Returns:
        Tuple of (approved, feedback) where approved indicates if the user
        approved the plan, and feedback contains refinement suggestions
    """
    click.echo("\n" + "=" * 60)
    click.echo("IMPLEMENTATION PLAN REVIEW")
    click.echo("=" * 60)
    click.echo("")

    # Display the formatted plan
    plan_markdown = renderer.render_plan(plan)
    click.echo(plan_markdown)

    click.echo("")
    click.echo("=" * 60)

    while True:
        choice = click.prompt(
            "Plan Review Options:\n"
            "  [a]pprove - Execute this plan as-is\n"
            "  [r]efine - Provide feedback to improve the plan\n"
            "  [c]ancel - Cancel the operation\n\n"
            "Your choice",
            type=click.Choice(["a", "r", "c", "approve", "refine", "cancel"], case_sensitive=False),
            default="approve",
        ).lower()

        if choice in ("a", "approve"):
            return True, None
        elif choice in ("r", "refine"):
            feedback = click.prompt(
                "\nWhat would you like to change about this plan?\n"
                "Be specific about steps, files, or approaches you'd like modified",
                type=str,
            )
            return False, feedback
        elif choice in ("c", "cancel"):
            raise click.ClickException("Operation cancelled by user")
