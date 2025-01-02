from typing import Any, Dict


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=30),
    retry=retry_if_exception_type(openai.RateLimitError),
)
def query(self, question: str) -> Dict[str, Any]:
    """Query the RAG system with improved error handling and rate limiting.
    Returns both the answer and the source documents used to generate it.
    """
    if not self.vector_store:
        raise ValueError("Vector store not initialized. Please process documents first.")

    try:
        # Configure the retriever with specific search parameters
        retriever = self.vector_store.as_retriever(
            search_type="mmr",  # Maximum Marginal Relevance for diverse results
            search_kwargs={
                "k": 3,  # Number of documents to return
                "fetch_k": 5,  # Number of documents to fetch before filtering
            },
        )

        prompt_template = """Use the following pieces of context to answer the question at the end.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        
        Context: {context}
        
        Question: {question}
        
        Answer: Let me help you with that.
        """

        PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True,
        )

        response = qa_chain.invoke(question)

        # Extract sources with metadata
        sources = []
        for doc in response["source_documents"]:
            source = {
                "type": doc.metadata["source"],
                "title": doc.metadata["title"],
                "url": doc.metadata["url"],
                "created_at": doc.metadata["created_at"],
            }
            sources.append(source)

        return {"answer": response["result"], "sources": sources}

    except openai.RateLimitError:
        print("Rate limit hit during query, retrying...")
        raise
    except Exception as e:
        print(f"Error during query: {e}")
        return {"answer": "Sorry, I encountered an error processing your question.", "sources": []}
