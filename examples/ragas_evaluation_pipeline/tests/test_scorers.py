"""Deterministic scorer unit tests (Step 12)."""

from ragas_evaluation_pipeline.metrics import scorers


def test_recall_and_precision():
    assert scorers.context_recall(["doc1"], ["doc1", "doc2"]) == 1.0
    assert scorers.context_precision(["doc1"], ["doc1", "doc2"]) == 0.5
    assert scorers.context_recall(["doc1", "doc3"], ["doc1"]) == 0.5


def test_citation_coverage():
    assert scorers.citation_coverage(["doc1"], ["doc1"]) == 1.0
    assert scorers.citation_coverage(["doc1", "doc2"], ["doc1"]) == 0.5
    assert scorers.citation_coverage([], []) == 1.0


def test_faithfulness_grounded():
    ctx = [{"text": "The Eiffel Tower stands 330 meters tall."}]
    assert scorers.faithfulness_score("The Eiffel Tower stands 330 meters tall.", ctx) == 1.0


def test_answer_correctness_catches_right_doc_wrong_sentence():
    """The Risk-1 safeguard: an answer grounded in the RIGHT document but quoting
    the WRONG sentence stays faithful yet scores LOW on correctness.
    """
    contexts = [
        {"text": "The Eiffel Tower is located in Paris, France. It stands 330 meters tall."}
    ]
    reference = "The Eiffel Tower stands 330 meters tall."
    wrong_answer = "The Eiffel Tower is located in Paris, France."

    # Grounded in the context -> faithfulness stays high...
    assert scorers.faithfulness_score(wrong_answer, contexts) >= 0.8
    # ...but it does not match the reference fact -> correctness is low.
    assert scorers.answer_correctness_score(wrong_answer, reference) < 0.6
    # A correct answer scores high.
    assert scorers.answer_correctness_score(reference, reference) == 1.0
