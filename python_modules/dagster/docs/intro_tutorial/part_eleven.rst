Multiple Outputs
----------------

So far all of the examples have been solids that have a single output. However
solids support an arbitrary number of outputs. This allows for downstream
solids to only tie their dependency to a single output. Additionally -- by
allowing for multiple outputs to conditionally fire -- this also ends up
supporting dynamic branching and conditional execution of pipelines.


.. code-block:: python

    @solid(
        outputs=[
            OutputDefinition(dagster_type=types.Int, name='out_one'),
            OutputDefinition(dagster_type=types.Int, name='out_two'),
        ],
    )
    def return_dict_results(_info):
        return MultipleResults.from_dict({
            'out_one': 23,
            'out_two': 45,
        })

    @solid(inputs=[InputDefinition('num', dagster_type=types.Int)])
    def log_num(info, num):
        info.context.info('num {num}'.format(num=num))
        return num

    @solid(inputs=[InputDefinition('num', dagster_type=types.Int)])
    def log_num_squared(info, num):
        info.context.info(
            'num_squared {num_squared}'.format(num_squared=num * num)
        )
        return num * num

Notice how ``return_dict_results`` has two outputs. For the first time
we have provided the name argument to an :py:class:`OutputDefinition`. (It
defaults to ``'result'``, as it does in a :py:class:`DependencyDefinition`)
These names must be unique and results returns by a solid transform function
must be named one of these inputs. (In all previous examples the value returned
by the transform had been wrapped in a :py:class:`Result` object with the name
``'result'``.)

So from ``return_dict_results`` we used :py:class:`MultipleResults` to return
all outputs from this transform.

Next let's examine the :py:class:`PipelineDefinition`:

.. code-block:: python

    def define_part_eleven_step_one():
        return PipelineDefinition(
            name='part_eleven_step_one',
            solids=[return_dict_results, log_num, log_num_squared],
            dependencies={
                'log_num': {
                    'num': DependencyDefinition(
                        'return_dict_results',
                        'out_one',
                    ),
                },
                'log_num_squared': {
                    'num': DependencyDefinition(
                        'return_dict_results',
                        'out_two',
                    ),
                },
            },
        )

Just like this tutorial is the first example of an :py:class:`OutputDefinition` with
a name, this is also the first time that a :py:class:`DependencyDefinition` has
specified name, because dependencies point to a particular **output** of a solid,
rather than to the solid itself. In previous examples the name of output has been
defaulted to ``'result'``.

With this we can run the pipeline:

.. code-block:: python

    execute_pipeline(define_part_eleven_step_one())

and run it: foobar

.. code-block:: sh

    python step_eleven.py
    ... log spew
    2018-09-16 17:08:09 - dagster - INFO - orig_message="Solid return_dict_results emitted output \"out_one\" value 23" log_message_id="76fe7e9b-f11c-43a3-ac17-8bc8616bd0bd" pipeline="part_eleven_step_one" solid="return_dict_results"
    2018-09-16 17:08:09 - dagster - INFO - orig_message="Solid return_dict_results emitted output \"out_two\" value 45" log_message_id="ef11a36a-da7b-4df1-9eeb-0f92c04d392a" pipeline="part_eleven_step_one" solid="return_dict_results"
    ... more log spew

The :py:class:`MultipleResults` class is not the only way to return multiple to
results from a solid transform function. You can also yield multiple instances
of the `Result` object. (Note: this is actually the core specification
of the transform function: all other forms are implemented in terms of
the iterator form.)

.. code-block:: python

    @solid(
        outputs=[
            OutputDefinition(dagster_type=types.Int, name='out_one'),
            OutputDefinition(dagster_type=types.Int, name='out_two'),
        ],
    )
    def yield_outputs(_info):
        yield Result(23, 'out_one')
        yield Result(45, 'out_two')

    def define_part_eleven_step_two():
        return PipelineDefinition(
            name='part_eleven_step_two',
            solids=[yield_outputs, log_num, log_num_squared],
            dependencies={
                'log_num': {
                    'num': DependencyDefinition('yield_outputs', 'out_one')
                },
                'log_num_squared': {
                    'num': DependencyDefinition('yield_outputs', 'out_two')
                },
            },
        )

    if __name__ == '__main__':
        execute_pipeline(define_part_eleven_step_two())

... and you'll see the same log spew around outputs in this version:

.. code-block:: sh
    $ python part_eleven.py
    2018-09-16 17:53:15 - dagster - INFO - orig_message="Solid yield_outputs emitted output \"out_one\" value 23" log_message_id="7313cb9c-85dc-4467-9f48-a724a75db63f" pipeline="part_eleven_step_two" solid="yield_outputs"
    2018-09-16 17:53:15 - dagster - INFO - orig_message="Solid yield_outputs emitted output \"out_two\" value 45" log_message_id="fed2866f-5f29-4bbd-b124-90bd9eda8690" pipeline="part_eleven_step_two" solid="yield_outputs"

Conditional Outputs
^^^^^^^^^^^^^^^^^^^

Multiple outputs are the mechanism by which we implement branching or conditional execution.

Let's modify the first solid above to conditionally emit one output or the other based on config
and then execute that pipeline.

.. code-block:: python

    @solid(
        config_def=ConfigDefinition(types.String, description='Should be either out_one or out_two'),
        outputs=[
            OutputDefinition(dagster_type=types.Int, name='out_one'),
            OutputDefinition(dagster_type=types.Int, name='out_two'),
        ],
    )
    def conditional(info):
        if info.config == 'out_one':
            yield Result(23, 'out_one')
        elif info.config == 'out_two':
            yield Result(45, 'out_two')
        else:
            raise Exception('invalid config')


    def define_part_eleven_step_three():
        return PipelineDefinition(
            name='part_eleven_step_three',
            solids=[conditional, log_num, log_num_squared],
            dependencies={
                'log_num': {
                    'num': DependencyDefinition('conditional', 'out_one')
                },
                'log_num_squared': {
                    'num': DependencyDefinition('conditional', 'out_two')
                },
            },
        )

    if __name__ == '__main__':
        execute_pipeline(
            define_part_eleven_step_three(),
            {
                'solids': {
                    'conditional': {
                        'config': 'out_two'
                    },
                },
            },
        ) 

Note that we are configuring this solid to *only* emit out_two which will end up
only triggering log_num_squared. log_num will never be executed.

.. code-block:: sh

    $ python part_eleven.py
    ... log spew
    2018-09-16 18:58:32 - dagster - INFO - orig_message="Solid conditional emitted output \"out_two\" value 45" log_message_id="f6fd78c5-c25e-40ea-95ef-6b80d12155de" pipeline="part_eleven_step_three" solid="conditional"
    2018-09-16 18:58:32 - dagster - INFO - orig_message="Solid conditional did not fire outputs {'out_one'}" log_message_id="d548ea66-cb10-42b8-b150-aed8162cc25c" pipeline="part_eleven_step_three" solid="conditional"    
    ... log spew
