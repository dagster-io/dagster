from .simple_graph import do_it_all

# pylint: disable=unused-variable


def execute_simple_graph():
    # start_execute
    result = do_it_all.execute_in_process()
    # end_execute

    # start_retrieve_output
    output = result.output_for_node("do_something")
    events = result.events_for_node("do_something")
    # end_retrieve_output
