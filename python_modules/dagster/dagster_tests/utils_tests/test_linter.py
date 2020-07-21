import astroid
import pylint.testutils

from dagster.utils.linter import define_dagster_checker


class TestDagsterChecker(pylint.testutils.CheckerTestCase):
    CHECKER_CLASS = define_dagster_checker()

    def test_finally_yield(self):
        yield_node = astroid.extract_node(
            """
        def foo():
            try:
                yield
            except ImportError:
                pass
            finally:
                yield #@
            """
        )

        with self.assertAddsMessages(
            pylint.testutils.Message(msg_id="finally-yield", node=yield_node)
        ):
            self.checker.visit_yield(yield_node)

    def test_handled_finally_yield(self):
        yield_node = astroid.extract_node(
            """
        def foo():
            try:
                yield
            except ImportError:
                pass
            except GeneratorExit:
                pass
            finally:
                yield #@
            """
        )

        with self.assertNoMessages():
            self.checker.visit_yield(yield_node)

    def test_finally_yield_expression(self):
        yield_node = astroid.extract_node(
            """
        def foo():
            cond = True
            try:
                yield 1
            except ImportError:
                pass
            finally:
                if cond:
                    yield 2 #@
            """
        )

        with self.assertAddsMessages(
            pylint.testutils.Message(msg_id="finally-yield", node=yield_node)
        ):
            self.checker.visit_yield(yield_node)
