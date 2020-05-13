from .represented import RepresentedPipeline


class HistoricalPipeline(RepresentedPipeline):
    @property
    def config_schema_snapshot(self):
        raise NotImplementedError('TODO')

    def get_mode_def_snap(self, mode_name):
        raise NotImplementedError('TODO')
