from dagster import InputDefinition, OutputDefinition, solid
from pandas import DataFrame, Series


@solid(
    input_defs=[
        InputDefinition(
            "stories",
            root_manager_key="warehouse_loader",
            metadata={"table": "hackernews.stories", "columns": ["id"]},
        ),
        InputDefinition(
            "comments",
            root_manager_key="warehouse_loader",
            metadata={
                "table": "hackernews.comments",
                "columns": ["id", "by", "parent"],
            },
        ),
    ],
    output_defs=[
        OutputDefinition(
            io_manager_key="warehouse_io_manager", metadata={"table": "hackernews.comment_stories"}
        )
    ],
)
def build_comment_stories(stories: DataFrame, comments: DataFrame) -> DataFrame:
    """
    Traverses the comment tree to link each comment to its root story.

    Returns a DataFrame with a row per comment and the columns:
    - comment_id (int)
    - story_id (int)
    - commenter_id (str)
    """
    comments.rename(columns={"by": "commenter_id", "id": "comment_id"}, inplace=True)
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
        comment_stories = remaining_comments.merge(stories, left_on="parent", right_index=True)
        comment_stories.rename(columns={"parent": "story_id"}, inplace=True)
        full_comment_stories = full_comment_stories.append(comment_stories)
        remaining_comments = remaining_comments.drop(comment_stories.index)

        # join comments with comments and replace comments with that
        remaining_comments = remaining_comments.merge(
            comments[["parent"]], left_on="parent", right_index=True
        )
        remaining_comments = remaining_comments[["parent_y", "commenter_id"]]
        remaining_comments.rename(columns={"parent_y": "parent"}, inplace=True)

    return full_comment_stories
