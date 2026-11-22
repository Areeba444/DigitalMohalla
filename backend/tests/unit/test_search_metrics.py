"""Search metrics by hand (M11; DA-25 section 5). Synthetic toy labels, no real judgements."""

import math

import pytest

from app.evaluation.search_metrics import (
    ndcg_at,
    paired_difference,
    per_query,
    precision_at,
    recall_at,
    summarise,
)

LABELS = {"a": 2, "b": 1, "c": 0, "d": 2}  # three relevant items: a, b, d


def test_precision_at_5_counts_label_one_or_more() -> None:
    assert precision_at(["a", "c", "b", "x", "y"], LABELS) == pytest.approx(2 / 5)
    assert precision_at(["a", "b"], LABELS, threshold=2) == pytest.approx(1 / 5)  # S-E3 variant


def test_recall_at_10_and_the_no_answer_query() -> None:
    assert recall_at(["a", "x", "b"], LABELS) == pytest.approx(2 / 3)
    assert recall_at(["a"], {"a": 0, "b": 0}) is None  # left out of recall


def test_ndcg_perfect_order_is_one_and_a_worse_order_is_lower() -> None:
    assert ndcg_at(["a", "d", "b", "c"], LABELS) == pytest.approx(1.0)
    # got: 3/1 + 0 + 1/2 ... by hand: [b, c, a]: 1/1 + 0 + 3/2 = 2.5; ideal [a, d, b]: 3 + 3/1.585 + 1/2
    ideal = 3 + 3 / math.log2(3) + 1 / 2
    assert ndcg_at(["b", "c", "a"], LABELS) == pytest.approx((1 + 0 + 3 / 2) / ideal)
    assert ndcg_at(["a"], {"a": 0}) is None


def test_unjudged_items_count_as_zero() -> None:
    assert precision_at(["zz1", "zz2"], LABELS) == 0.0


def test_summary_by_type_and_paired_difference() -> None:
    labels = {"q1": LABELS, "q2": LABELS}
    hybrid = per_query({"q1": ["a", "d", "b"], "q2": ["a", "d", "b"]}, labels)
    keyword = per_query({"q1": ["c", "x", "a"], "q2": ["b", "c", "x"]}, labels)
    s = summarise(hybrid, {"q1": "exact", "q2": "need"}, resamples=50)
    assert set(s) == {"all", "exact", "need"} and s["all"]["ndcg@10"]["queries"] == 2
    diff = paired_difference(hybrid, keyword, "ndcg@10", 50)
    assert diff is not None and diff["mean"] > 0 and diff["queries"] == 2
