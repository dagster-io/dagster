from dagster import RepositoryDefinition

from dagster_contrib.dagster_examples.tutorials import (
    test_intro_tutorial_part_one,
    test_intro_tutorial_part_two,
    test_intro_tutorial_part_three,
    test_intro_tutorial_part_four,
    test_intro_tutorial_part_five,
    test_intro_tutorial_part_ten,
    test_intro_tutorial_part_eleven,
    test_intro_tutorial_part_twelve,
    test_intro_tutorial_part_thirteen,
    test_intro_tutorial_part_fourteen,
)

from dagster_contrib.dagster_examples.tutorials.test_intro_tutorial_part_six import (
    test_intro_tutorial_part_six
)

from dagster_contrib.dagster_examples.tutorials.test_intro_tutorial_part_seven import (
    test_intro_tutorial_part_seven
)

from dagster_contrib.dagster_examples.tutorials.test_intro_tutorial_part_eight import (
    test_intro_tutorial_part_eight
)

from dagster_contrib.dagster_examples.tutorials.test_intro_tutorial_part_nine import (
    test_intro_tutorial_part_nine
)


def define_repository():
    return RepositoryDefinition(
        name='tutorial_repository',
        pipeline_dict={
            'part_one_pipeline':
            test_intro_tutorial_part_one.define_pipeline,
            'part_two_pipeline':
            test_intro_tutorial_part_two.define_pipeline,
            'part_three_pipeline':
            test_intro_tutorial_part_three.define_pipeline,
            'part_four_pipeline':
            test_intro_tutorial_part_four.define_pipeline,
            'part_five_step_one_pipeline':
            test_intro_tutorial_part_five.define_step_one_pipeline,
            'part_five_step_two_pipeline':
            test_intro_tutorial_part_five.define_step_two_pipeline,
            'part_five_step_three_pipeline':
            test_intro_tutorial_part_five.define_step_three_pipeline,
            'part_six_pipeline':
            test_intro_tutorial_part_six.define_part_six_pipeline,
            'part_seven_pipeline':
            test_intro_tutorial_part_seven.define_part_seven_pipeline,
            'part_eight_step_one_pipeline':
            test_intro_tutorial_part_eight.define_part_eight_step_one_pipeline,
            'part_eight_step_two_pipeline':
            test_intro_tutorial_part_eight.define_part_eight_step_two_pipeline,
            'part_eight_step_three_pipeline':
            test_intro_tutorial_part_eight.define_part_eight_step_three_pipeline,
            'part_nine_step_one_pipeline':
            test_intro_tutorial_part_nine.define_part_nine_step_one_pipeline,
            'part_nine_step_two_pipeline':
            test_intro_tutorial_part_nine.define_part_nine_step_two_pipeline,
            'part_nine_final_pipeline':
            test_intro_tutorial_part_nine.define_part_nine_final_pipeline,
            'part_ten_step_one_pipeline':
            test_intro_tutorial_part_ten.define_part_ten_step_one_pipeline,
            'part_eleven_step_one_pipeline':
            test_intro_tutorial_part_eleven.define_part_eleven_step_one_pipeline,
            'part_eleven_step_two_pipeline':
            test_intro_tutorial_part_eleven.define_part_eleven_step_two_pipeline,
            'part_eleven_step_three_pipeline':
            test_intro_tutorial_part_eleven.define_part_eleven_step_three_pipeline,
            'part_twelve_step_one_pipeline':
            test_intro_tutorial_part_twelve.define_part_twelve_step_one_pipeline,
            'part_twelve_step_two_pipeline':
            test_intro_tutorial_part_twelve.define_part_twelve_step_two_pipeline,
            'part_twelve_step_three_pipeline':
            test_intro_tutorial_part_twelve.define_part_twelve_step_three_pipeline,
            'part_twelve_step_four_pipeline':
            test_intro_tutorial_part_twelve.define_part_twelve_step_four_pipeline,
            'part_thirteen_step_one_pipeline':
            test_intro_tutorial_part_thirteen.define_part_thirteen_step_one_pipeline,
            'part_thirteen_step_two_pipeline':
            test_intro_tutorial_part_thirteen.define_part_thirteen_step_two_pipeline,
            'part_thirteen_step_three_pipeline':
            test_intro_tutorial_part_thirteen.define_part_thirteen_step_three_pipeline,
            'part_fourteen_step_one_pipeline':
            test_intro_tutorial_part_fourteen.define_part_fourteen_step_one_pipeline,
        },
    )
