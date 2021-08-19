import random
from hacker_news.solids.user_story_matrix import IndexedCooMatrix
from hacker_news.resources.hn_resource import HNAPIClient
from pandas import DataFrame, Series
from sklearn.decomposition import TruncatedSVD
import numpy as np
from scipy.sparse import coo_matrix


if __name__ == "__main__":
    #
    # Fetch items from Hacker News API
    #
    start_id, end_id = 0, 1000000
    hn_client = HNAPIClient()

    rows = []
    for item_id in range(start_id, end_id):
        rows.append(hn_client.fetch_item_by_id(item_id))

    non_none_rows = [row for row in rows if row is not None]

    items = DataFrame(non_none_rows).drop_duplicates(subset=["id"])

    #
    # Build dataset of comments
    #
    comments = items.where(items["type"] == "comment")

    #
    # Build dataset of stories
    #
    stories = items.where(items["type"] == "story")

    #
    # Traverse the comment tree to link each comment to its root story.
    #
    comments.rename(columns={"by": "commenter_id", "id": "comment_id"}, inplace=True)
    comments = comments.set_index("comment_id")[["commenter_id", "parent"]]
    stories = stories.set_index("id")[[]]

    comment_stories = DataFrame(
        index=Series(name="comment_id", dtype="int"),
        data={"story_id": Series(dtype="int"), "commenter_id": Series(dtype="object")},
    )
    remaining_comments = comments.copy()

    max_depth = 10
    depth = 0
    while remaining_comments.shape[0] > 0 and depth < max_depth:
        depth += 1
        # join comments with stories and remove all comments that match a story
        cur_comment_stories = remaining_comments.merge(stories, left_on="parent", right_index=True)
        cur_comment_stories.rename(columns={"parent": "story_id"}, inplace=True)
        comment_stories = comment_stories.append(cur_comment_stories)
        remaining_comments = remaining_comments.drop(cur_comment_stories.index)

        # join comments with comments and replace comments with that
        remaining_comments = remaining_comments.merge(
            comments[["parent"]], left_on="parent", right_index=True
        )
        remaining_comments = remaining_comments[["parent_y", "commenter_id"]]
        remaining_comments.rename(columns={"parent_y": "parent"}, inplace=True)

    #
    # Build a sparse matrix where the rows are users, the columns are stories, and the values
    # are whether the user commented on the story.
    #
    deduplicated = comment_stories[["story_id", "commenter_id"]].drop_duplicates().dropna()

    users = deduplicated["commenter_id"].drop_duplicates()
    user_row_indices = Series(index=users, data=list(range(len(users))))
    stories = deduplicated["story_id"].drop_duplicates()
    story_col_indices = Series(index=stories, data=list(range(len(stories))))

    sparse_rows = user_row_indices[deduplicated["commenter_id"]]
    sparse_cols = story_col_indices[deduplicated["story_id"]]
    sparse_data = np.ones(len(sparse_rows))

    user_story_matrix = IndexedCooMatrix(
        matrix=coo_matrix(
            (sparse_data, (sparse_rows, sparse_cols)), shape=(len(users), len(stories))
        ),
        row_index=Series(user_row_indices.index.values, index=user_row_indices),
        col_index=Series(story_col_indices.index.values, index=story_col_indices),
    )

    #
    # Train an SVD model for collaborative filtering-based recommendation.
    #
    n_components = random.randint(90, 110)
    model = TruncatedSVD(n_components=n_components)
    model.fit(user_story_matrix.matrix)

    #
    # For each component in the collaborative filtering model, find the titles of the top stories
    # it's associated with.
    #
    n_stories = 10

    components_column = []
    titles_column = []

    story_titles = stories.set_index("id")

    for i in range(model.components_.shape[0]):
        component = model.components_[i]
        top_story_indices = component.argsort()[-n_stories:][::-1]
        top_story_ids = user_story_matrix.col_index[top_story_indices]
        top_story_titles = story_titles.loc[top_story_ids]

        for title in top_story_titles["title"]:
            components_column.append(i)
            titles_column.append(title)

    component_top_stories = DataFrame(
        {"component_index": Series(components_column), "title": Series(titles_column)}
    )
