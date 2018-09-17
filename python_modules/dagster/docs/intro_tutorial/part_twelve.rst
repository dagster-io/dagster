User-defined Types
------------------

So far we have only used the built-in types the come with dagster to describe
data flowing between different solids. However this only gets one so far, and
is typically only useful for toy pipelines. You are going to want to define
our own custom types to describe your pipeline- and runtime-specific data
structures.

For the first example, we'll show how to flow a plain python object
through the a pipeline and then describe that object in the type system.
Let's say we wanted to flow a tuple through a pipeline.

.. code-block:: python

    StringTuple = namedtuple('StringTuple', 'str_one str_two')

    @lambda_solid
    def produce_valid_value():
        return StringTuple(str_one='value_one', str_two='value_two')


And then we want to consume it. However, we want this to be type-checked
and metadata to be surface in tools like dagit.

To do this we'll introduce a dagster type.

.. code-block:: python

    StringTupleType = types.PythonObjectType(
        'StringTuple',
        python_type=StringTuple,
        description='A tuple of strings.',
    )

And then annotate relevant functions with it.

.. code-block:: python

    @lambda_solid(output=OutputDefinition(StringTupleType))
    def produce_valid_value():
        return StringTuple(str_one='value_one', str_two='value_two')

    @solid(inputs=[InputDefinition('string_tuple', StringTupleType)])
    def consume_string_tuple(info, string_tuple):
        info.context.info(
            'Logging value {string_tuple}'.format(
                string_tuple=string_tuple
            )
        )

    def define_part_twelve_step_one():
        return PipelineDefinition(
            name='part_twelve_step_one',
            solids=[produce_valid_value, consume_string_tuple],
            dependencies={
                'consume_string_tuple': {
                    'string_tuple': 
                    DependencyDefinition('produce_valid_value')
                }
            },
        )

    if __name__ == '__main__':
        execute_pipeline(define_part_twelve_step_())

.. code-block:: sh

    $ python part_twelve.py
    ... log spew
    2018-09-17 06:55:06 - dagster - INFO - orig_message="Logging value StringTuple(str_one='value_one', str_two='value_two')" log_message_id="675f905d-c1f4-4539-af26-c28d23a757be" pipeline="part_twelve_step_one" solid="consume_string_tuple"
    ...

Now what if things go wrong? Imagine you made an error and wired up `consume_string_tuple`
to a solid

.. code-block:: python

    @lambda_solid
    def produce_invalid_value():
        return 'not_a_tuple'

    def define_part_twelve_step_two():
        return PipelineDefinition(
            name='part_twelve_step_two',
            solids=[produce_invalid_value, consume_string_tuple],
            dependencies={
                'consume_string_tuple': {
                    'string_tuple':
                    DependencyDefinition('produce_invalid_value')
                }
            },
        )

    if __name__ == '__main__':
        execute_pipeline(define_part_twelve_step_two())

If you run this you'll get some helpful error messages

.. code-block:: sh

    $ python part_twelve.py
    ... log spew
    2018-09-17 07:00:11 - dagster - ERROR - orig_message="Solid consume_string_tuple input string_tuple received value not_a_tuple which does not pass the typecheck for Dagster type StringTuple. Compute node consume_string_tuple.transform" log_message_id="4070d30d-8b29-4130-bbd6-6049d40e742b" pipeline="part_twelve_step_two"    
    ... stack trace
    dagster.core.errors.DagsterEvaluateValueError: Expected valid value for StringTuple but got 'not_a_tuple'
    ... more stack trace
    dagster.core.errors.DagsterTypeError: Solid consume_string_tuple input string_tuple received value not_a_tuple which does not pass the typecheck for Dagster type StringTuple. Compute node consume_string_tuple.transform

Custom Types
^^^^^^^^^^^^

The type system is very flexible, and values can by both type-checked and coerced by user-defined code.

Imagine we wants to be able process social security numbers and ensure that they are well-formed
throughout the whole pipeline.

In order to do this we'll define a type.

.. code-block:: python

    class SSNString(str):
        pass

    class SSNStringTypeClass(types.DagsterType):
        def __init__(self):
            super(SSNStringTypeClass, self).__init__(name='SSNString')

        def evaluate_value(self, value):
            if isinstance(value, SSNString):
                return value

            if not isinstance(value, str):
                raise DagsterEvaluateValueError(
                    '{value} is not a string. SSNStringType typecheck failed'.format(value=repr(value))
                )

            if not re.match(r'^(\d\d\d)-(\d\d)-(\d\d\d\d)$', value):
                raise DagsterEvaluateValueError(
                    '{value} did not match SSN regex'.format(value=repr(value))
                )

            return SSNString(value)


    SSNStringType = SSNStringTypeClass()

This type does a couple things. One is that ensures that any string that gets passed to
evaluate_value matches a strict regular expression. You'll also notice that it coerces
that incoming string type to a type called `SSNString`. This type just trivially inherits
from ``str``, but it signifies that the typecheck has already occured. That means if 
evaluate_value is called again, the bulk of the typecheck can be short-circuited, saving
repeated processing through the pipeline. (Note: this is slightly silly because the amount
of computation here is trivial, but one can imagine types that require significant
amounts of computation to verify). 


.. code-block:: python

    @lambda_solid
    def produce_valid_ssn_string():
        return '394-30-2032'

    @solid(inputs=[InputDefinition('ssn', SSNStringType)])
    def consume_ssn(info, ssn):
        if not isinstance(ssn, SSNString):
            raise Exception('This should never be thrown')
        info.context.info('ssn: {ssn}'.format(ssn=ssn))

    def define_part_twelve_step_three():
        return PipelineDefinition(
            name='part_twelve_step_three',
            solids=[produce_valid_ssn_string, consume_ssn],
            dependencies={
                'consume_ssn': {
                    'ssn':
                    DependencyDefinition('produce_valid_ssn_string')
                }
            },
        )

    if __name__ == '__main__':
        execute_pipeline(define_part_twelve_step_three())

You'll note that the exception in ``consume_ssn`` was not thrown, meaning that the
str was coerced to an SSNString by the dagster type.

Future Directions
^^^^^^^^^^^^^^^^^

1. Up-front type checking
2. Serializations
3. Hashing