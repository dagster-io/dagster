from langchain_openai import OpenAIEmbeddings, ChatOpenAI
import openai
from typing import List, Optional, Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import random
import time
from tqdm import tqdm

class RateLimitedOpenAIEmbeddings(OpenAIEmbeddings):
    """
    OpenAI embeddings class with advanced rate limit handling and adaptive batching.
    Inherits from OpenAIEmbeddings and adds rate limiting functionality.
    """
    
    def __init__(self, *args, **kwargs):
        # First call the parent class's initialization
        super().__init__(*args, **kwargs)
        
        # Initialize our rate limiting parameters as instance attributes
        # Start with a conservative batch size to avoid hitting rate limits immediately
        self._initial_batch_size = 4
        self._max_batch_size = 50
        self._current_batch_size = self._initial_batch_size
        self._success_count = 0
        self._required_successes = 3

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type(openai.RateLimitError),
        before_sleep=lambda retry_state: print(f"Rate limited, waiting {retry_state.next_action.sleep} seconds...")
    )
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed documents with retry logic and adaptive batch size adjustment.
        Automatically reduces batch size on rate limits and increases it after consistent successes.
        """
        try:
            # Attempt to embed the current batch
            result = super().embed_documents(texts)
            # If successful, increment our success counter
            self._success_count += 1
            
            # Consider increasing batch size after several successful attempts
            if self._success_count >= self._required_successes:
                self._success_count = 0  # Reset success counter
                if self._current_batch_size < self._max_batch_size:
                    self._current_batch_size = min(
                        self._current_batch_size + 5,  # Gradually increase batch size
                        self._max_batch_size
                    )
            return result
            
        except openai.RateLimitError:
            # On rate limit, reduce batch size and reset success counter
            self._current_batch_size = max(1, self._current_batch_size // 2)
            self._success_count = 0
            raise
        except Exception as e:
            # On any other error, reset success counter but maintain batch size
            self._success_count = 0
            raise e

    def batch_embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Process documents in dynamically-sized batches with progress tracking.
        Implements adaptive delays between batches to avoid rate limits.
        """
        embeddings = []
        total_processed = 0
        
        with tqdm(total=len(texts), desc="Generating embeddings") as pbar:
            while total_processed < len(texts):
                # Calculate the end index for the current batch
                end_idx = total_processed + self._current_batch_size
                # Get the current batch of texts
                batch = texts[total_processed:end_idx]
                
                for attempt in range(3):  # Allow retries for each batch
                    try:
                        # Attempt to embed the current batch
                        batch_embeddings = self.embed_documents(batch)
                        embeddings.extend(batch_embeddings)
                        total_processed += len(batch)
                        pbar.update(len(batch))
                        
                        # Add adaptive delay between batches
                        delay = random.uniform(0.5, 1.0)
                        time.sleep(delay)
                        break  # Exit retry loop on success
                    
                    except openai.RateLimitError:
                        print(f"Rate limit hit for batch. Retrying in 5 seconds... (Attempt {attempt + 1})")
                        time.sleep(5)  # Add longer delay for rate limits
                        if attempt == 2:  # If retries are exhausted
                            print(f"Failed to process batch after 3 attempts: {batch}")
                            raise
                    except Exception as e:
                        print(f"Unexpected error during batch processing: {str(e)}")
                        time.sleep(5)
                        break  # Exit the loop on other errors
        return embeddings
