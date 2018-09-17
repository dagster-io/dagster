Pipeline Execution
------------------

So far we've been driving execution of pipelines from python APIs. Now it is
time to instead drive these from the command line.

Similar to the the part six tutorial, we are going to create a pipeline, a repository,
and a yaml file so that the CLI tool can know about the repository.

.. code-block:: python

    from dagster import *

    @solid
    def double_the_word(info):
        return info.config['word'] * 2

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
    2018-09-10 06:29:41 - dagster - DEBUG - orig_message="About to execute the compute node graph in the following order ['double_the_word.transform', 'count_letters.transform']" log_message_id="12c7c3f0-ea99-44ce-bd1e-5c362560795a"
    2018-09-10 06:29:41 - dagster - DEBUG - orig_message="Entering execute_compute_nodes loop. Order: ['double_the_word.transform', 'count_letters.transform']" log_message_id="c6750058-1a1c-49cd-b529-e149cd6fee27"
    2018-09-10 06:29:41 - dagster - DEBUG - orig_message="Executing core transform for solid double_the_word." log_message_id="09eb5f50-3681-4594-a1e5-d1a007630a47" solid="double_the_word"
    2018-09-10 06:29:41 - dagster - DEBUG - orig_message="Solid double_the_word emitted output \"result\" value 'barbar'" log_message_id="44af0ca9-a62c-472d-ae9b-91cd0a66fe8d" solid="double_the_word"
    2018-09-10 06:29:41 - dagster - DEBUG - orig_message="Finished executing transform for solid double_the_word. Time elapsed: 0.269 ms" log_message_id="ad8f806d-6022-4b81-865d-cc33bff03e0f" solid="double_the_word" execution_time_ms=0.2689361572265625
    2018-09-10 06:29:41 - dagster - DEBUG - orig_message="Executing core transform for solid count_letters." log_message_id="108c91b6-4503-4004-947b-1d5ccb77698d" solid="count_letters"
    2018-09-10 06:29:41 - dagster - DEBUG - orig_message="Solid count_letters emitted output \"result\" value {'b': 2, 'a': 2, 'r': 2}" log_message_id="000cdb0e-7471-42c1-9616-281eaea28f6c" solid="count_letters"
    2018-09-10 06:29:41 - dagster - DEBUG - orig_message="Finished executing transform for solid count_letters. Time elapsed: 0.160 ms" log_message_id="9bb52b66-519c-4301-abec-0ff1b6a62eae" solid="count_letters" execution_time_ms=0.16021728515625