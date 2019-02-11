# New Concepts in 0.3.0

The upgrade guide describes the changes you are _require_ to make to install 0.3.0. This guide describes the changes you _should_ make in order to use the latest capabilities. The new concepts take some getting used to, but are quite powerful.

## Resources

In 0.2.0 the notion of resources were relatively informal. This is no longer true: They are now an officially supported abstraction. They break apart context creation into composable, reusable chunks of software.

**Defining a Resource**

Let's take a typical unittest context.

Before:

```py
def define_unittest_context():
    return PipelineContextDefinition(
        config_field=Field(
            Dict(
                {
                    'data_source_run_id' : _data_source_run_id_field(),
                    'conf' : _conf_field(),
                    'log_level' : _log_level_field(),
                    'cleanup_files' : _cleanup_field(),
                },
            )
        ),
        context_fn=create_fileload_unittest_context,
        description='''
Context for use in unit tests. It does not allow for any interaction with aws
or s3, and can only be used for a subset of the pipeline that can execute on a
local machine.

This context does not log to file and also has a configurable log_level.
        '''
    )

def create_fileload_unittest_context(info):
    data_source_run_id = info.config['data_source_run_id']
    log_level = level_from_string(info.config['log_level'])
    pipeline_run_id = str(uuid.uuid4())

    resources = FileloadResources(
        aws=None,
        redshift=None,
        bucket_path=None,
        local_fs=LocalFsHandleResource.for_pipeline_run(pipeline_run_id),
        sa=None,
        pipeline_guid=data_source_run_id)

    yield ExecutionContext(
        loggers=[define_colored_console_logger('dagster', log_level)],
        resources=resources,
        tags={
            'data_source_run_id': data_source_run_id,
            'data_source': 'new_data',
            'pipeline_run_id': pipeline_run_id,
        },
    )
```

That's quite the ball of wax for what should be relatively straightforward. And this doesn't even include the boilerplate `FileloadResources` class as well. We're going to break this apart using the `ResourceDefinition` abstraction and eliminate the need for that class.

The only real reusable resource here is the LocalFsHandleResource, so let's break that out into it's own `ResourceDefinition`.

```py
def define_local_fs_resource():
    def _create_resource(init_context):
        resource = LocalFsHandleResource.for_pipeline_run(init_context.run_id)
        yield resource
        if init_context.resource_config['cleanup_files']:
            LocalFsHandleResource.clean_up_dir(init_context.run_id)

    return ResourceDefinition(
        resource_fn=_create_resource,
        config_field=Field(
            Dict({'cleanup_files': Field(Bool, is_optional=True, default_value=True)})
        ),
    )
```

This is now a self-contained piece that can be reused in other contexts as well.

Aside: We now guarantee a system-generated run_id, so the manually created pipeline_guid resource is no longer relevant.

The rest of the "resources" in the unittesting context are None, and we have a special helper to create "none" resources.

Let's put it all together:

```py
def define_unittest_context():
    return PipelineContextDefinition(
        config_field=Field(Dict({
            'log_level' : _log_level_field(),
            'data_source_run_id': _data_source_run_id_field(),
        })),
        resources={
            'local_fs': define_local_fs_resource(),
            'aws': ResourceDefinition.none_resource(),
            'redshift': ResourceDefinition.none_resource(),
            'bucket_path': ResourceDefinition.none_resource(),
            'sa': ResourceDefinition.none_resource(),
        },
        context_fn=create_fileload_unittest_context,
        description='''
Context for use in unit tests. It does not allow for any interaction with aws
or s3, and can only be used for a subset of the pipeline that can execute on a
local machine.

This context does not log to file and also has a configurable log_level.
        '''
    )

def create_fileload_unittest_context(init_context):
    data_source_run_id = init_context.context_config['data_source_run_id']
    log_level = level_from_string(init_context.context_config['log_level'])

    yield ExecutionContext(
        loggers=[define_colored_console_logger('dagster', log_level)],
        tags={
            'data_source_run_id': data_source_run_id,
            'data_source': 'new_data',
        },
    )
```

Notice a few things. The bulk of the context creation function is now gone. Instead of having to manually create the `FileloadResources`, that is replaced by a class (a `namedtuple`) that is system-synthesized. Predictably it has N fields, one for each resource. The pipeline-code-facing API is the same, it just requires less boilerplate within the pipeline infrastructure.

**Configuring a Resource**

The configuration schema changes, as each resource has it's own section.

Before:

```py
environment = {
    'context':{
        'unittest' : {
            'config' : {
                'data_source_run_id': str(uuid.uuid4()),
                'conf': CONF,
                'log_level': 'ERROR',
                'cleanup_files': False,
            }
        }
    },
    'solids': {
        'unzip_file': {
            'config' : {
                'zipped_file': ZIP_FILE_PATH,
            }
        }
    }
}
```

In particular we need to move `cleanup_files` to a resource section of the config.

```py
environment = {
    'context':{
        'unittest' : {
            'config' : {
                'data_source_run_id': str(uuid.uuid4()),
                'log_level': 'ERROR',
            },
            'resources' : {
                'local_fs': {
                    'config' : {
                        'cleanup_files': False,
                    }
                }
            }
        }
    },
    'solids': {
        'unzip_file': {
            'config' : {
                'zipped_file': ZIP_FILE_PATH,
            }
        }
    }
}
```

While slightly more verbose, you will be able to count on more consistent of configuration between pipelines as you reuse resources, and you an even potentially share resource configuration _between_ pipelines using the configuration file merging feature of 0.3.0

## Resource Libraries

The real promise of resources to build a library of resuable, composable resources.

For example, here would be a resource to create a redshift connection.

```py
def define_redshift_sa_resource():
    def _create_resource(init_context):
        user = init_context.resource_config['user']
        password = init_context.resource_config['password']
        host = init_context.resource_config['host']
        port = init_context.resource_config['port']
        dbname = init_context.resource_config['dbname']
        return sa.create_engine(f'postgresql://{user}:{password}@{host}:{port}/{dbname}')

    return ResourceDefinition(
        resource_fn=_create_resource,
        config_field=Field(
            Dict(
                {
                    'user' : Field(String),
                    'password' : Field(String),
                    'host' : Field(String),
                    'port' : Field(Int),
                    'dbname' : Field(String),
                }
            )
        )
    )
```

This could be used -- unmodified -- across all your pipelines. This will also make it easier to write reusable solids as they can know that they will be using the same resource. Indeed, we may formalize this in subsequent releases, allowing solids to formally declare their dependencies on specific resource types.

## Solid-Level Configs to Inputs

With the new ability to source inputs from the environment config files, we anticipate that solid-level configuration will become much less common, and instead that we will uses inputs and outputs exclusively.

Let's use another example from the a typical fileload pipeline.

Before:

```py
@solid(
    name='unzip_file',
    inputs=[],
    outputs=[OutputDefinition(dagster_type=DagsterTypes.PathToFile)],
    description='''
This takes a single, pre-existing zip folder with a single file and unzips it,
and then outputs the path to that file.
''',
    config_def=ConfigDefinition(
        types.ConfigDictionary('UnzipFileConfig', {'zipped_file' : Field(types.Path)}),
    ),
)
def unzip_file(info):
    context = info.context
    zipped_file = info.config['zipped_file']
```

You'll note that in 0.2.8 we have to model the incoming zipped file as config rather than an input because `unzip_file` had no upstream dependencies and inputs
had to come from previous solids. In 0.3.0 this is no longer true. Inputs
can be sourced from the config file now, which means that by default you should
be modeling such things as inputs.

After:

```py
@solid(
    name='unzip_file',
    inputs=[InputDefinition('zipped_file', Path)],
    outputs=[OutputDefinition(Path)],
    description='''
This takes a single, pre-existing zip folder with a single file and unzips it,
and then outputs the path to that file.
''',
)
def unzip_file(context, zipped_file):
    # ...
    pass
```

In order to invoke a pipeline that contains this solid, you need to satisy this input in the environment config.

Before:

```py
    environment = {
        # .. context section omitted
        'solids': {
            'unzip_file': {
                'config' : {
                    'zipped_file': ZIP_FILE_PATH,
                }
            }
        }
    }
```

After:

```py
    environment = {
        # .. context section omitted
        'solids': {
            'unzip_file': {
                'inputs' : {
                    'zipped_file': ZIP_FILE_PATH,
                }
            }
        }
    }
```

What's great about this new input structure is that now the unzip_file is more reusable as it could be reused in the middle of a pipeline with its input coming from a previous solid, or as a solid at the beginning of a pipeline.
