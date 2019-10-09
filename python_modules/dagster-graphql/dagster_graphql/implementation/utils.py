def capture_dauphin_error(fn):
    def _fn(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except UserFacingGraphQLError as de_exception:
            return de_exception.dauphin_error

    return _fn


class UserFacingGraphQLError(Exception):
    def __init__(self, dauphin_error, *args, **kwargs):
        self.dauphin_error = dauphin_error
        super(UserFacingGraphQLError, self).__init__(*args, **kwargs)
