import pytest
from pandas import DataFrame

from project_fully_featured.assets.recommender.user_story_matrix import (
    user_story_matrix,
)


@pytest.mark.parametrize(
    "comment_stories, expected",
    [
        ([[2, 1000, "bob"]], [[1]]),
        (
            [[2, 1000, "bob"], [3, 1000, "alice"]],
            [[1], [1]],  # Stories with no comments not currently included in matrix
        ),
        (
            [[2, 1000, "bob"], [3, 1000, "alice"], [4, 2000, "bob"]],
            [
                [1, 1],
                [1, 0],
            ],  # Bob has commented on both 1000 and 2000, alice has only commented on 1000
        ),
    ],
)
def test_user_story_matrix(comment_stories, expected):
    comment_stories_df = DataFrame(
        comment_stories, columns=["comment_id", "story_id", "commenter_id"]
    )
    indexed_matrix = user_story_matrix.op(comment_stories=comment_stories_df).value

    assert indexed_matrix.matrix.toarray().tolist() == expected
