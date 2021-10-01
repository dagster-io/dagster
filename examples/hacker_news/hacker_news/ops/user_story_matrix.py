from dataclasses import dataclass

import numpy as np
from dagster import Out, op
from pandas import DataFrame, Series
from scipy.sparse import coo_matrix


@dataclass
class IndexedCooMatrix:
    """A matrix with indexes for the rows and columns"""

    matrix: coo_matrix

    row_index: Series
    """A Series whose index corresponds to the row numbers in the
    matrix and whose values are the corresponding values in the index."""

    col_index: Series
    """A Series whose index corresponds to the col numbers in the
    matrix and whose values are the corresponding values in this index."""


@op(out=Out(metadata={"key": "user_story_matrix"}))
def build_user_story_matrix(comment_stories: DataFrame) -> IndexedCooMatrix:
    """
    Builds a sparse matrix where the rows are users, the columns are stories, and the values
    are whether the user commented on the story.
    """
    deduplicated = comment_stories[["story_id", "commenter_id"]].drop_duplicates().dropna()

    users = deduplicated["commenter_id"].drop_duplicates()
    user_row_indices = Series(index=users, data=list(range(len(users))))
    stories = deduplicated["story_id"].drop_duplicates()
    story_col_indices = Series(index=stories, data=list(range(len(stories))))

    sparse_rows = user_row_indices[deduplicated["commenter_id"]]
    sparse_cols = story_col_indices[deduplicated["story_id"]]
    sparse_data = np.ones(len(sparse_rows))

    return IndexedCooMatrix(
        matrix=coo_matrix(
            (sparse_data, (sparse_rows, sparse_cols)), shape=(len(users), len(stories))
        ),
        row_index=Series(user_row_indices.index.values, index=user_row_indices),
        col_index=Series(story_col_indices.index.values, index=story_col_indices),
    )
