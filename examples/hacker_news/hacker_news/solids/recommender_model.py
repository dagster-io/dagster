import random

from dagster import EventMetadata, InputDefinition, Output, OutputDefinition, solid
from dagster.utils import file_relative_path
from dagstermill import define_dagstermill_solid
from hacker_news.solids.user_story_matrix import IndexedCooMatrix
from pandas import DataFrame, Series
from sklearn.decomposition import TruncatedSVD


@solid(
    output_defs=[OutputDefinition(dagster_type=TruncatedSVD, metadata={"key": "recommender_model"})]
)
def build_recommender_model(user_story_matrix: IndexedCooMatrix):
    """
    Trains an SVD model for collaborative filtering-based recommendation.
    """
    n_components = random.randint(90, 110)
    svd = TruncatedSVD(n_components=n_components)
    svd.fit(user_story_matrix.matrix)

    total_explained_variance = svd.explained_variance_ratio_.sum()

    yield Output(
        svd,
        metadata={
            "Total explained variance ratio": total_explained_variance,
            "Number of components": n_components,
        },
    )


model_perf_notebook = define_dagstermill_solid(
    "recommender_model_perf",
    notebook_path=file_relative_path(__file__, "../notebooks/recommender_model_perf.ipynb"),
    input_defs=[InputDefinition(dagster_type=TruncatedSVD, name="recommender_model")],
    output_notebook="perf_notebook",
)


@solid(
    input_defs=[
        InputDefinition(
            "story_titles",
            root_manager_key="warehouse_loader",
            metadata={
                "table": "hackernews.stories",
                "columns": ["id", "title"],
            },
        ),
    ],
    output_defs=[
        OutputDefinition(
            dagster_type=DataFrame,
            io_manager_key="warehouse_io_manager",
            metadata={"table": "hackernews.component_top_stories"},
        )
    ],
)
def build_component_top_stories(
    model: TruncatedSVD, user_story_matrix: IndexedCooMatrix, story_titles: DataFrame
):
    """
    For each component in the collaborative filtering model, finds the titles of the top stories
    it's associated with.
    """
    n_stories = 10

    components_column = []
    titles_column = []

    story_titles = story_titles.set_index("id")

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

    yield Output(
        component_top_stories,
        metadata={
            "Top component top stories": EventMetadata.md(
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
                + ["- " + row["title"] for _, row in component_i_top_5_stories.iterrows()]
            )
        )

    return "\n\n".join(component_markdowns)
