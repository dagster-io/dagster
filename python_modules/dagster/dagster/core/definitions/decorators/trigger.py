from dagster import check
from dagster.core.definitions.trigger import TriggeredExecutionDefinition
from dagster.utils.backcompat import experimental


@experimental
def triggered_execution(
    pipeline_name,
    name=None,
    mode="default",
    solid_selection=None,
    tags_fn=None,
    should_execute_fn=None,
):
    """
    The decorated function will be called as the ``run_config_fn`` of the underlying
    :py:class:`~dagster.TriggeredDefinition` and should take a
    :py:class:`~dagster.TriggeredExecutionContext` as its only argument, returning the environment
    dict for the triggered execution.

    Args:
        pipeline_name (str): The name of the pipeline to execute when the trigger fires.
        name (Optional[str]): The name of this triggered execution.
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute when the trigger fires. e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The pipeline mode to apply for the triggered execution
            (Default: 'default')
        tags_fn (Optional[Callable[[TriggeredExecutionContext], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the triggered execution. Takes a
            :py:class:`~dagster.TriggeredExecutionContext` and returns a dictionary of tags (string
            key-value pairs).
        should_execute_fn (Optional[Callable[[TriggeredExecutionContext], bool]]): A function that
            runs at trigger time to determine whether a pipeline execution should be initiated or
            skipped. Takes a :py:class:`~dagster.TriggeredExecutionContext` and returns a boolean
            (``True`` if a pipeline run should be execute). Defaults to a function that always
            returns ``True``.
    """

    check.str_param(pipeline_name, "pipeline_name")
    check.opt_str_param(name, "name")
    check.str_param(mode, "mode")
    check.opt_nullable_list_param(solid_selection, "solid_selection", of_type=str)
    check.opt_callable_param(tags_fn, "tags_fn")
    check.opt_callable_param(should_execute_fn, "should_execute_fn")

    def inner(fn):
        check.callable_param(fn, "fn")
        trigger_name = name or fn.__name__

        return TriggeredExecutionDefinition(
            name=trigger_name,
            pipeline_name=pipeline_name,
            run_config_fn=fn,
            tags_fn=tags_fn,
            should_execute_fn=should_execute_fn,
            mode=mode,
            solid_selection=solid_selection,
        )

    return inner
