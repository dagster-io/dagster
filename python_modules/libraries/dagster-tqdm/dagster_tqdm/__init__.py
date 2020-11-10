from tqdm.auto import tqdm


class dagster_tqdm(tqdm):
    def __init__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        kwargs["mininterval"] = kwargs.get("mininterval", 5)

        self.context = kwargs.pop("context")
        self._is_notebook = None

        super().__init__(*args, **kwargs)

    @property
    def is_notebook(self):
        if self._is_notebook is not None:
            return self._is_notebook

        try:
            shell = get_ipython().__class__.__name__
            self._is_notebook = shell == "ZMQInteractiveShell"
        except NameError:
            self._is_notebook = False

        return self._is_notebook

    def display(self, **kwargs):
        super().display(**kwargs)

        if not self.is_notebook:
            fmt = self.format_dict
            if "bar_format" in fmt and fmt["bar_format"]:
                fmt["bar_format"] = fmt["bar_format"].replace("<bar/>", "{bar}")
            else:
                fmt["bar_format"] = "{l_bar}{bar}{r_bar}"
            fmt["bar_format"] = fmt["bar_format"].replace("{bar}", "{bar:10u}")
            self.context.log.info(self.format_meter(**fmt))


__all__ = ["dagster_tqdm"]
