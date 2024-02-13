import pandas as pd
from dagster import AssetIn, asset
from pandas import DataFrame, Series


@asset(
    ins={
        "stories": AssetIn(key_prefix=["snowflake", "core"], metadata={"columns": ["id"]}),
        "comments": AssetIn(
            key_prefix=["snowflake", "core"], metadata={"columns": ["id", "user_id", "parent"]}
        ),
    },
    io_manager_key="warehouse_io_manager",
    key_prefix=["snowflake", "recommender"],
)
def comment_stories(stories: DataFrame, comments: DataFrame) -> DataFrame:
    """Comments linked to their root stories.

    Owners: sandy@dagsterlabs.com, owen@dagsterlabs.com
    """
    comments.rename(columns={"user_id": "commenter_id", "id": "comment_id"}, inplace=True)
    comments = comments.set_index("comment_id")[["commenter_id", "parent"]]
    stories = stories.set_index("id")[[]]

    full_comment_stories = DataFrame(
        index=Series(name="comment_id", dtype="int"),
        data={"story_id": Series(dtype="int"), "commenter_id": Series(dtype="object")},
    )
    remaining_comments = comments.copy()

    max_depth = 10
    depth = 0
    while remaining_comments.shape[0] > 0 and depth < max_depth:
        depth += 1
        # join comments with stories and remove all comments that match a story
        comment_stories_at_depth = remaining_comments.merge(
            stories, left_on="parent", right_index=True
        )
        comment_stories_at_depth.rename(columns={"parent": "story_id"}, inplace=True)
        full_comment_stories = pd.concat([full_comment_stories, comment_stories_at_depth])
        remaining_comments = remaining_comments.drop(comment_stories_at_depth.index)

        # join comments with comments and replace comments with that
        remaining_comments = remaining_comments.merge(
            comments[["parent"]], left_on="parent", right_index=True
        )
        remaining_comments = remaining_comments[["parent_y", "commenter_id"]]
        remaining_comments.rename(columns={"parent_y": "parent"}, inplace=True)

    return full_comment_stories
