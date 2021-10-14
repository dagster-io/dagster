import time

import dagster


@dagster.solid
def solid():
    time.sleep(30)
    return True


@dagster.pipeline
def pipeline():
    solid()


@dagster.repository
def repository():
    return [pipeline]
