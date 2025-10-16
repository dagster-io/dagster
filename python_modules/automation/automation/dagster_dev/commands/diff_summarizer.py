"""Smart diff summarization for AI code analysis."""

import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ChangeType(Enum):
    """Categories of code changes for different analysis approaches."""

    DOCUMENTATION = "documentation"
    TESTS = "tests"
    CONFIGURATION = "configuration"
    NEW_FEATURE = "new_feature"
    BUG_FIX = "bug_fix"
    REFACTOR = "refactor"
    MAJOR_REFACTOR = "major_refactor"


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

    change_category: ChangeType
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
    needs_detailed_review: bool  # Whether full diff is recommended


def run_git_command(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run git command and return result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Git command failed: {' '.join(cmd)}\nError: {e}")


def categorize_changes(modified_files: list[str], stats: dict[str, int]) -> ChangeType:
    """Categorize the type of changes based on files and stats."""
    total_changes = stats.get("additions", 0) + stats.get("deletions", 0)

    # Documentation changes
    doc_files = [f for f in modified_files if f.endswith((".md", ".rst", ".txt")) or "docs/" in f]
    if len(doc_files) == len(modified_files):
        return ChangeType.DOCUMENTATION

    # Test changes
    test_files = [f for f in modified_files if "test" in f.lower() or f.endswith("_test.py")]
    if len(test_files) == len(modified_files):
        return ChangeType.TESTS

    # Configuration changes
    config_files = [
        f for f in modified_files if f.endswith((".json", ".yaml", ".yml", ".toml", ".cfg", ".ini"))
    ]
    if len(config_files) == len(modified_files):
        return ChangeType.CONFIGURATION

    # Size-based categorization for code changes
    if total_changes > 500:
        return ChangeType.MAJOR_REFACTOR
    elif total_changes > 100:
        return ChangeType.REFACTOR
    elif any("fix" in f.lower() or "bug" in f.lower() for f in modified_files):
        return ChangeType.BUG_FIX
    else:
        return ChangeType.NEW_FEATURE


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


def get_focused_content_excerpts(diff_content: str, change_category: ChangeType) -> str:
    """Get targeted content based on change category."""
    if change_category == ChangeType.DOCUMENTATION:
        return "Documentation updates - see file changes for details"

    elif change_category == ChangeType.TESTS:
        # Extract test function names and key assertions
        lines = diff_content.split("\n")
        test_lines = [line for line in lines[:50] if "def test_" in line or "assert" in line]
        return "\n".join(test_lines[:10])

    elif change_category in [ChangeType.MAJOR_REFACTOR, ChangeType.REFACTOR]:
        # For refactors, get key structural changes
        lines = diff_content.split("\n")
        key_lines = [
            line
            for line in lines[:100]
            if any(keyword in line for keyword in ["class ", "def ", "import ", "from ", "@"])
        ]
        return "\n".join(key_lines[:20])

    elif change_category == ChangeType.NEW_FEATURE:
        # Focus on public APIs and main logic
        lines = diff_content.split("\n")
        api_lines = [
            line
            for line in lines[:100]
            if line.startswith("+")
            and any(keyword in line for keyword in ["def ", "class ", "public"])
        ]
        return "\n".join(api_lines[:15])

    elif change_category == ChangeType.BUG_FIX:
        # Focus on the actual fix lines
        lines = diff_content.split("\n")
        fix_context = []
        for i, line in enumerate(lines[:200]):
            if line.startswith(("-", "+")) and not line.startswith(("---", "+++")):
                # Get some context around changes
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                fix_context.extend(lines[start:end])
                if len(fix_context) > 30:  # Limit context size
                    break
        return "\n".join(fix_context[:25])

    return "See structural changes for details"


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

    # Categorize the changes
    stats = {"additions": additions, "deletions": deletions}
    change_category = categorize_changes(modified_files, stats)

    # Get structural changes (still lightweight)
    all_functions = []
    all_classes = []
    all_imports = []

    # For small to medium changes, get some structural info
    if change_category != ChangeType.MAJOR_REFACTOR and len(modified_files) <= 10:
        for file_path in modified_files[:5]:  # Limit scope
            try:
                file_diff_result = run_git_command(["git", "diff", diff_range, "--", file_path])
                file_diff = file_diff_result.stdout

                all_functions.extend(extract_function_changes(file_diff, file_path))
                all_classes.extend(extract_class_changes(file_diff, file_path))
                all_imports.extend(extract_import_changes(file_diff, file_path))
            except ValueError:
                # Skip files we can't analyze
                continue

    # Get focused content excerpts only when beneficial
    key_details = ""
    needs_detailed_review = False

    if change_category in [ChangeType.BUG_FIX, ChangeType.NEW_FEATURE] and len(modified_files) <= 3:
        try:
            # Get limited diff content for analysis
            limited_diff_result = run_git_command(["git", "diff", diff_range])
            diff_content = limited_diff_result.stdout[:5000]  # Limit size
            key_details = get_focused_content_excerpts(diff_content, change_category)
        except ValueError:
            key_details = "Could not analyze implementation details"

    elif change_category == ChangeType.MAJOR_REFACTOR:
        needs_detailed_review = True
        key_details = f"Large refactor affecting {files_changed} files - recommend detailed review"

    # Calculate confidence in our analysis
    confidence = 1.0
    if change_category == ChangeType.MAJOR_REFACTOR:
        confidence = 0.6  # Large changes are harder to summarize
    elif (
        not all_functions
        and not all_classes
        and change_category not in [ChangeType.DOCUMENTATION, ChangeType.CONFIGURATION]
    ):
        confidence = 0.7  # We might be missing important details

    # Detect API changes
    api_changes = detect_api_changes(all_functions)

    return SmartDiffSummary(
        change_category=change_category,
        files_changed=files_changed,
        additions=additions,
        deletions=deletions,
        functions=all_functions,
        classes=all_classes,
        imports=all_imports,
        key_implementation_details=key_details,
        api_changes=api_changes,
        summary_confidence=confidence,
        needs_detailed_review=needs_detailed_review,
    )


def format_summary_for_ai(summary: SmartDiffSummary) -> dict[str, Any]:
    """Format summary in structure optimized for AI consumption."""
    return {
        "change_overview": {
            "category": summary.change_category.value,
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
            "needs_detailed_review": summary.needs_detailed_review,
            "analysis_scope": "smart_summary"
            if summary.summary_confidence > 0.8
            else "limited_analysis",
        },
    }
