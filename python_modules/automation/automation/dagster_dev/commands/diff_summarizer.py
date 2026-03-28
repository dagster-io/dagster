"""Smart diff summarization for AI code analysis."""

import re
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class StructuralChange:
    """Represents a structural change without full content."""

    change_type: str  # "added", "modified", "deleted"
    name: str  # Function/class name
    file_path: str  # Where the change occurred
    details: str  # Brief description


@dataclass
class SmartDiffSummary:
    """Comprehensive but lightweight diff analysis."""

    files_changed: int
    additions: int
    deletions: int

    # Structural information
    functions: list[StructuralChange]
    classes: list[StructuralChange]
    imports: list[StructuralChange]

    # Focused content excerpts (when needed)
    key_implementation_details: str
    api_changes: list[str]

    # Context for AI
    summary_confidence: float  # How confident we are in this analysis


def run_git_command(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run git command and return result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Git command failed: {' '.join(cmd)}\nError: {e}")


def extract_function_changes(diff_content: str, file_path: str) -> list[StructuralChange]:
    """Extract function-level changes without full implementation."""
    functions = []

    # Pattern for Python function definitions
    function_pattern = r"^[+-](\s*)def\s+(\w+)\s*\([^)]*\):"

    for line in diff_content.split("\n"):
        match = re.match(function_pattern, line)
        if match:
            change_type = (
                "added"
                if line.startswith("+")
                else "deleted"
                if line.startswith("-")
                else "modified"
            )
            func_name = match.group(2)

            functions.append(
                StructuralChange(
                    change_type=change_type,
                    name=func_name,
                    file_path=file_path,
                    details=f"{change_type} function: {func_name}()",
                )
            )

    return functions


def extract_class_changes(diff_content: str, file_path: str) -> list[StructuralChange]:
    """Extract class-level changes."""
    classes = []

    # Pattern for Python class definitions
    class_pattern = r"^[+-](\s*)class\s+(\w+).*:"

    for line in diff_content.split("\n"):
        match = re.match(class_pattern, line)
        if match:
            change_type = (
                "added"
                if line.startswith("+")
                else "deleted"
                if line.startswith("-")
                else "modified"
            )
            class_name = match.group(2)

            classes.append(
                StructuralChange(
                    change_type=change_type,
                    name=class_name,
                    file_path=file_path,
                    details=f"{change_type} class: {class_name}",
                )
            )

    return classes


def extract_import_changes(diff_content: str, file_path: str) -> list[StructuralChange]:
    """Extract import/dependency changes."""
    imports = []

    # Pattern for import statements
    import_patterns = [
        r"^[+-](\s*)(import\s+\w+.*)",
        r"^[+-](\s*)(from\s+\w+.*import.*)",
    ]

    for line in diff_content.split("\n"):
        for pattern in import_patterns:
            match = re.match(pattern, line)
            if match:
                change_type = "added" if line.startswith("+") else "deleted"
                import_stmt = match.group(2).strip()

                imports.append(
                    StructuralChange(
                        change_type=change_type,
                        name=import_stmt,
                        file_path=file_path,
                        details=f"{change_type} import: {import_stmt}",
                    )
                )
                break

    return imports


def get_focused_content_excerpts(diff_content: str) -> str:
    """Get targeted content excerpts from diff content."""
    # Extract key structural elements from diff
    lines = diff_content.split("\n")
    key_lines = [
        line
        for line in lines[:100]
        if line.startswith(("+", "-"))
        and not line.startswith(("+++", "---"))
        and any(keyword in line for keyword in ["class ", "def ", "import ", "from ", "@"])
    ]
    return "\n".join(key_lines[:20])


def detect_api_changes(functions: list[StructuralChange]) -> list[str]:
    """Detect public API changes that might need special attention."""
    api_changes = []

    for func in functions:
        # Heuristic for public API - functions that don't start with _
        if not func.name.startswith("_") and func.change_type in ["added", "deleted"]:
            api_changes.append(f"{func.change_type.title()} public function: {func.name}")

    return api_changes


def get_smart_diff_summary(diff_range: str) -> SmartDiffSummary:
    """Generate intelligent diff summary optimized for AI consumption."""
    # Get basic file statistics (lightweight)
    name_status_result = run_git_command(["git", "diff", "--name-status", diff_range])
    stat_result = run_git_command(["git", "diff", "--stat", diff_range])

    # Parse modified files
    modified_files = []
    for line in name_status_result.stdout.strip().split("\n"):
        if line and "\t" in line:
            status, filepath = line.split("\t", 1)
            if status in ["M", "A"]:  # Modified or Added
                modified_files.append(filepath)

    # Parse statistics
    stat_lines = stat_result.stdout.strip().split("\n")
    files_changed = 0
    additions = 0
    deletions = 0

    for line in stat_lines:
        if " file" in line and " changed" in line:
            parts = line.split(",")
            files_part = parts[0].strip()
            if files_part:
                files_changed = int(files_part.split()[0])

            for part in parts[1:]:
                stripped_part = part.strip()
                if "insertion" in stripped_part:
                    additions = int(stripped_part.split()[0])
                elif "deletion" in stripped_part:
                    deletions = int(stripped_part.split()[0])

    # Get structural changes for all files (reasonable limit)
    all_functions = []
    all_classes = []
    all_imports = []

    # Analyze up to 10 files for structural info
    for file_path in modified_files[:10]:
        try:
            file_diff_result = run_git_command(["git", "diff", diff_range, "--", file_path])
            file_diff = file_diff_result.stdout

            all_functions.extend(extract_function_changes(file_diff, file_path))
            all_classes.extend(extract_class_changes(file_diff, file_path))
            all_imports.extend(extract_import_changes(file_diff, file_path))
        except ValueError:
            # Skip files we can't analyze
            continue

    # Get focused content excerpts from limited diff content
    key_details = ""
    try:
        limited_diff_result = run_git_command(["git", "diff", diff_range])
        diff_content = limited_diff_result.stdout[:5000]  # Limit size
        key_details = get_focused_content_excerpts(diff_content)
    except ValueError:
        key_details = "Could not analyze implementation details"

    # Calculate confidence based on available information
    confidence = 0.9  # High confidence by default
    if not all_functions and not all_classes and not all_imports:
        confidence = 0.7  # Lower if no structural info found

    # Detect API changes
    api_changes = detect_api_changes(all_functions)

    return SmartDiffSummary(
        files_changed=files_changed,
        additions=additions,
        deletions=deletions,
        functions=all_functions,
        classes=all_classes,
        imports=all_imports,
        key_implementation_details=key_details,
        api_changes=api_changes,
        summary_confidence=confidence,
    )


def format_summary_for_ai(summary: SmartDiffSummary) -> dict[str, Any]:
    """Format summary in structure optimized for AI consumption."""
    return {
        "change_overview": {
            "scope": f"{summary.files_changed} files, +{summary.additions}/-{summary.deletions} lines",
            "confidence": summary.summary_confidence,
        },
        "structural_changes": {
            "functions": [
                f"{change.change_type} {change.name}() in {change.file_path}"
                for change in summary.functions
            ],
            "classes": [
                f"{change.change_type} {change.name} in {change.file_path}"
                for change in summary.classes
            ],
            "imports": [f"{change.change_type}: {change.name}" for change in summary.imports],
        },
        "implementation_highlights": summary.key_implementation_details,
        "api_impact": summary.api_changes,
        "analysis_notes": {
            "analysis_scope": "smart_summary"
            if summary.summary_confidence > 0.8
            else "limited_analysis",
        },
    }
