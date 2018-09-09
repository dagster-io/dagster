Pipeline Execution
------------------

So far we've been driving execution of pipelines from python APIs. Now it is
time to instead drive these from the command line.

Similar to the the part six tutorial, we are going to create a pipeline, a repository,
and a yaml file so that the CLI tool can know about the repository.

.. code-block:: python

    from dagster import *

    @solid
    def double_the_word(_context, conf):
        return conf['config_key'] * 2

    @lambda_solid(inputs=[InputDefinition('word')])
    def count_letters(word):
        counts = defaultdict(int)
        for letter in word:
            counts[letter] += 1
        return dict(counts)

    def define_part_seven_pipeline():
        return PipelineDefinition(
            name='part_seven',
            solids=[double_the_word, count_letters],
            dependencies={
                'count_letters': {
                    'word': DependencyDefinition('double_the_word'),
                },
            },
        )

    def define_part_seven_repo():
        return RepositoryDefinition(
            name='part_seven_repo',
            pipeline_dict={
                'part_seven': define_part_seven_pipeline,
            },
        )
And now the repository file:

.. code-block:: yaml

    repository:
        file: part_seven.py
        fn: define_part_seven_repo

Now we want to execute it from the command line. In order to do that we need to create a yaml file
with all the elements we need to create an environment. The form of this file is very similar
to the in-memory ``config.Environment`` and related objects that were used in previous steps
in the tutorial.

.. code-block:: yaml

    context:
        config:
            log_level: DEBUG

    solids:
        double_the_word:
            config:
                word: bar

With these elements in place we can now drive execution from the CLI

.. code-block:: sh

    dagster pipeline execute part_seven -e env.yml
    2018-09-09 11:47:38 - dagster - DEBUG - message="About to execute the compute node graph in the following order ['double_the_word.transform', 'count_letters.transform']"
    2018-09-09 11:47:38 - dagster - DEBUG - message="Entering execute_compute_nodes loop. Order: ['double_the_word.transform', 'count_letters.transform']"
    2018-09-09 11:47:38 - dagster - DEBUG - message="Executing core transform for solid double_the_word." solid=double_the_word
    2018-09-09 11:47:38 - dagster - DEBUG - message="Solid double_the_word emitted output "result" value 'barbar'" solid=double_the_word
    2018-09-09 11:47:38 - dagster - INFO - metric:core_transform_time_ms=0.136 solid=double_the_word
    2018-09-09 11:47:38 - dagster - DEBUG - message="Executing core transform for solid count_letters." solid=count_letters
    2018-09-09 11:47:38 - dagster - DEBUG - message="Solid count_letters emitted output "result" value {'b': 2, 'a': 2, 'r': 2}" solid=count_letters
    2018-09-09 11:47:38 - dagster - INFO - metric:core_transform_time_ms=0.130 solid=count_letters