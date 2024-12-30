import os
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

from langchain.schema import Document
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import openai

from ingestion.github import GithubResource
from ingestion.openai import RateLimitedOpenAIEmbeddings
from ingestion.webscrape import SitemapScraper
# Load environment variables
load_dotenv()


class RAGApplication:
    def __init__(self, github_resource, site_scraper):
        """
        Initialize RAG application with improved embedding handling.
        """
        self.github = github_resource
        self.scraper = site_scraper
        # Validate OpenAI API key
        self.openai_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        # Initialize OpenAI components with rate limiting
        self.embeddings = RateLimitedOpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=self.openai_key
        )
        
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7
        )
        
        # Initialize text splitter with conservative settings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.vector_store = None

    def fetch_github_data(self, 
                         start_date: str = None, 
                         end_date: str = None) -> List[Document]:
        """Fetch GitHub data within date range."""
        if not start_date or not end_date:
            current_year = datetime.now().year
            start_date = f"{current_year}-01-01"
            end_date = f"{current_year}-01-31"
        issues = self.github.get_issues(start_date=start_date, end_date=end_date)
        discussions = self.github.get_discussions(start_date=start_date, end_date=end_date)

        issue_docs = self.github._convert_issues_to_documents(issues)
        discussion_docs = self.github._convert_discussions_to_documents(discussions)
        return issue_docs + discussion_docs

    def scrape_docs_site(self, limit: int = 5) -> List[Document]:
        documents = self.scraper.get_documents(limit=5)
    
        print(f"Scraped {len(documents)} documents")
        return documents
    
    def process_documents(self, documents: List[Document], persist_directory: str = None):
        """
        Process documents using Chroma integration with rate-limited embeddings.
        This method handles document splitting, rate-limited embedding generation, and vector storage.
        """
        print(f"Processing {len(documents)} documents...")
        if not documents or not all(isinstance(doc, Document) for doc in documents):
            raise ValueError("Invalid documents: Ensure all items are of type `Document`")
        
        # Split documents into smaller chunks
        splits = self.text_splitter.split_documents(documents)
        print(f"Created {len(splits)} splits")
        
        # Initialize vector store
        self.vector_store = Chroma(
            collection_name="github_knowledge",
            embedding_function=self.embeddings,  
            persist_directory=persist_directory or "./chroma_db"
        )
        
        try:
            # Get text content for all documents
            texts = [doc.page_content for doc in splits]
            
            # Use the rate-limited batch embedding method
            print("Starting batch embedding process...")
            embeddings = self.embeddings.batch_embed_documents(texts)
            
            # Add all documents and their embeddings to the vector store
            print("Adding documents to vector store...")
            self.vector_store.add_documents(
                documents=splits,
                embeddings=embeddings
            )
            
            print("Processing completed successfully")
            
        except Exception as e:
            print(f"Error during document processing: {str(e)}")
            print("Attempting to process in smaller batches...")
            
            # Fallback to processing in smaller batches
            chunk_size = 25  # Smaller chunk size for recovery
            for i in range(0, len(splits), chunk_size):
                try:
                    chunk = splits[i:i + chunk_size]
                    texts = [doc.page_content for doc in chunk]
                    
                    # Use batch_embed_documents which handles rate limiting internally
                    embeddings = self.embeddings.batch_embed_documents(texts)
                    
                    self.vector_store.add_documents(
                        documents=chunk,
                        embeddings=embeddings
                    )
                    
                    print(f"Successfully processed chunk {i//chunk_size + 1}/{(len(splits)-1)//chunk_size + 1}")
                    time.sleep(1.0)  # Small delay between chunks
                    
                except Exception as chunk_error:
                    print(f"Error processing chunk {i//chunk_size + 1}: {str(chunk_error)}")
                    time.sleep(5)  # Longer delay after errors
                    continue
            
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        retry=retry_if_exception_type(openai.RateLimitError)
    )
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the RAG system with improved error handling and rate limiting.
        Returns both the answer and the source documents used to generate it.
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Please process documents first.")
            
        try:
            # Configure the retriever with specific search parameters
            retriever = self.vector_store.as_retriever(
                search_type="mmr",  # Maximum Marginal Relevance for diverse results
                search_kwargs={
                    "k": 3,        # Number of documents to return
                    "fetch_k": 5   # Number of documents to fetch before filtering
                }
            )
            
            prompt_template = """Use the following pieces of context to answer the question at the end.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            
            Context: {context}
            
            Question: {question}
            
            Answer: Let me help you with that.
            """
            
            PROMPT = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                chain_type_kwargs={"prompt": PROMPT},
                return_source_documents=True
            )
            
            response = qa_chain.invoke(question)
            
            # Extract sources with metadata
            sources = []
            for doc in response['source_documents']:
                source = {
                    'type': doc.metadata['source'],
                    'title': doc.metadata['title'],
                    'url': doc.metadata['url'],
                    'created_at': doc.metadata['created_at']
                }
                sources.append(source)
            
            return {
                'answer': response['result'],
                'sources': sources
            }
            
        except openai.RateLimitError:
            print("Rate limit hit during query, retrying...")
            raise
        except Exception as e:
            print(f"Error during query: {e}")
            return {
                'answer': "Sorry, I encountered an error processing your question.",
                'sources': []
            }

def main():
    # Initialize GitHub resource and the webscraper
    github = GithubResource(github_token=os.getenv('GITHUB_TOKEN'))
    
    sitemap_url = os.getenv('GITHUB_TOKEN')
    scraper = SitemapScraper(sitemap_url)
    # Initialize RAG
    rag = RAGApplication(github, scraper)
    
    try:
        #Fetch and process data
        github_documents = rag.fetch_github_data(
            start_date="2024-01-01",
            end_date="2024-01-04"
        )
        
        rag.process_documents(
            github_documents,
            persist_directory="./github_knowledge_base",
        )
        
        doc_site_documents = rag.scrape_docs_site(limit=5)
        
        rag.process_documents(
            doc_site_documents,
            persist_directory="./github_knowledge_base",
        )
        
        # Example queries

        questions = [
            "What are the most common issues reported?",
            "What features are users requesting most often?",
            "What are the recent bug reports about?"
        ]
        
        for question in questions:
            print(f"\nQ: {question}")
            try:
                response = rag.query(question)
                print(f"A: {response['answer']}")
                print("\nSources:")
                for source in response['sources']:
                    print(f"- {source['title']} ({source['type']}) - {source['url']}")
            except Exception as e:
                print(f"Error processing question: {e}")
            print("\n" + "="*50)
            
    except Exception as e:
        print(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()