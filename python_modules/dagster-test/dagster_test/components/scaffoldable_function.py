from dagster_components.scaffold.scaffold import Scaffolder, scaffold_with


class SomeScaffolder(Scaffolder):
    def scaffold(self, request, params):
        pass


@scaffold_with(SomeScaffolder)
def scaffoldable_fn():
    """A sample function that can be scaffolded."""
    pass
