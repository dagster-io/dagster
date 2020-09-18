def compute_version_for_step_output(step_context, _output):
    """
    Args:
        step_context (SystemStepExecutionContext):
        output (Output):
    """
    # Get version of solid.
    solid_def = step_context.solid_def
    # This is an incorrect placeholder implmenetation - we actually need to include the versions of all the
    # solid's inputs.
    return solid_def.version
