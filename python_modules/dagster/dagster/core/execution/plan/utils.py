def build_resources_for_manager(io_manager_key, step_context):
    required_resource_keys = step_context.mode_def.resource_defs[
        io_manager_key
    ].required_resource_keys
    return step_context.scoped_resources_builder.build(required_resource_keys)
