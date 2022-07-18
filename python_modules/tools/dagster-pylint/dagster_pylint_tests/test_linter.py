import astroid
import pylint.testutils
import pytest

from dagster_pylint import DagsterChecker


class TestDagsterChecker(pylint.testutils.CheckerTestCase):
    CHECKER_CLASS = DagsterChecker

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
            pylint.testutils.MessageTest(
                msg_id="finally-yield",
                node=yield_node,
                line=8,
                col_offset=8,
                end_line=8,
                end_col_offset=13,
            )
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
            pylint.testutils.MessageTest(
                msg_id="finally-yield",
                node=yield_node,
                line=10,
                col_offset=12,
                end_line=10,
                end_col_offset=19,
            )
        ):
            self.checker.visit_yield(yield_node)

    @pytest.mark.parametrize("statement", ["print(abc)", "def afunc():\n    print(abc)"])
    def test_print_call(self, statement):
        node = astroid.extract_node(statement)
        self.walk(node)
        assert [msg.msg_id for msg in self.linter.release_messages()] == ["print-call"]
