from abc import ABCMeta, abstractmethod

import six


class IConfigMappable(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def process_config(self, config):
        '''
        Args:
            config (Any): The configuration to be processed.

        Returns (EvaluateValueResult):
            If successful, the value is the "processed" configuration, which has defaults and
            environment variables resolved.
        '''
        raise NotImplementedError()

    @abstractmethod
    def configured(self, config_or_config_fn, config_schema=None, **kwargs):
        '''
        Wraps this object in an object of the same type that provides configuration to the inner
        object.

        Args:
            config_or_config_fn (Union[Any, Callable[[Any], Any]]): Either (1) Run configuration
                that fully satisfies this object's config schema or (2) A function that accepts run
                configuration and returns run configuration that fully satisfies this object's
                config schema.  In the latter case, config_schema must be specified.  When
                passing a function, it's easiest to use :py:func:`configured`.
            config_schema (ConfigSchema): If config_or_config_fn is a function, the config schema
                that its input must satisfy.
            **kwargs: Arbitrary keyword arguments that will be passed to the initializer of the
                returned object.

        Returns (IConfigMappable): A configured version of this object.
        '''
        raise NotImplementedError()


def configured(configurable, config_schema=None, **kwargs):
    '''
    A decorator that makes it easy to create a function-configured version of an object.

    Args:
        configurable (IConfigMappable): An object that can be configured.
        config_schema (ConfigSchema): The config schema that the inputs to the decorated function
            must satisfy.
        **kwargs: Arbitrary keyword arguments that will be passed to the initializer of the returned
            object.

    Returns (Callable[[Union[Any, Callable[[Any], Any]]], IConfigMappable])

    Examples:

        .. code-block:: python

            dev_s3 = configured(s3_resource)({'bucket': 'dev'})

            @configured(s3_resource):
            def dev_s3(_):
                return {'bucket': 'dev'}

            @configured(s3_resource, {'bucket_prefix', str}):
            def dev_s3(config):
                return {'bucket': config['bucket_prefix'] + 'dev'}
    '''

    def _configured(config_or_config_fn):
        return configurable.configured(
            config_schema=config_schema, config_or_config_fn=config_or_config_fn, **kwargs
        )

    return _configured
