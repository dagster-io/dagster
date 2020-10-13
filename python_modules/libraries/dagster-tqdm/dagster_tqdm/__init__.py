from tqdm.auto import tqdm


class dagster_tqdm(tqdm):
    def __init__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        self.context = kwargs.pop('context')
        super().__init__(*args, **kwargs)

    def display(self, **kwargs):
        super().display(**kwargs)
        fmt = self.format_dict
        if 'bar_format' in fmt and fmt['bar_format']:
            fmt['bar_format'] = fmt['bar_format'].replace('<bar/>', '{bar}')
        else:
            fmt['bar_format'] = '{l_bar}{bar}{r_bar}'
        fmt['bar_format'] = fmt['bar_format'].replace('{bar}', '{bar:10u}')
        self.context.log.info(self.format_meter(**fmt))


__all__ = ["dagster_tqdm"]
