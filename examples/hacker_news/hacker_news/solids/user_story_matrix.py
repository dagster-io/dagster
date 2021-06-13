import numpy as np
from dagster import Output, OutputDefinition, solid
from pandas import DataFrame, Series
from scipy.sparse import coo_matrix


@solid(
    output_defs=[
        OutputDefinition(
            Series,
            name="row_users",
            description="A series whose index corresponds to the row indices in the user story "
            "matrix and whose values are the corresponding user IDs.",
            metadata={"key": "row_users"},
        ),
        OutputDefinition(
            Series,
            name="col_stories",
            description="A series whose index corresponds to the column indices in the user story "
            "matrix and whose values are the corresponding story IDs.",
            metadata={"key": "col_stories"},
        ),
        OutputDefinition(
            coo_matrix, name="user_story_matrix", metadata={"key": "user_story_matrix"}
        ),
    ]
)
def build_user_story_matrix(comment_stories: DataFrame):
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

    yield Output(
        Series(user_row_indices.index.values, index=user_row_indices),
        output_name="row_users",
    )
    yield Output(
        Series(story_col_indices.index.values, index=story_col_indices),
        output_name="col_stories",
    )
    yield Output(
        coo_matrix((sparse_data, (sparse_rows, sparse_cols)), shape=(len(users), len(stories))),
        output_name="user_story_matrix",
    )
