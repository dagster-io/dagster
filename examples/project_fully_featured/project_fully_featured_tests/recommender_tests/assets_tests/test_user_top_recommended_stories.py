import numpy as np
from pandas import DataFrame, Series
from scipy.sparse import coo_matrix
from sklearn.decomposition import TruncatedSVD

from project_fully_featured.assets.recommender.user_story_matrix import (
    IndexedCooMatrix,
)
from project_fully_featured.assets.recommender.user_top_recommended_stories import (
    user_top_recommended_stories,
)


def test_user_top_recommended_stories():
    model = TruncatedSVD()
    model.components_ = np.array([[1.0, 0.0, 1.0]])
    user_story_matrix = coo_matrix(np.array([[1.0, 0.0, 0.0]]))
    row_users = Series(["abc"])
    col_stories = Series([35, 38, 40])

    result = user_top_recommended_stories(
        None,
        recommender_model=model,
        user_story_matrix=IndexedCooMatrix(user_story_matrix, row_users, col_stories),
    )

    expected = DataFrame(
        [
            {"user_id": "abc", "story_id": 40, "relevance": 1.0},
            {"user_id": "abc", "story_id": 35, "relevance": 1.0},
        ]
    )

    assert result.equals(expected), str(result)
