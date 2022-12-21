import numpy as np
from dagster import asset
from pandas import DataFrame
from scipy.sparse import coo_matrix, csc_matrix, csr_matrix
from sklearn.decomposition import TruncatedSVD

from .user_story_matrix import IndexedCooMatrix


@asset(io_manager_key="warehouse_io_manager", key_prefix=["snowflake", "recommender"])
def user_top_recommended_stories(
    context, recommender_model: TruncatedSVD, user_story_matrix: IndexedCooMatrix
) -> DataFrame:
    """The top stories for each commenter (user)."""
    # Compute XV, which has a row for each user and a column for each component
    XV = recommender_model.transform(user_story_matrix.matrix)

    # Now we want to project XV back into story-space.  As a dense matrix, the product would be way
    # too big - | # users * # stories|, so we sparsify both the multiplicands to make it more
    # manageable.
    XV[np.abs(XV) < 1] = 0
    sparse_XV = csr_matrix(XV)
    context.log.info(f"sparse_XV shape: {sparse_XV.shape}")
    context.log.info(f"sparse_XV non-zero: {sparse_XV.count_nonzero()}")

    recommender_model.components_[np.abs(recommender_model.components_) < 1e-2] = 0
    sparse_components = csc_matrix(recommender_model.components_)
    context.log.info(f"recommender_model.components_ shape: {recommender_model.components_.shape}")
    context.log.info(f"sparse_components non-zero: {sparse_components.count_nonzero()}")

    # A matrix with the same dimensions as user_story_matrix, but reduced in rank
    X_hat = sparse_XV @ sparse_components

    coo = coo_matrix(X_hat)
    story_ids = user_story_matrix.col_index[coo.col].values
    user_ids = user_story_matrix.row_index[coo.row].values
    context.log.info(f"recommendations: {len(story_ids)}")

    return DataFrame.from_dict({"user_id": user_ids, "story_id": story_ids, "relevance": coo.data})
