from typing import Any

import dagster as dg
import gql
from gql.transport.requests import RequestsHTTPTransport
from langchain_core.documents import Document

from project_ask_ai_dagster.resources.github_gql_queries import (
    GITHUB_DISCUSSIONS_QUERY,
    GITHUB_ISSUES_QUERY,
)


class GithubResource(dg.ConfigurableResource):
    """Resource for fetching Github issues and discussions."""

    github_token: str

    def client(self):
        return gql.Client(
            schema=None,
            transport=RequestsHTTPTransport(
                url="https://api.github.com/graphql",
                headers={
                    "Authorization": f"Bearer {self.github_token}",
                    "Accept": "application/vnd.github.v4.idl",
                },
                retries=3,
            ),
            fetch_schema_from_transport=True,
        )

    def get_issues(self, start_date="2023-01-01", end_date="2023-12-31") -> list[dict]:
        issues_query_str = GITHUB_ISSUES_QUERY.replace("START_DATE", start_date).replace(
            "END_DATE", end_date
        )
        return self._fetch_results(issues_query_str, "issues")

    def get_discussions(self, start_date="2023-01-01", end_date="2023-12-31") -> list[dict]:
        discussion_query_str = GITHUB_DISCUSSIONS_QUERY.replace("START_DATE", start_date).replace(
            "END_DATE", end_date
        )
        return self._fetch_results(discussion_query_str, "discussions")

    def _fetch_results(self, query_str: str, object_type: str) -> list[dict]:
        log = dg.get_dagster_logger()
        client = self.client()
        cursor = None
        results = []
        while True:
            log.info(f"Fetching results from Github: {object_type} with cursor: {cursor}")
            query = gql.gql(
                query_str.replace("CURSOR_PLACEHOLDER", f'"{cursor}"' if cursor else "null"),
            )
            result = client.execute(query)
            search = result["search"]
            edges = search["edges"]
            for node in edges:
                results.append(node["node"])
            log.info(f"Total results: {len(results)}")
            if not search["pageInfo"]["hasNextPage"]:
                break
            cursor = search["pageInfo"]["endCursor"]
        return results

    def convert_discussions_to_documents(self, items: list[dict[str, Any]]) -> list[Document]:
        """Convert GitHub discussions to LangChain documents.

        This function transforms GitHub discussion data into LangChain Document objects,
        preserving the hierarchical structure of discussions including answers and comments.
        It's specifically designed to handle the Q&A format and category information
        that's unique to GitHub discussions.

        Args:
            items: List of GitHub discussion items as dictionaries

        Returns:
            List of LangChain Document objects formatted for vector storage
        """
        log = dg.get_dagster_logger()
        log.info(f"Starting conversion of {len(items)} discussions to documents")
        documents = []
        for item in items:
            try:
                # Create comprehensive metadata including discussion-specific fields
                metadata = {
                    "source": "github_discussion",
                    "id": item.get("id"),
                    "url": item.get("url"),
                    "created_at": item.get("createdAt"),
                    "title": item.get("title"),
                    "number": item.get("number"),
                    "category": item.get("category", {}).get("name"),
                    "is_answered": item.get("isAnswered", False),
                    "upvote_count": item.get("upvoteCount", 0),
                }

                # Build content parts with structured sections
                content_parts = [
                    f"Title: {item.get('title', '')}",
                    f"Category: {item.get('category', {}).get('name', 'Uncategorized')}",
                    f"Question: {item.get('bodyText', '')}",
                ]

                # Add the accepted answer if present
                if item.get("answer"):
                    content_parts.append(f"Accepted Answer: {item['answer'].get('bodyText', '')}")

                # Add any additional comments
                if "comments" in item and "nodes" in item["comments"]:
                    for comment in item["comments"]["nodes"]:
                        if comment and "bodyText" in comment:
                            # Skip if this comment is the same as the accepted answer
                            if not item.get("answer") or comment["bodyText"] != item["answer"].get(
                                "bodyText"
                            ):
                                content_parts.append(f"Comment: {comment['bodyText']}")

                # Add labels if present
                if "labels" in item and "nodes" in item["labels"]:
                    labels = [label["name"] for label in item["labels"]["nodes"]]
                    if labels:
                        content_parts.append(f"Labels: {', '.join(labels)}")

                # Create document with properly formatted content
                doc = Document(page_content="\n\n".join(content_parts), metadata=metadata)
                documents.append(doc)

                # Debug information for verification
                log.info(
                    f"Processed discussion #{item.get('number')}: "
                    f"{item.get('title')} ({metadata['category']})"
                )

            except Exception as e:
                log.error(f"Error processing discussion #{item.get('number', 'unknown')}:")
                log.error(f"Error details: {e!s}")
                continue

        log.info(f"Successfully converted {len(documents)} discussions")
        return documents

    def convert_issues_to_documents(self, items: list[dict[str, Any]]) -> list[Document]:
        """Convert GitHub issues to LangChain documents.

        This function transforms GitHub issue data into LangChain Document objects,
        preserving issue-specific metadata and content structure including labels,
        state information, and comments.

        Args:
            items: List of GitHub issue items as dictionaries

        Returns:
            List of LangChain Document objects formatted for vector storage
        """
        documents = []
        log = dg.get_dagster_logger()
        log.info(f"Starting conversion of {len(items)} issues to documents")

        for item in items:
            try:
                # Extract issue-specific metadata
                metadata = {
                    "source": "github_issue",
                    "id": item.get("id"),
                    "url": item.get("url"),
                    "created_at": item.get("createdAt"),
                    "title": item.get("title"),
                    "number": item.get("number"),
                    "state": item.get("state"),
                    "closed_at": item.get("closedAt"),
                    "state_reason": item.get("stateReason"),
                    "reaction_count": item.get("reactions", {}).get("totalCount", 0),
                }

                # Build content parts with issue structure
                content_parts = [
                    f"Title: {item.get('title', '')}",
                    f"State: {item.get('state', '')}",
                    f"Description: {item.get('bodyText', '')}",
                ]

                # Add labels if present
                if "labels" in item and "nodes" in item["labels"]:
                    labels = [label["name"] for label in item["labels"]["nodes"]]
                    if labels:
                        content_parts.append(f"Labels: {', '.join(labels)}")

                # Add comments if present
                if "comments" in item and "nodes" in item["comments"]:
                    for comment in item["comments"]["nodes"]:
                        if comment and "body" in comment:
                            content_parts.append(f"Comment: {comment['body']}")

                # Create document with properly formatted content
                doc = Document(page_content="\n\n".join(content_parts), metadata=metadata)
                documents.append(doc)

                # Debug information for verification
                log.info(
                    f"Processed issue #{item.get('number')}: {item.get('title')} ({metadata['state']})"
                )

            except Exception as e:
                log.error(f"Error processing issue #{item.get('number', 'unknown')}:")
                log.error(f"Error details: {e!s}")
                continue

        log.info(f"Successfully converted {len(documents)} issues")
        return documents


github_resource = GithubResource(github_token=dg.EnvVar("GITHUB_TOKEN"))
