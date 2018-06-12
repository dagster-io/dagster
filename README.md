# Dagster

The core abstraction in Dagster is a **Solid**, a logical unit of computation in a data pipeline.

At its core a Solid is a coarse-grained pure function. It takes multiple inputs, performs a computation, produces an output. Inputs can either be received from outputs from upstream solids in the pipeline or external sources (e.g. files). Likewise, outputs from the transform can either be flowed to downstream solids or materialized (e.g. to a file in an object store) so that it can be inspected or accessed by an external system.

Solid formally separates the notion of inputs, outputs, the core transform. The core goal of this is cleanly and clearly separate the domain logic of each transform and its operational environments. This allows solids or pipelines of solids to easily be executable in a number of environments: unit-testing, local development, integration tests, CI/CD, staging environments, production environments, and so on and so forth. 

A solid has the following concepts:

* Transform 
* Inputs
    * Dependencies
    * Sources
        * Arguments for each source (e.g. a file path)
* Output
    * Materializations
        * Arguments for each materialization (e.g. a file path)

We will go through these in detail, driven by an example:

Note: This API is purely pedagogical. Actual APIs used in real pipelines
would be composed of higher level abstractions. This is purely used to illustrate the core concepts.

```python=
def hello_world_transform_fn(num_df):
    num_df['sum'] = num_df['num1'] + num_df['num2']
    return num_df
    
csv_input = InputDefinition(
    name='num_df',
    sources=[
        SourceDefinition(
            source_type='CSV',
            argument_def_dict={'path': types.PATH},
            source_fn=lambda arg_dict: pd.read_csv(arg_dict['path']),
        ),
    ],
)

csv_materialization = MaterializationDefinition(
    materialization_type='CSV',
    materialization_fn=
        lambda df, arg_dict: df.to_csv(arg_dict['path'], index=False),
    argument_def_dict={'path': types.PATH}
)

hello_world = Solid(
    name='hello_world',
    inputs=[csv_input],
    transform_fn=hello_world_transform_fn,
    output=OutputDefinition(materializations=[csv_materialization])
)
```

### Transform

This is core, user-defined transform that performs the logical data computation. In this case the transform is ```hello_world_transform_fn``` and it is passed as parameter into the solid. It takes one or more inputs and produces an output. All other concepts in a solid are the metadata and structure that surround this core computation

### Inputs

For each argument to the transform function, there is one ```InputDefinition``` object. It has a name, which must match the parameters to the transform function. The input definitions define a name, a dependency for the input (what upstream solid produces its value, see below) and a number of sources. An input definition must specify at least a dependency or a source. The input can have any number of sources.

#### Sources

Sources are the the way that one can create an input to a transform from external resources. A source is a function that takes a set of arguments and produces a value that is passed to the transform for processing. In this case, a CSV file is the only source type. One can imagine adding other source types to create pandas dataframes for Json, Parquet, and so forth. End users will typically rely on pre-existing libraries to specify sources.

Sources also declare what arguments they expect. These are inspectable and could be used to render information for web or command line tools, to verify the validity of confie files, and other tooling contexts. The framework verifies when solids or pipelines of solids are executed, that the arguments abide by the declaration. These arguments are then sent to the source function in the ```arg_dict``` parameter.

### Output

The ```OutputDefinition``` represents the output of the transform function. 

#### Materializations

Materializations are the other end of source. This specifies the way the output of a transform can be materialized. In this example which uses pandas dataframes, the sources and materializations will be symmetrical. In the above example we specified a single materialization, a CSV. One could expand this to include JSON, Parquet, or other materialiations as appropriate. 

However in other contexts that might be true. Take solids that operate on SQL-based data warehouses or similar. The core transform would be the SQL command, but the materialization would specify a ```CREATE TABLE AS```, a table append, or a partition creation, as examples. 
   
   
### Higher-level APIs

These definitions will typically be composed with higher level APIs. For example, the above solid could be expressed using APIs provided by the pandas kernel. (Note: the "kernel" terminology is not settled) 

```python
import dagster
import dagster.pandas_kernel as dagster_pd

def sum_transform(num_df):
    num_df['sum'] = num_df['num1'] + num_df['num2']
    return num_df

sum_solid = Solid(
    name='sum',
    description='This computes the sum of two numbers.'
    inputs=[dagster_pd.dataframe_csv_input(name='num_df')],
    transform_fn=sum_transform,
    output=dagster_pd.dataframe_output(),
)
```

### Execution

These are useless without being able to execute them. In order to execute a solid, you need to package it up into a pipeline.

```python
pipeline = dagster.pipeline(name='hello_world', solids=[sum_solid])
```

Then you an execute it by providing an environment. You must provide enough source data to create all the inputs necessary for the pipeline. 

```python
environment = dagster.config.environment(
    inputs=[
        dagster.config.input(
            name='num_df',
            source='CSV', 
            args={'path': 'path/to/input.csv'}
        )
    ]    
)

pipeline_result = dagster.execute_pipeline(
    dagster.context(),
    pipeline,
    environment
)

print(pipeline_result.result_named('sum').transformed_value)
```

Execute pipeline does a purely in-memory transform, materializing nothing. This is useful in testing and CI/CD contexts. 

### Materialization

In order to produce outputs that are available to external systems, you must materialize them. In this case, that means producing files. In addition to your environment, you must specify your materializations.

```python
materializations = [
    config.materialization(
        solid='sum', 
        materialization_type='CSV', 
        args={'path': 'path/to/output.csv'},
    )    
]

dagster.materialize_pipeline(
    dagster.context(),
    pipeline,
    environment,
    materializations,
)
```

### Dependencies

So far we have demonstrated a single stage pipeline, which is obviously of limited value.

Imagine we wanted to add another stage which took the sum we produced and squared that value. (Fancy!)

```python
def sum_sq_transform(sum_df):
    sum_df['sum_sq'] = sum_df['sum'] * sum_df['sum']
    return sum_df
    
# Fully expanded InputDefintion. Should be wrapped in higher-level
# but this is here for explanatory code.
sum_sq_input = InputDefinition(
    name='sum_df',
    sources=[
        SourceDefinition(
            source_type='CSV',
            argument_def_dict={'path': types.PATH},
            source_fn=lambda arg_dict: pd.read_csv(arg_dict['path']),
        ),
    ],
    depends_on=sum_solid,
)

sum_sq_solid = Solid(
    name='sum_sq',
    inputs=[sum_sq_input],
    transform_fn=sum_sq_transform,
    output=dagster_pd.dataframe_output(),
)
```

Note that input specifies that dependency. This means that the input value
passed to the transform can be generated by an upstream dependency OR by an external source. This allows for the solid to be executable in isolation or in the context of a pipeline.

```python
pipeline = dagster.pipeline(solids=[sum_solid, sum_sq_solid])

environment = dagster.config.environment(
    inputs=[
        dagster.config.input(
            name='num_df',
            source='CSV', 
            args={'path': 'path/to/num.csv'}
        )
    ]    
)

pipeline_result = dagster.execute_pipeline(
    dagster.context(),
    pipeline,
    environment
)
```

The above executed both solids, even though one input was provided. The input into sum_sq_solid was provided by the upstream result from the output of sum_solid. 

You can also execute subsets of the pipeline. Given the above pipeline, you could specify that you only want to specify the first solid:

```python
environment = dagster.config.environment(
    inputs=[
        dagster.config.input(
            name='num_df',
            source='CSV', 
            args={'path': 'path/to/num.csv'}
        )
    ]    
)

pipeline_result = dagster.execute_pipeline(
    dagster.context(),
    pipeline,
    environment,
    through=['sum'],
)
```

Or you could specify just the second solid. In that case the environment would have to be changed.

```python
environment = dagster.config.environment(
    inputs=[
        dagster.config.input(
            name='sum_df',
            source='CSV', 
            args={'path': 'path/to/sum.csv'}
        )
    ]    
)

pipeline_result = dagster.execute_pipeline(
    dagster.context(),
    pipeline,
    environment,
    from=['sum'],
    through=['sum_sq'],
)
```

TODO: Documentation yaml file config format for environment and materializations


### Expectations

Expectations are another reason to introduce logical seams between data computations. They are a way to perform data quality tests or statistical process control on data pipelines.

TODO: Complete this section when the APIs and functionality are more fleshed out.

