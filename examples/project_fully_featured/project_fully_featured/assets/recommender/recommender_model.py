import random

from dagster import AssetIn, MetadataValue, Output, asset
from pandas import DataFrame, Series
from sklearn.decomposition import TruncatedSVD

from .user_story_matrix import IndexedCooMatrix


@asset(key_prefix=["s3", "recommender"])
def recommender_model(user_story_matrix: IndexedCooMatrix) -> Output[TruncatedSVD]:
    """An SVD model for collaborative filtering-based recommendation."""
    n_components = min(random.randint(90, 110), len(user_story_matrix.col_index) - 1)
    svd = TruncatedSVD(n_components=n_components)
    svd.fit(user_story_matrix.matrix)

    total_explained_variance = svd.explained_variance_ratio_.sum()

    return Output(
        svd,
        metadata={
            "Total explained variance ratio": total_explained_variance,
            "Number of components": n_components,
        },
    )


@asset(
    ins={
        "stories": AssetIn(key_prefix=["snowflake", "core"], metadata={"columns": ["id", "title"]})
    },
    io_manager_key="warehouse_io_manager",
    key_prefix=["snowflake", "recommender"],
)
def component_top_stories(
    recommender_model: TruncatedSVD, user_story_matrix: IndexedCooMatrix, stories: DataFrame
) -> Output[DataFrame]:
    """For each component in the collaborative filtering model, the titles of the top stories
    it's associated with.
    """
    n_stories = 10

    components_column = []
    titles_column = []

    story_titles = stories.set_index("id")

    for i in range(recommender_model.components_.shape[0]):
        component = recommender_model.components_[i]
        top_story_indices = component.argsort()[-n_stories:][::-1]
        top_story_ids = user_story_matrix.col_index[top_story_indices]
        top_story_titles = story_titles.loc[top_story_ids]

        for title in top_story_titles["title"]:
            components_column.append(i)
            titles_column.append(title)

    component_top_stories = DataFrame(
        {"component_index": Series(components_column), "title": Series(titles_column)}
    )

    return Output(
        component_top_stories,
        metadata={
            "Top component top stories": MetadataValue.md(
                top_components_to_markdown(component_top_stories)
            ),
        },
    )


def top_components_to_markdown(component_top_stories: DataFrame) -> str:
    component_markdowns = []
    for i in range(5):
        component_i_top_5_stories = component_top_stories[
            component_top_stories["component_index"] == i
        ].head(5)

        component_markdowns.append(
            "\n".join(
                [f"Component {i}"]
                + ["- " + str(row["title"]) for _, row in component_i_top_5_stories.iterrows()]
            )
        )

    return "\n\n".join(component_markdowns)
