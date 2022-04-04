from dagster import job, op


@op
def refresh_items():
    """Loads a table of raw item data and outputs a cleaned, canonical table of items"""


@op
def refresh_users():
    """Loads a table of raw user data and outputs a cleaned, canonical table of users"""


@op
def build_user_item_matrix(users, items):
    """Builds a matrix of users and items that an ML model can score"""


@op
def refresh_recommendations(user_item_matrix):
    """Loads an ML model and applies it to a user-item matrix to generate recommendations"""


@op
def send_promotional_emails(recommendations):
    """Sends promotional emails based on a set of item recommendations"""


@job
def refresh_recommendations_and_send_promotions():
    user_item_matrix = build_user_item_matrix(refresh_items(), refresh_users())
    recommendations = refresh_recommendations(user_item_matrix)
    send_promotional_emails(recommendations)
