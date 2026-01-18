class InputStepBuilder:
    def __init__(self, prompt, fields, key=None):
        self._step = {"input": prompt, "fields": fields}
        if key is not None:
            self._step["key"] = key

    def with_condition(self, condition):
        self._step["if"] = condition
        return self

    def depends_on(self, dependencies):
        self._step["depends_on"] = dependencies
        return self

    def build(self):
        return self._step
