GITHUB_ISSUES_QUERY = """
query {
  search(
    query: "repo:dagster-io/dagster updated:START_DATE..END_DATE is:issue"
    type: ISSUE
    first: 100
    after: CURSOR_PLACEHOLDER
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    issueCount
    edges {
      node {
        ... on Issue {
          id
          number
          title
          bodyText
          createdAt
          closedAt
          state
          stateReason
          url
          comments(last: 10) {
            totalCount
            nodes {
              id
              bodyText
            }
          }
          labels(first: 10) {
            nodes {
              name
            }
          }
          reactions(content: THUMBS_UP) {
            totalCount
          }
        }
      }
    }
  }
}
"""

GITHUB_DISCUSSIONS_QUERY = """
query {
  search(
    query: "repo:dagster-io/dagster updated:START_DATE..END_DATE is:discussion"
    type: DISCUSSION
    first: 100
    after: CURSOR_PLACEHOLDER
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    discussionCount
    edges {
      node {
        ... on Discussion {
          id
          number
          title
          bodyText
          createdAt
          closed
          closedAt
          stateReason
          url
          isAnswered
          upvoteCount
          category { 
            name
            slug
          }
          answer {
            bodyText
          }
          comments(last: 10) {
            totalCount
            nodes {
              id
              bodyText
            }
          }
          labels(first: 10) {
            nodes {
              name
            }
          }
          reactions(content: THUMBS_UP) {
            totalCount
          }
        }
      }
    }
  }
}"""
