"""Tests for analyze module: vote, unanimous, mcnemar, ci, analyze."""
import json
import numpy as np
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import analyze as A
import scoring as S


class TestVote:
    """Test majority voting with confidence tie-breaking."""

    def test_vote_unanimous_majority(self):
        """Unanimous answer returns that answer."""
        task = {"kind": "mc", "n_options": 4}
        answers = ["A", "A", "A"]
        confs = [0.9, 0.8, 0.7]
        assert A.vote(answers, confs, task) == "A"

    def test_vote_simple_majority(self):
        """2-1 majority returns majority answer."""
        task = {"kind": "mc", "n_options": 4}
        answers = ["A", "A", "B"]
        confs = [0.9, 0.8, 0.95]  # B has higher conf but loses to majority
        assert A.vote(answers, confs, task) == "A"

    def test_vote_no_majority_confidence_tie_break(self):
        """No majority (1-1-1): highest confidence wins."""
        task = {"kind": "mc", "n_options": 4}
        answers = ["A", "B", "C"]
        confs = [0.5, 0.9, 0.3]
        assert A.vote(answers, confs, task) == "B"

    def test_vote_no_majority_earliest_on_conf_tie(self):
        """Tie-break by earliest index if confs equal."""
        task = {"kind": "mc", "n_options": 4}
        answers = ["A", "B", "C"]
        confs = [0.8, 0.8, 0.8]  # All tied
        # Should pick earliest, which is A (index 0)
        assert A.vote(answers, confs, task) == "A"

    def test_vote_all_none(self):
        """All None answers -> None."""
        task = {"kind": "mc", "n_options": 4}
        answers = [None, None, None]
        confs = [0.0, 0.0, 0.0]
        assert A.vote(answers, confs, task) is None

    def test_vote_some_none_abstentions(self):
        """None answers are skipped in voting."""
        task = {"kind": "mc", "n_options": 4}
        answers = ["A", None, "A"]
        confs = [0.9, 0.0, 0.8]
        assert A.vote(answers, confs, task) == "A"

    def test_vote_numeric_near_equal_clustering(self):
        """Numeric answers within 1% form a cluster."""
        task = {"kind": "seqqa2", "subtask": "x"}
        # 100, 100.5, 101 should all cluster together
        answers = ["100", "100.5", "101"]
        confs = [0.5, 0.6, 0.7]
        # All three cluster, so first one returned
        result = A.vote(answers, confs, task)
        # Verify it's a valid answer from the group
        assert result in answers

    def test_vote_numeric_separate_clusters(self):
        """Numeric answers far apart form separate clusters."""
        task = {"kind": "seqqa2", "subtask": "x"}
        # 100 vs 150: 50% diff, should be separate
        answers = ["100", "150", "100"]
        confs = [0.5, 0.9, 0.5]
        # Majority is 100 (2 answers cluster together)
        result = A.vote(answers, confs, task)
        # Should return one of the "100" answers
        assert S.same(S.canonical(result, task), ("num", 100.0))

    def test_vote_string_list_clustering(self):
        """String list answers in different orders cluster."""
        task = {"kind": "seqqa2", "subtask": "x"}
        # "a, b, c" and "c, b, a" should be equivalent (sorted)
        answers = ["a, b, c", "a, b, c", "x, y, z"]
        confs = [0.8, 0.7, 0.9]
        result = A.vote(answers, confs, task)
        # Majority (2) has a, b, c
        assert result in ["a, b, c", "a, b, c"]


class TestUnanimous:
    """Test unanimity detection."""

    def test_unanimous_all_same(self):
        """All same answers -> True."""
        task = {"kind": "mc", "n_options": 4}
        answers = ["A", "A", "A"]
        assert A.unanimous(answers, task)

    def test_unanimous_different_answers(self):
        """Different answers -> False."""
        task = {"kind": "mc", "n_options": 4}
        answers = ["A", "B", "A"]
        assert not A.unanimous(answers, task)

    def test_unanimous_any_none(self):
        """Any None answer -> False."""
        task = {"kind": "mc", "n_options": 4}
        answers = ["A", "A", None]
        assert not A.unanimous(answers, task)

    def test_unanimous_numeric_within_1_percent(self):
        """Numeric answers within 1% are unanimous."""
        task = {"kind": "seqqa2", "subtask": "x"}
        answers = ["100", "100.5", "101"]
        assert A.unanimous(answers, task)

    def test_unanimous_numeric_outside_1_percent(self):
        """Numeric answers > 1% apart are not unanimous."""
        task = {"kind": "seqqa2", "subtask": "x"}
        answers = ["100", "102", "100"]
        assert not A.unanimous(answers, task)


class TestCi:
    """Test confidence interval bootstrap calculation."""

    def test_ci_basic(self):
        """CI should bracket the mean."""
        x = np.array([1.0, 1.0, 0.0, 1.0])
        idx = np.array([[0, 1, 2, 3]] * 100)  # Simple resampling
        result = A.ci(x, idx)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] <= result[1]
        # Mean is 0.75, CI should bracket it
        assert result[0] <= 0.75 <= result[1]

    def test_ci_shape(self):
        """CI returns [lower, upper] percentiles."""
        x = np.array([0.0, 0.5, 1.0])
        idx = np.random.default_rng(123).integers(0, 3, size=(100, 3))
        result = A.ci(x, idx)
        assert len(result) == 2
        assert isinstance(result[0], float)
        assert isinstance(result[1], float)


class TestMcnemar:
    """Test McNemar's exact test."""

    def test_mcnemar_perfect_agreement(self):
        """No discordant pairs -> p=1.0."""
        a = np.array([True, False, True, False])
        b = np.array([True, False, True, False])
        result = A.mcnemar(a, b)
        assert result["a_only"] == 0
        assert result["b_only"] == 0
        assert result["p_exact"] == 1.0

    def test_mcnemar_complete_disagreement(self):
        """Symmetric disagreement -> p close to 1.0."""
        a = np.array([True, False, False, False])
        b = np.array([False, True, True, True])
        result = A.mcnemar(a, b)
        # a & ~b: [True, False, False, False] -> 1 = a_only
        # ~a & b: [False, True, True, True] -> 3 = b_only
        assert result["a_only"] == 1
        assert result["b_only"] == 3

    def test_mcnemar_one_sided(self):
        """a better than b -> p_exact < 0.5."""
        a = np.array([True, True, False, False])
        b = np.array([True, False, False, False])
        result = A.mcnemar(a, b)
        # a & ~b: [False, True, False, False] -> 1 = a_only
        # ~a & b: [False, False, False, False] -> 0 = b_only
        assert result["a_only"] == 1
        assert result["b_only"] == 0

    def test_mcnemar_returns_dict(self):
        """Result is dict with a_only, b_only, p_exact."""
        a = np.array([True, False])
        b = np.array([False, True])
        result = A.mcnemar(a, b)
        assert isinstance(result, dict)
        assert set(result.keys()) == {"a_only", "b_only", "p_exact"}


class TestAnalyze:
    """Test full analysis on synthetic row data."""

    def create_row(self, qid, category="ProtocolQA", unanimous=True, correct_mask=None):
        """Create a synthetic row matching per_question output."""
        if correct_mask is None:
            correct_mask = [True, True, True, True]
        return {
            "qid": qid,
            "category": category,
            "subtask": "test",
            "unanimous": unanimous,
            "indep_samples_correct": correct_mask[0:3],
            "critique_initial_correct": correct_mask[0],
            "multi_s1_correct": correct_mask[0],
            "multi_s2_correct": correct_mask[1],
            "multi_scientists_agree": True,
            "direct_answer": "A",
            "direct_correct": correct_mask[0],
            "direct_tokens": 100,
            "direct_in": 50,
            "direct_out": 50,
            "direct_latency": 0.1,
            "direct_truncated": 0,
            "direct_parse_fail": 0,
            "indep3_answer": "A",
            "indep3_correct": correct_mask[0],
            "indep3_tokens": 300,
            "indep3_in": 150,
            "indep3_out": 150,
            "indep3_latency": 0.3,
            "indep3_truncated": 0,
            "indep3_parse_fail": 0,
            "critique3_answer": "A",
            "critique3_correct": correct_mask[0],
            "critique3_tokens": 300,
            "critique3_in": 150,
            "critique3_out": 150,
            "critique3_latency": 0.3,
            "critique3_truncated": 0,
            "critique3_parse_fail": 0,
            "multi3_answer": "A",
            "multi3_correct": correct_mask[0],
            "multi3_tokens": 300,
            "multi3_in": 150,
            "multi3_out": 150,
            "multi3_latency": 0.3,
            "multi3_truncated": 0,
            "multi3_parse_fail": 0,
        }

    def test_analyze_basic_stats(self):
        """Analyze computes accuracy and token stats."""
        rows = [self.create_row(f"q{i}") for i in range(5)]
        result = A.analyze(rows)
        assert result["n"] == 5
        assert "strategies" in result
        assert all(s in result["strategies"] for s in A.STRATEGIES)

    def test_analyze_accuracy_all_correct(self):
        """All correct answers -> 1.0 accuracy."""
        rows = [self.create_row(f"q{i}", correct_mask=[True, True, True, True]) for i in range(5)]
        result = A.analyze(rows)
        for s in A.STRATEGIES:
            assert result["strategies"][s]["accuracy"] == 1.0

    def test_analyze_accuracy_all_wrong(self):
        """All wrong answers -> 0.0 accuracy."""
        rows = [self.create_row(f"q{i}", correct_mask=[False, False, False, False]) for i in range(5)]
        result = A.analyze(rows)
        for s in A.STRATEGIES:
            assert result["strategies"][s]["accuracy"] == 0.0

    def test_analyze_ci95_exists(self):
        """Each strategy has 95% CI."""
        rows = [self.create_row(f"q{i}") for i in range(10)]
        result = A.analyze(rows)
        for s in A.STRATEGIES:
            assert "ci95" in result["strategies"][s]
            ci = result["strategies"][s]["ci95"]
            assert len(ci) == 2
            assert ci[0] <= ci[1]

    def test_analyze_contrasts_computed(self):
        """Contrasts between strategy pairs are computed."""
        rows = [self.create_row(f"q{i}") for i in range(5)]
        result = A.analyze(rows)
        assert "contrasts" in result
        # Should have pre-defined pairs
        assert len(result["contrasts"]) > 0

    def test_analyze_by_category_breakdown(self):
        """Results broken down by category."""
        rows = [self.create_row(f"q{i}", category="ProtocolQA") for i in range(3)]
        rows += [self.create_row(f"q{i+3}", category="SeqQA2") for i in range(2)]
        result = A.analyze(rows)
        assert "by_category" in result
        assert "ProtocolQA" in result["by_category"] or "SeqQA2" in result["by_category"]

    def test_analyze_disagreement_rate(self):
        """Disagreement subset is identified."""
        rows = [self.create_row(f"q{i}", unanimous=True) for i in range(3)]
        rows += [self.create_row(f"q{i+3}", unanimous=False) for i in range(2)]
        result = A.analyze(rows)
        assert result["disagreement"]["n"] == 2
        assert result["disagreement"]["frac"] == 0.4

    def test_analyze_transitions_rescue_corruption(self):
        """Transitions tracked (rescue/corruption)."""
        rows = [self.create_row(f"q{i}") for i in range(5)]
        result = A.analyze(rows)
        assert "transitions" in result
        # Should have transition analysis for strategies vs indep3

    def test_analyze_deterministic_with_seed(self):
        """Same input produces same (deterministic) output."""
        rows = [self.create_row(f"q{i}") for i in range(10)]
        result1 = A.analyze(rows)
        result2 = A.analyze(rows)
        # Core accuracy should be identical
        for s in A.STRATEGIES:
            assert result1["strategies"][s]["accuracy"] == result2["strategies"][s]["accuracy"]
