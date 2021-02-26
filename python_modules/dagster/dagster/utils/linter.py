def define_dagster_checker():
    # if we have reached here, we have pylint/astroid installed, since that is what registers the
    # linter

    import astroid
    from pylint.checkers import BaseChecker
    from pylint.interfaces import IAstroidChecker

    INFO_LINK = "https://amir.rachum.com/blog/2017/03/03/generator-cleanup/"

    class DagsterChecker(BaseChecker):
        __implements__ = IAstroidChecker

        name = "DagsterChecker"
        priority = -1
        msgs = {
            "W0001": (
                "Yield in finally without handling GeneratorExit (see {})".format(INFO_LINK),
                "finally-yield",
                "Cannot yield in a finally block without handling GeneratorExit (see {})".format(
                    INFO_LINK
                ),
            ),
            "W0002": ("print() call", "print-call", "Cannot call print()"),
            "W0003": (
                "setting daemon=True in threading.Thread constructor",
                "daemon-thread",
                "Cannot set daemon=True in threading.Thread constructor (py2 compat)",
            ),
            "W0004": (
                "calling pendulum.create or pendulum.datetime",
                "pendulum-create",
                "Use dagster.seven.create_pendulum_time instead of pendulum.create or pendulum.datetime",
            ),
            "W0005": (
                "calling in_tz() on a pendulum datetime",
                "pendulum-in-tz",
                "Use dagster.seven.to_timezone instead of calling in_tz on a pendulum datetime",
            ),
        }
        options = ()

        def visit_yield(self, node):
            current = node
            while current:
                if isinstance(current, (astroid.ClassDef, astroid.FunctionDef)):
                    break

                if isinstance(current, astroid.TryFinally):
                    if not current.finalbody:
                        # no finally block (weird)
                        break

                    for x in current.finalbody:
                        if not x.eq(node) and not x.parent_of(node):
                            # this yield was not in the finally block
                            return

                    if (
                        current.body
                        and isinstance(current.body[0], astroid.TryExcept)
                        and any(
                            handler.catch(["GeneratorExit"]) for handler in current.body[0].handlers
                        )
                    ):
                        # this try block catches and handles GeneratorExit
                        return

                    self.add_message("finally-yield", node=node)

                current = current.parent

        def visit_call(self, node):
            if (
                node.callable
                and isinstance(node.func, astroid.node_classes.Name)
                and node.func.name == "print"
            ):
                self.add_message("print-call", node=node)
            if (
                node.callable
                and isinstance(node.func, astroid.node_classes.Attribute)
                and node.func.attrname == "Thread"
                and isinstance(node.func.expr, astroid.node_classes.Name)
                and node.func.expr.name == "threading"
                and "daemon" in [keyword.arg for keyword in node.keywords]
            ):
                self.add_message("daemon-thread", node=node)
            if (
                node.callable
                and isinstance(node.func, astroid.node_classes.Attribute)
                and (node.func.attrname == "create" or node.func.attrname == "datetime")
                and isinstance(node.func.expr, astroid.node_classes.Name)
                and node.func.expr.name == "pendulum"
            ):
                self.add_message("pendulum-create", node=node)

            if (
                node.callable
                and isinstance(node.func, astroid.node_classes.Attribute)
                and (node.func.attrname == "in_tz")
            ):
                self.add_message("pendulum-in-tz", node=node)

    return DagsterChecker


def register_solid_transform():
    import astroid

    def _is_solid(node):
        if not node.decorators:
            return False
        return (
            "dagster.core.definitions.decorators.solid.solid" in node.decoratornames()
            or "dagster.core.definitions.decorators.solid._Solid" in node.decoratornames()
            or "dagster.core.definitions.decorators.composite_solid._CompositeSolid"
            in node.decoratornames()
            or "dagster.core.definitions.decorators.composite_solid.composite_solid"
            in node.decoratornames()
        )

    @astroid.inference_tip
    def _modify_return(node, context=None):
        module = astroid.parse(
            f"""
        def {node.name}(*args, **kwargs):
            return unknown()
            """
        )

        mock_function = next(module.igetattr("solid", context=context))
        return iter([mock_function])

    # Register a new inference result for solid decorated functions which effectively
    # blanks out the inference by changing the return type to the output of an unknown function
    astroid.MANAGER.register_transform(astroid.FunctionDef, _modify_return, _is_solid)


def register(linter):
    checker = define_dagster_checker()
    linter.register_checker(checker(linter))
    register_solid_transform()
