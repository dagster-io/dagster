"""Utility for summarizing text using OpenAI.

This code was "borrowed" from the OpenAI cookbook:

    https://cookbook.openai.com/examples/summarizing_long_documents

For an alternate approach using langchain, see the Dagster essentials capstone project for
summarizing movie subtitles:

    https://github.com/cmpadden/dagster-essentials-capstone/blob/main/dagster_essentials_capstone/assets/metrics.py

"""

import logging
from typing import Optional

import tiktoken
from openai import Client


def get_chat_completion(client, messages, model="gpt-4-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message.content


def tokenize(text: str) -> list[str]:
    encoding = tiktoken.encoding_for_model("gpt-4-turbo")
    return encoding.encode(text)  # type: ignore


def chunk_on_delimiter(input_string: str, max_tokens: int, delimiter: str) -> list[str]:
    chunks = input_string.split(delimiter)
    combined_chunks, _, dropped_chunk_count = combine_chunks_with_no_minimum(
        chunks, max_tokens, chunk_delimiter=delimiter, add_ellipsis_for_overflow=True
    )
    if dropped_chunk_count > 0:
        logging.info(f"warning: {dropped_chunk_count} chunks were dropped due to overflow")
    combined_chunks = [f"{chunk}{delimiter}" for chunk in combined_chunks]
    return combined_chunks


def combine_chunks_with_no_minimum(
    chunks: list[str],
    max_tokens: int,
    chunk_delimiter="\n\n",
    header: Optional[str] = None,
    add_ellipsis_for_overflow=False,
) -> tuple[list[str], list[int], int]:
    dropped_chunk_count = 0
    output = []
    output_indices = []
    candidate = [] if header is None else [header]
    candidate_indices = []
    for chunk_i, chunk in enumerate(chunks):
        chunk_with_header = [chunk] if header is None else [header, chunk]
        if len(tokenize(chunk_delimiter.join(chunk_with_header))) > max_tokens:
            logging.info("warning: chunk overflow")
            if (
                add_ellipsis_for_overflow
                and len(tokenize(chunk_delimiter.join(candidate + ["..."]))) <= max_tokens
            ):
                candidate.append("...")
                dropped_chunk_count += 1
            continue
        extended_candidate_token_count = len(tokenize(chunk_delimiter.join(candidate + [chunk])))
        if extended_candidate_token_count > max_tokens:
            output.append(chunk_delimiter.join(candidate))
            output_indices.append(candidate_indices)
            candidate = chunk_with_header
            candidate_indices = [chunk_i]
        else:
            candidate.append(chunk)
            candidate_indices.append(chunk_i)
    if (header is not None and len(candidate) > 1) or (header is None and len(candidate) > 0):
        output.append(chunk_delimiter.join(candidate))
        output_indices.append(candidate_indices)
    return output, output_indices, dropped_chunk_count


def summarize(
    client: Client,
    text: str,
    detail: float = 0,
    model: str = "gpt-4-turbo",
    additional_instructions: Optional[str] = None,
    minimum_chunk_size: int = 500,
    chunk_delimiter: str = ".",
    summarize_recursively=False,
    verbose=False,
):
    """Summarizes a given text by splitting it into chunks, each of which is summarized individually.

    Args:
        text (str): The text to be summarized.
        detail (float, optional): A value between 0 and 1 indicating the desired level of detail in the summary.
        0 leads to a higher level summary, and 1 results in a more detailed summary. Defaults to 0.
        model (str, optional): The model to use for generating summaries. Defaults to 'gpt-3.5-turbo'.
        additional_instructions (Optional[str], optional): Additional instructions to provide to the model for customizing summaries.
        minimum_chunk_size (Optional[int], optional): The minimum size for text chunks. Defaults to 500.
        chunk_delimiter (str, optional): The delimiter used to split the text into chunks. Defaults to ".".
        summarize_recursively (bool, optional): If True, summaries are generated recursively, using previous summaries for context.
        verbose (bool, optional): If True, logging.infos detailed information about the chunking process.

    Returns:
        The final compiled summary of the text.

    """
    assert 0 <= detail <= 1

    max_chunks = len(chunk_on_delimiter(text, minimum_chunk_size, chunk_delimiter))
    min_chunks = 1
    num_chunks = int(min_chunks + detail * (max_chunks - min_chunks))

    document_length = len(tokenize(text))
    chunk_size = max(minimum_chunk_size, document_length // num_chunks)
    text_chunks = chunk_on_delimiter(text, chunk_size, chunk_delimiter)
    if verbose:
        logging.info(f"Splitting the text into {len(text_chunks)} chunks to be summarized.")
        logging.info(f"Chunk lengths are {[len(tokenize(x)) for x in text_chunks]}")

    system_message_content = "Rewrite this text in summarized form."
    if additional_instructions is not None:
        system_message_content += f"\n\n{additional_instructions}"

    accumulated_summaries = []
    for chunk in text_chunks:
        if summarize_recursively and accumulated_summaries:
            accumulated_summaries_string = "\n\n".join(accumulated_summaries)
            user_message_content = f"Previous summaries:\n\n{accumulated_summaries_string}\n\nText to summarize next:\n\n{chunk}"
        else:
            user_message_content = chunk

        messages = [
            {"role": "system", "content": system_message_content},
            {"role": "user", "content": user_message_content},
        ]

        response = get_chat_completion(client, messages, model=model)
        accumulated_summaries.append(response)

    final_summary = "\n\n".join(accumulated_summaries)

    return final_summary
