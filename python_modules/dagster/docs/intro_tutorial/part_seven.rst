Pipeline Execution
------------------

Similar to the the part six tutorial, we are going to create a pipeline, a repository,
and a yaml file so that the CLI tool can know about the repository.

.. code-block:: python

    @solid(config_field=ConfigDefinition(types.Any))
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
with all the elements we need to create an environment. 

.. code-block:: yaml

    context:
      default:
        config:
          log_level: DEBUG

    solids:
      double_the_word:
        config:
          word: bar

With these elements in place we can now drive execution from the CLI specifying only the pipeline name.
The tool loads the repository using the repository.yml file and looks up the pipeline by name.

.. code-block:: sh

    dagster pipeline execute part_seven -e env.yml
    2018-11-07 15:06:18 - dagster - DEBUG - orig_message="About to execute the compute node graph in the following order ['double_the_word.transform', 'count_letters.transform']" log_message_id="59e612e0-1827-404b-a249-644de6a02f59" run_id="027cdfa1-b240-425d-85d5-d7efaa260da2" pipeline="part_seven"
    2018-11-07 15:06:18 - dagster - DEBUG - orig_message="Entering execute_compute_nodes loop. Order: ['double_the_word.transform', 'count_letters.transform']" log_message_id="6e5ea2f0-6185-449d-8fc3-4492551cc20c" run_id="027cdfa1-b240-425d-85d5-d7efaa260da2" pipeline="part_seven"
    2018-11-07 15:06:18 - dagster - DEBUG - orig_message="Executing core transform for solid double_the_word." log_message_id="2c327d1c-5f84-4ea2-9ff5-7882b6e4413b" run_id="027cdfa1-b240-425d-85d5-d7efaa260da2" pipeline="part_seven" solid="double_the_word" solid_definition="double_the_word"
    2018-11-07 15:06:18 - dagster - INFO - orig_message="Solid double_the_word emitted output \"result\" value 'barbar'" log_message_id="f4e2ec54-bb8e-4b51-a1f4-f3e22331dc46" run_id="027cdfa1-b240-425d-85d5-d7efaa260da2" pipeline="part_seven" solid="double_the_word" solid_definition="double_the_word"
    2018-11-07 15:06:18 - dagster - DEBUG - orig_message="Finished executing transform for solid double_the_word. Time elapsed: 0.215 ms" log_message_id="ed4b2f63-d7ce-4f4a-9a0a-2773ae203123" run_id="027cdfa1-b240-425d-85d5-d7efaa260da2" pipeline="part_seven" solid="double_the_word" solid_definition="double_the_word" execution_time_ms=0.21505355834960938
    2018-11-07 15:06:18 - dagster - DEBUG - orig_message="Executing core transform for solid count_letters." log_message_id="2e08aef2-445c-477e-84a3-6cd8fcecbf63" run_id="027cdfa1-b240-425d-85d5-d7efaa260da2" pipeline="part_seven" solid="count_letters" solid_definition="count_letters"
    2018-11-07 15:06:18 - dagster - INFO - orig_message="Solid count_letters emitted output \"result\" value {'b': 2, 'a': 2, 'r': 2}" log_message_id="baa3e486-b8cb-4cbb-a765-09b22d372a38" run_id="027cdfa1-b240-425d-85d5-d7efaa260da2" pipeline="part_seven" solid="count_letters" solid_definition="count_letters"
    2018-11-07 15:06:18 - dagster - DEBUG - orig_message="Finished executing transform for solid count_letters. Time elapsed: 0.200 ms" log_message_id="5a056fe2-9ab6-49b9-81be-ff4d021dc710" run_id="027cdfa1-b240-425d-85d5-d7efaa260da2" pipeline="part_seven" solid="count_letters" solid_definition="count_letters" execution_time_ms=0.20003318786621094
