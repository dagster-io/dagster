## How to add a new event for comsumption by the GraphQL API

We distill the process of adding a new event by examining how we added the new event `StepMaterialization` that is emitted whenever we materialize anything in a solid (currently only called for materializating output notebooks in Dagstermill.)

The `context` object (type `SystemTransformExecutionContext`) that is passed into the transform function of a solid has an attribute `context.events` that is an instantiation of the `ExecutionEvents()` class (in the file `dagster.core.events`). To trigger an event that is consumed by the GraphQL API, we call a method of the `ExecutionEvents` class, such as `context.events.step_materialization_event(**kwargs)`. Thus we must add this event to the `ExecutionEvents` class as below:

`python_modules/dagster/dagster/core/events.py`

```
class ExecutionEvents()
    ...
    def step_materialization_event(self, **kwargs):
        self.context.info(
            msg='Step {step_key} produced materialization of {name} at {loc}'.format(
                step_key=step_key, name=file_name, loc=file_location
            ),
            event_type=EventType.STEP_MATERIALIZATION.value,
            step_key=step_key,
            file_name=file_name,
            file_location=file_location
        )
```

When `ExecutionEvents()` is created, its `self.context` points to the corresponding `RuntimeExecutionContext` that contains it. Thus this function simply logs the event. However notice that the other arguments we're passing into the logger (such as `step_key` or `file_name` are stored as part of meta-information in the Structured Logger log message). Normally if the logger is just writing to the console, then this meta-information is just pretty-printed to the console. However, if there is a `event_callback` in the `SystemTransformExecutionContext`, then we have that the logger message is converted to an `EventRecord` (by the function `construct_event_record(logger_message)`), which is passed into the `event_callback` (which might be provided by Dagit, for example).

Thus we need to make a corresponding EventRecord class that corresponds to our new event.

```
class StepMaterializationRecord(ExecutionStepEventRecord):
    def __init__(self, file_name, file_location, **kwargs):
        ...
    @property
    def name():
        ...
    def to_dict(self):
        ...
```

We need to make sure `construct_event_record` calls the correct `EventRecord` constructor, so we must add our EventRecord to the `EVENT_CLS_LOOKUP` dictionary:

```
EVENT_CLS_LOOKUP = {
    ...
    EventType.STEP_MATERIALIZATION: StepMaterializationRecord,
}
```

We also need to make sure we add the new event to the `EventType` enum, like below

```
class EventType(Enum):
    ...
    STEP_MATERIALIZATION = 'STEP_MATERIALIZATION'
```

We also need to modify the `logger_to_kwargs` function that constructs the kwargs dictionary that gets passed into `StepMaterializationRecord` constructor in `construct_event_record` to add new arguments necesary for the constructor. Notice this should remind us of something we've already done since we're already passed in these parameters as keyword args when we did logging in the function `step_materialization_event` in the `ExecutionEvents()` class, so now we're unpacking these arguments that were stored in the meta information of the logging and re-constructing them in creation of the EventRecord.

```
def logger_to_kwargs(logger_message):
    ...
    if event_cls == StepMaterializationRecord:
        step_args['file_name'] = logger_message.meta['file_name']
        step_args['file_location'] = logger_message.meta['file_location']
    ...
```

This is the end of all the changes necesary in the `events.py` file, but we still need to hook up emission of a Dagster `EventRecord` to a GraphQL schema and GraphQL event.

`python_modules/dagit/dagit/schema/runs.py`

The above file is where the function `from_dagster_event()` converts an `EventRecord` to an `Dauphin` object (which itself is a wrapper on Graphene objects). To add a Dauphin class, we actually create a wrapper class that uses this `Meta` incantation that auto-registers itself with the Dauphin reigstry (in `dagit.dagit.schema.dauphin`) that we later lookup according to the `name` field. Spoooooky 👻! Example below...

```
class DauphinStepMaterializationEvent(dauphin.ObjectType):
    class Meta:
        name = 'StepMaterializationEvent'
        interfaces = (DauphinMessageEvent, DauphinExecutionStepEvent)

    file_name = dauphin.NonNull(dauphin.String)
    file_location = dauphin.NonNull(dauphin.String)
```

The fields `file_name` and `file_location` are fields in the corresponding GraphQL schema for `StepMaterializationEvent`. The interfaces that the event implements define additional fields contained in thos classes. Finally, we need to add code to the `from_dagster_event()` function to actually return an instance of the `DauphinStepMaterializationEvent` class.

```
elif event.event_type == EventType.STEP_MATERIALIZATION:
    return info.schema.type_named('StepMaterializationEvent')(
        step=info.schema.type_named('ExecutionStep')(
            pipeline_run.execution_plan,
            pipeline_run.execution_plan.get_step_by_key(event.step_key)
        ),
        file_name=event.file_name,
        file_location=event.file_location,
        **basic_params
    )
```

The line `info.schema.type_named('StepMaterializationEvent')` auto-magically looks up the `DauphinStepMaterializationEvent` class within the `DauphinRegistry` and calls its constructor with the provided arguments. It is _essential_ to include `**basic_params`, as those arguments generally are used in the interfaces that the Dauphin class implements.

There you go, now you know how to add an event type to the GraphQL schema and thread it through the entire codebase!
