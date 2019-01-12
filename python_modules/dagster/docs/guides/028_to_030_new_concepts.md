The upgrade guide describes the changes you are *require* to make to install 0.3.0. This guide describes the changes you *should* make in order to use the latest capabilities. The new concepts take some getting used to, but are quite powerful.

Resources
---------

In 0.2.0 the notion of resources were relatively informal. This is no longer true. They are now an officially supported abstraction. They break apart context creation in a composable, reusable chunks of software.

**Defining a Resource**


Let's take the unittest context in the allscripts_fileload pipeline as an example.

```
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
        context_fn=create_allscripts_fileload_unittest_context,
        description='''
Context for use in unit tests. It does not allow for any interaction with aws
or s3, and can only be used for a subset of the pipeline that can execute on a
local machine.

This context does not log to file and also has a configurable log_level.
        '''
    )

def create_allscripts_fileload_unittest_context(info):
    data_source_run_id = info.config['data_source_run_id']
    log_level = level_from_string(info.config['log_level'])
    pipeline_run_id = str(uuid.uuid4())

    resources = AllscriptsFileloadResources(
        aws=None,
        redshift=None,
        bucket_path=None,
        local_fs=LocalFsHandleResource.for_pipeline_run(pipeline_run_id),
        sa=None,
        cooper_pair=None,
        pipeline_guid=data_source_run_id)

    yield ExecutionContext(
        loggers=[define_colored_console_logger('dagster', log_level)],
        resources=resources,
        context_stack={
            'data_source_run_id': data_source_run_id,
            'data_source': 'allscripts',
            'pipeline_run_id': pipeline_run_id,
        },
    )
```

That's quite the ball of wax for what should be relatively straightforward. And this hides the boilerplate AllScriptsFileloadResources class as well. We're going to break this apart and eliminate the need for that class.

The only real reusable resource here is the LocalFsHandleResource, so let's break that out into it's own Resource.

```
def define_local_fs_resource():
    def _create_resource(info):
        resource = LocalFsHandleResource.for_pipeline_run(info.run_id)
        yield resource
        if info.config['cleanup_files']:
            LocalFsHandleResource.clean_up_dir(info.run_id)

    return ResourceDefinition(
        resource_fn=_create_resource,
        config_field=Field(
            Dict({'cleanup_files': Field(Bool, is_optional=True, default_value=True)})
        ),
    )
```

This is now a self-contained piece that can be reused in other contexts as well.

Additionally, we now guarantee a system-generated run_id, so the manually created pipeline_guid resource is no longer relevant. The rest of the "resources" in the unittesting context are None, and we have a special helper to create "none" resources.

Let's put it all together:

```
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
            'cooper_pair': ResourceDefinition.none_resource(),
        },
        context_fn=create_allscripts_fileload_unittest_context,
        description='''
Context for use in unit tests. It does not allow for any interaction with aws
or s3, and can only be used for a subset of the pipeline that can execute on a
local machine.

This context does not log to file and also has a configurable log_level.
        '''
    )

def create_allscripts_fileload_unittest_context(info):
    data_source_run_id = info.config['data_source_run_id']
    log_level = level_from_string(info.config['log_level'])

    yield ExecutionContext(
        loggers=[define_colored_console_logger('dagster', log_level)],
        context_stack={
            'data_source_run_id': data_source_run_id,
            'data_source': 'allscripts',
        },
    )
```

Notice a few things. The bulk of the context creation function is now gone. Instead of having to manually create the `AllscriptsFileloadResources`, that is replacea by a class (a `namedtuple`) that is system-synthesized. Predictably it has N fields, one for each resource. The pipeline-code-facing API is the same, it just requires less boilerplate within the pipeline infrastructure.

**Configuring a Resource**

The configuration schema changes, as each resource has it's own section.

Before:

```
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

```
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

While slightly more verbose, you will be able to count on more consistent of configuration between pipelines as you reuse resources, and you an even potentially share resource configuration *between* pipelines using the configuration file merging feature of 0.3.0



