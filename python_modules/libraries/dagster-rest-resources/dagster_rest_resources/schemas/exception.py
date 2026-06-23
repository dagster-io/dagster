class DagsterPlusUnauthorizedError(Exception):
    pass


class DagsterPlusGraphqlError(Exception):
    pass


class UnconfirmedProdDeletionError(Exception):
    pass


class S3Error(Exception):
    pass
