"""Project analysis and codebase pattern detection for planning context.

This module provides functionality to analyze Dagster projects and extract
patterns, conventions, and structural information that can be used to inform
intelligent code generation and planning decisions.
"""

from typing import Any

from dagster_dg_core.context import DgContext
from dagster_shared.record import record

from dagster_dg_cli.cli.scaffold.branch.claude.diagnostics import ClaudeDiagnostics


@record
class ComponentUsagePattern:
    """Pattern detected in component usage.

    Attributes:
        component_type: The type of component (e.g., 'dagster_dbt.DbtTranslatorComponent')
        usage_count: Number of times this component is used
        common_attributes: Most commonly used attributes and their values
        file_locations: Paths where this component is typically used
    """

    component_type: str
    usage_count: int
    common_attributes: dict[str, Any]
    file_locations: list[str]


@record
class FileOrganizationPattern:
    """Pattern detected in file organization.

    Attributes:
        directory_structure: Common directory patterns and their purposes
        file_naming_conventions: Patterns in file naming
        component_placement: Where different types of components are typically placed
    """

    directory_structure: dict[str, str]
    file_naming_conventions: dict[str, list[str]]
    component_placement: dict[str, list[str]]


@record
class ConfigurationPattern:
    """Pattern detected in YAML configurations.

    Attributes:
        common_attributes: Most frequently used attribute names and patterns
        environment_variable_patterns: Common patterns in env var usage
        typical_values: Common values for different attribute types
    """

    common_attributes: dict[str, int]
    environment_variable_patterns: list[str]
    typical_values: dict[str, list[Any]]


@record
class ProjectAnalysisResult:
    """Complete analysis result of a Dagster project.

    Attributes:
        project_path: Path to the analyzed project
        component_patterns: Detected component usage patterns
        file_patterns: File organization patterns
        config_patterns: Configuration patterns
        available_components: List of available component types
        integration_examples: Examples of external system integrations
        metadata: Additional analysis metadata
    """

    project_path: str
    component_patterns: list[ComponentUsagePattern]
    file_patterns: FileOrganizationPattern
    config_patterns: ConfigurationPattern
    available_components: list[str]
    integration_examples: dict[str, list[str]]
    metadata: dict[str, Any]


class ProjectAnalyzer:
    """Analyzes Dagster projects to extract patterns and conventions.

    This analyzer examines the project structure, component usage, and
    configuration patterns to provide context for intelligent code generation.
    """

    def __init__(self, diagnostics: ClaudeDiagnostics):
        """Initialize the project analyzer.

        Args:
            diagnostics: Diagnostics service for logging analysis operations
        """
        self.diagnostics = diagnostics
        self._analysis_cache: dict[str, ProjectAnalysisResult] = {}

    def analyze_project(
        self, dg_context: DgContext, force_refresh: bool = False
    ) -> ProjectAnalysisResult:
        """Analyze a Dagster project to extract patterns and conventions.

        Args:
            dg_context: Dagster project context
            force_refresh: Whether to bypass cache and perform fresh analysis

        Returns:
            Complete analysis result with detected patterns
        """
        project_path = str(dg_context.root_path)

        # Check cache first unless forced refresh
        if not force_refresh and project_path in self._analysis_cache:
            self.diagnostics.debug(
                "project_analysis_cache_hit",
                "Using cached project analysis result",
                {"project_path": project_path},
            )
            return self._analysis_cache[project_path]

        self.diagnostics.info(
            "project_analysis_start",
            "Starting comprehensive project analysis",
            {"project_path": project_path, "force_refresh": force_refresh},
        )

        # Analyze different aspects of the project
        component_patterns = self._analyze_component_usage(dg_context)
        file_patterns = self._analyze_file_organization(dg_context)
        config_patterns = self._analyze_configuration_patterns(dg_context)
        available_components = self._get_available_components(dg_context)
        integration_examples = self._find_integration_examples(dg_context)

        result = ProjectAnalysisResult(
            project_path=project_path,
            component_patterns=component_patterns,
            file_patterns=file_patterns,
            config_patterns=config_patterns,
            available_components=available_components,
            integration_examples=integration_examples,
            metadata={
                "analysis_timestamp": "2025-01-01T00:00:00Z",  # TODO: Use proper timestamp
                "analysis_version": "1.0",
                "total_patterns_detected": len(component_patterns),
            },
        )

        # Cache the result
        self._analysis_cache[project_path] = result

        self.diagnostics.info(
            "project_analysis_completed",
            "Project analysis completed successfully",
            {
                "component_patterns_count": len(component_patterns),
                "available_components_count": len(available_components),
                "integration_examples_count": len(integration_examples),
            },
        )

        return result

    def _analyze_component_usage(self, dg_context: DgContext) -> list[ComponentUsagePattern]:
        """Analyze how components are used in the project.

        Args:
            dg_context: Dagster project context

        Returns:
            List of detected component usage patterns
        """
        self.diagnostics.debug(
            "component_usage_analysis_start",
            "Analyzing component usage patterns",
            {"project_path": str(dg_context.root_path)},
        )

        patterns = []
        component_usage = {}

        # Find all defs.yaml files in the project
        defs_files = list(dg_context.root_path.rglob("*defs.yaml"))
        defs_files.extend(list(dg_context.root_path.rglob("*defs.yml")))

        for defs_file in defs_files:
            try:
                content = defs_file.read_text()
                # Basic parsing - in a full implementation, would use proper YAML parsing
                if "type:" in content:
                    # Extract component types mentioned in the file
                    lines = content.split("\n")
                    for line in lines:
                        if line.strip().startswith("type:"):
                            component_type = line.split(":", 1)[1].strip()
                            if component_type not in component_usage:
                                component_usage[component_type] = {
                                    "count": 0,
                                    "files": [],
                                    "attributes": {},
                                }
                            component_usage[component_type]["count"] += 1
                            component_usage[component_type]["files"].append(str(defs_file))
            except Exception as e:
                self.diagnostics.debug(
                    "component_usage_file_error",
                    f"Error analyzing defs file: {defs_file}",
                    {"error": str(e)},
                )

        # Convert to ComponentUsagePattern objects
        for component_type, usage_info in component_usage.items():
            pattern = ComponentUsagePattern(
                component_type=component_type,
                usage_count=usage_info["count"],
                common_attributes=usage_info.get("attributes", {}),
                file_locations=usage_info["files"],
            )
            patterns.append(pattern)

        return patterns

    def _analyze_file_organization(self, dg_context: DgContext) -> FileOrganizationPattern:
        """Analyze file organization patterns in the project.

        Args:
            dg_context: Dagster project context

        Returns:
            Detected file organization patterns
        """
        self.diagnostics.debug(
            "file_organization_analysis_start",
            "Analyzing file organization patterns",
            {"project_path": str(dg_context.root_path)},
        )

        directory_structure = {}
        file_naming_conventions = {
            "defs_files": [],
            "python_files": [],
            "yaml_files": [],
        }
        component_placement = {}

        # Analyze directory structure
        for path in dg_context.root_path.rglob("*"):
            if path.is_dir():
                relative_path = path.relative_to(dg_context.root_path)
                # Categorize directories by common patterns
                if "assets" in path.name.lower():
                    directory_structure[str(relative_path)] = "assets_directory"
                elif "jobs" in path.name.lower():
                    directory_structure[str(relative_path)] = "jobs_directory"
                elif "resources" in path.name.lower():
                    directory_structure[str(relative_path)] = "resources_directory"

        # Analyze file naming patterns
        for defs_file in dg_context.root_path.rglob("*defs.yaml"):
            relative_path = defs_file.relative_to(dg_context.root_path)
            file_naming_conventions["defs_files"].append(str(relative_path))

        return FileOrganizationPattern(
            directory_structure=directory_structure,
            file_naming_conventions=file_naming_conventions,
            component_placement=component_placement,
        )

    def _analyze_configuration_patterns(self, dg_context: DgContext) -> ConfigurationPattern:
        """Analyze configuration patterns in YAML files.

        Args:
            dg_context: Dagster project context

        Returns:
            Detected configuration patterns
        """
        self.diagnostics.debug(
            "configuration_patterns_analysis_start",
            "Analyzing configuration patterns",
            {"project_path": str(dg_context.root_path)},
        )

        common_attributes = {}
        environment_variable_patterns = []
        typical_values = {}

        # Analyze YAML configuration files
        yaml_files = list(dg_context.root_path.rglob("*.yaml"))
        yaml_files.extend(list(dg_context.root_path.rglob("*.yml")))

        for yaml_file in yaml_files:
            try:
                content = yaml_file.read_text()
                # Basic pattern detection - look for common attribute names
                lines = content.split("\n")
                for line_raw in lines:
                    line = line_raw.strip()
                    if ":" in line and not line.startswith("#"):
                        attr_name = line.split(":", 1)[0].strip()
                        if attr_name:
                            common_attributes[attr_name] = common_attributes.get(attr_name, 0) + 1

                    # Look for environment variable patterns
                    if "${" in line or "$(" in line:
                        environment_variable_patterns.append(line.strip())

            except Exception as e:
                self.diagnostics.debug(
                    "configuration_pattern_file_error",
                    f"Error analyzing YAML file: {yaml_file}",
                    {"error": str(e)},
                )

        return ConfigurationPattern(
            common_attributes=common_attributes,
            environment_variable_patterns=list(set(environment_variable_patterns)),
            typical_values=typical_values,
        )

    def _get_available_components(self, dg_context: DgContext) -> list[str]:
        """Get list of available component types in the project.

        Args:
            dg_context: Dagster project context

        Returns:
            List of available component type names
        """
        # This would typically use the dg CLI to get available components
        # For now, return a basic set of common components
        return [
            "dagster.AssetsDefinition",
            "dagster.JobDefinition",
            "dagster.ScheduleDefinition",
            "dagster.SensorDefinition",
            "dagster.ResourceDefinition",
            "dagster_dbt.DbtCliResource",
            "dagster_dbt.DbtTranslatorComponent",
        ]

    def _find_integration_examples(self, dg_context: DgContext) -> dict[str, list[str]]:
        """Find examples of external system integrations.

        Args:
            dg_context: Dagster project context

        Returns:
            Dictionary mapping integration types to example file paths
        """
        integrations = {}

        # Look for common integration patterns in files
        python_files = list(dg_context.root_path.rglob("*.py"))

        for py_file in python_files:
            try:
                content = py_file.read_text()
                relative_path = str(py_file.relative_to(dg_context.root_path))

                # Check for common integrations
                if "dagster_dbt" in content:
                    integrations.setdefault("dbt", []).append(relative_path)
                if "dagster_snowflake" in content:
                    integrations.setdefault("snowflake", []).append(relative_path)
                if "dagster_pandas" in content:
                    integrations.setdefault("pandas", []).append(relative_path)
                if "requests" in content or "http" in content:
                    integrations.setdefault("http_apis", []).append(relative_path)

            except Exception as e:
                self.diagnostics.debug(
                    "integration_example_file_error",
                    f"Error analyzing Python file for integrations: {py_file}",
                    {"error": str(e)},
                )

        return integrations

    def get_planning_context_summary(self, analysis: ProjectAnalysisResult) -> dict[str, Any]:
        """Generate a summary suitable for planning context.

        Args:
            analysis: Project analysis result

        Returns:
            Dictionary containing summarized analysis for planning prompts
        """
        return {
            "most_used_components": [
                pattern.component_type
                for pattern in sorted(
                    analysis.component_patterns, key=lambda x: x.usage_count, reverse=True
                )[:5]
            ],
            "directory_patterns": list(analysis.file_patterns.directory_structure.keys())[:10],
            "common_config_attributes": list(
                sorted(
                    analysis.config_patterns.common_attributes.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:10]
            ),
            "available_integrations": list(analysis.integration_examples.keys()),
            "total_components_analyzed": len(analysis.component_patterns),
        }
