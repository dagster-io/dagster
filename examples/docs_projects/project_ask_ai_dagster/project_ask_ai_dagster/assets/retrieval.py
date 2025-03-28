import dagster as dg
from dagster_openai import OpenAIResource

from project_ask_ai_dagster.assets.ingestion import (
    docs_embedding,
    github_discussions_embeddings,
    github_issues_embeddings,
)
from project_ask_ai_dagster.resources.pinecone import PineconeResource


# start_config
class AskAI(dg.Config):
    question: str


# end_config


@dg.asset(
    deps=[github_issues_embeddings, github_discussions_embeddings, docs_embedding],
    kinds={"pinecone", "openai"},
    group_name="retrieval",
    description="""A Retrieval-Augmented Generation (RAG) asset that answers Dagster-related questions using embedded documentation and GitHub content.

    Takes a user question, converts it to an embedding vector, searches across Pinecone indexes of Dagster docs and GitHub content, and uses GPT-4 to generate an answer based on the retrieved context. Returns the answer along with source metadata.

    Args:
    context: Dagster execution context
    config: Contains the user's question
    pinecone: Client for vector similarity search
    openai: Client for embeddings and LLM completion

    Returns:
    MaterializeResult containing:
        - The original question
        - AI-generated answer
        - Source contexts used (with URLs and relevance scores)
    """,
)
def query(
    context: dg.AssetExecutionContext,
    config: AskAI,
    pinecone: PineconeResource,
    openai: OpenAIResource,
) -> dg.MaterializeResult:
    # start_query
    with openai.get_client(context) as client:
        question_embedding = (
            client.embeddings.create(model="text-embedding-3-small", input=config.question)
            .data[0]
            .embedding
        )

    results = []
    for namespace in ["dagster-github", "dagster-docs"]:
        index_obj, namespace_kwargs = pinecone.get_index("dagster-knowledge", namespace=namespace)
        search_results = index_obj.query(
            vector=question_embedding, top_k=3, include_metadata=True, **namespace_kwargs
        )
        results.extend(search_results.matches)

    results.sort(key=lambda x: x.score, reverse=True)
    results = results[:3]
    # end_query

    if not search_results.matches:  # pyright: ignore[reportPossiblyUnboundVariable]
        return dg.MaterializeResult(
            metadata={
                "question": config.question,
                "answer": "No relevant information found.",
                "sources": [],
            }
        )

    # Format context from search results
    contexts = []
    sources = []
    for match in search_results.matches:  # pyright: ignore[reportPossiblyUnboundVariable]
        contexts.append(match.metadata.get("text", ""))
        sources.append(
            {
                "type": match.metadata.get("source", "unknown"),
                "title": match.metadata.get("title", "unknown"),
                "url": match.metadata.get("url", "unknown"),
                "created_at": match.metadata.get("created_at", "unknown"),
                "score": match.score,
            }
        )

    # start_prompt
    # Create prompt with context
    prompt_template = """
    You are a experienced data engineer and Dagster expert.  

    Use the following pieces of context to answer the question at the end.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    Context: {full_context}
    
    Question: {question}
    
    Answer: Let me help you with that.
    """

    formatted_prompt = prompt_template.format(
        full_context="\n\n".join(contexts), question=config.question
    )

    # Get response from OpenAI
    with openai.get_client(context) as client:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview", messages=[{"role": "user", "content": formatted_prompt}]
        )
    # end_prompt

    return dg.MaterializeResult(
        metadata={
            "question": config.question,
            "answer": response.choices[0].message.content,
            "sources": sources,
        }
    )
