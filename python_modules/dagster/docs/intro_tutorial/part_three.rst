An actual DAG
-------------

Next we will build a slightly more complicated DAG that demonstrates how it
effects execution order. In this case will be build a diamond dag:

.. code-block:: python

    from dagster import *

    #   B
    #  / \
    # A   D
    #  \ /
    #   C


    @lambda_solid
    def solid_a():
        print('a: 1')
        return 1


    @lambda_solid(inputs=[InputDefinition('arg_a')])
    def solid_b(arg_a):
        print('b: {b}'.format(b=arg_a * 2))
        return arg_a * 2


    @lambda_solid(inputs=[InputDefinition('arg_a')])
    def solid_c(arg_a):
        print('c: {c}'.format(c=arg_a * 3))
        return arg_a * 3


    @lambda_solid(inputs=[
        InputDefinition('arg_b'),
        InputDefinition('arg_c'),
    ])
    def solid_d(arg_b, arg_c):
        print('d: {d}'.format(d=arg_b * arg_c))


    if __name__ == '__main__':
        execute_pipeline(
            PipelineDefinition(
                # The order of this solid list does not matter.
                # The dependencies argument determines execution order.
                # Solids will execute in topological order.
                solids=[solid_d, solid_c, solid_b, solid_a],
                dependencies={
                    'solid_b': {
                        'arg_a': DependencyDefinition('solid_a'),
                    },
                    'solid_c': {
                        'arg_a': DependencyDefinition('solid_a'),
                    },
                    'solid_d': {
                        'arg_b': DependencyDefinition('solid_b'),
                        'arg_c': DependencyDefinition('solid_c'),
                    }
                }
            )
        )

Again it is worth noting how we are connecting *inputs* and *outputs* rather than just *tasks*.
Point your attention to the ``solid_d`` entry in the dependencies dictionary. We are declaring
dependencies on a per-input basis.

Save this to a file named ``step_three.py``

.. code-block:: sh

    $ python3 step_three.py
    a: 1
    b: 2
    c: 3
    d: 6

In this case ``solid_b`` happens to execute before ``solid_c``. However ``solid_c`` executing
before ``solid_b`` would also be a valid execution order given this DAG.
