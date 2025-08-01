"""Docstring fixtures for testing instance method validation."""

from dagster._annotations import public


@public
class InstanceMethodFixtures:
    """Fixtures for testing instance method docstring validation."""

    @public
    def valid_instance_method(self, data, options=None):
        """Process the provided data with optional configuration.

        Args:
            data: The data to process
            options: Optional processing configuration

        Returns:
            Processed data result
        """
        pass

    @public
    def instance_method_documenting_self(self, data):
        """Process data (incorrect style documenting self).

        Args:
            self: The instance (should not be documented)
            data: Data to process

        Returns:
            Processed data result
        """
        pass

    @public
    def complex_instance_method(self, pipeline_config, execution_mode, retry_policy=None):
        """Execute multi-stage data processing pipeline.

        This method performs comprehensive data processing through multiple
        stages with configurable options and error handling.

        Args:
            pipeline_config: Configuration dictionary containing:
                - stage_1: Initial data ingestion settings
                - stage_2: Data transformation parameters
                - stage_3: Export configuration options
            execution_mode: Mode selection ('sequential', 'parallel', 'adaptive')
            retry_policy: Error retry configuration

        Returns:
            PipelineResult containing:
                - execution_summary: High-level statistics
                - stage_results: Detailed per-stage results
                - performance_metrics: Timing and resource data

        Raises:
            PipelineConfigError: If configuration is invalid
            DataProcessingError: If processing fails at any stage
            ResourceError: If insufficient system resources

        Examples:
            Basic usage:

            >>> config = {'stage_1': {...}, 'stage_2': {...}}
            >>> result = processor.execute_pipeline(config, 'sequential')
            >>> print(result.execution_summary)

        Note:
            This method requires substantial computational resources for large
            datasets. Consider using batch processing for datasets larger
            than 100,000 records.
        """
        pass
