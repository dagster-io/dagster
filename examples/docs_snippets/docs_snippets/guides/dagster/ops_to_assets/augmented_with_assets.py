from dagster import In, Nothing, job, op


@op(ins={"raw_items": In(Nothing)})
def refresh_items():
    """Loads a table of raw item data and outputs a cleaned, canonical table of items"""


@op(ins={"raw_users": In(Nothing)})
def refresh_users():
    """Loads a table of raw user data and outputs a cleaned, canonical table of users"""


@op
def build_user_item_matrix(users, items):
    """Builds a matrix of users and items that an ML model can score"""


@op(ins={"recommender_model": In(Nothing)})
def refresh_recommendations(user_item_matrix):
    """Loads an ML model and applies it to a user-item matrix to generate recommendations"""


@op
def send_promotional_emails(recommendations):
    """Sends promotional emails based on a set of item recommendations"""


@job(
    output_asset_keys={
        "refresh_recommendations.result": "recommendations",
        "refresh_items.result": "items",
        "refresh_users.result": "users",
    },
    input_asset_keys={
        "refresh_users.raw_users": "raw_users",
        "refresh_items.raw_items": "raw_items",
        "refresh_recommendations.recommender_model": "recommender_model",
    },
)
def refresh_recommendations_and_send_promotions():
    user_item_matrix = build_user_item_matrix(refresh_items(), refresh_users())
    recommendations = refresh_recommendations(user_item_matrix)
    send_promotional_emails(recommendations)
