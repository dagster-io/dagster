import dagster as dg
from dagster_openai import OpenAIResource

from project_ask_ai_dagster.assets.ingestion import docs_scrape, github_discussions, github_issues
from project_ask_ai_dagster.resources.pinecone import PineconeResource


class AskAI(dg.Config):
    question: str
    top_k: int


@dg.asset(deps=[github_discussions, github_issues, docs_scrape], kinds={"Pinecone", "OpenAI"})
def query(
    context: dg.AssetExecutionContext,
    config: AskAI,
    pinecone: PineconeResource,
    openai: OpenAIResource,
) -> dg.MaterializeResult:
    # Get embeddings for the question
    question_embedding = pinecone.embed_texts([config.question])[0]

    results = []
    for namespace in ["dagster-github", "dagster-docs"]:
        index_obj, namespace_kwargs = pinecone.get_index("dagster-knowledge", namespace=namespace)
        search_results = index_obj.query(
            vector=question_embedding, top_k=3, include_metadata=True, **namespace_kwargs
        )
        results.extend(search_results.matches)

    results.sort(key=lambda x: x.score, reverse=True)
    results = results[: config.top_k]

    if not search_results.matches:
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
    for match in search_results.matches:
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

    # Create prompt with context
    prompt_template = """Use the following pieces of context to answer the question at the end.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    Context: {context}
    
    Question: {question}
    
    Answer: Let me help you with that.
    """

    formatted_prompt = prompt_template.format(
        context="\n\n".join(contexts), question=config.question
    )

    # Get response from OpenAI
    with openai.get_client(context) as client:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview", messages=[{"role": "user", "content": formatted_prompt}]
        )

    return dg.MaterializeResult(
        metadata={
            "question": config.question,
            "answer": response.choices[0].message.content,
            "sources": sources,
        }
    )
