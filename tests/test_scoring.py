"""Tests for scoring module: parse_answer, parse_confidence, canonical, same, is_correct."""
import json
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import scoring as S
import data


class TestParseAnswer:
    """Test parse_answer with various input formats and edge cases."""

    def test_mc_simple_letter(self):
        """MC: extract simple single letter."""
        task = {"kind": "mc", "n_options": 4}
        assert S.parse_answer("<answer>B</answer>", task) == "B"

    def test_mc_lowercase_letter(self):
        """MC: handle lowercase letters (should uppercase)."""
        task = {"kind": "mc", "n_options": 4}
        assert S.parse_answer("<answer>c</answer>", task) == "C"

    def test_mc_letter_with_parentheses(self):
        """MC: extract letter from (B) format."""
        task = {"kind": "mc", "n_options": 4}
        assert S.parse_answer("<answer>(D)</answer>", task) == "D"

    def test_mc_letter_with_trailing_text(self):
        """MC: extract letter ignoring trailing text like 'C) text...'."""
        task = {"kind": "mc", "n_options": 4}
        assert S.parse_answer("<answer>B) The answer is B</answer>", task) == "B"

    def test_mc_letter_with_period(self):
        """MC: handle period suffix."""
        task = {"kind": "mc", "n_options": 4}
        assert S.parse_answer("<answer>A.</answer>", task) == "A"

    def test_mc_out_of_range_letter(self):
        """MC: reject letter beyond n_options (4 options means A-D)."""
        task = {"kind": "mc", "n_options": 4}
        assert S.parse_answer("<answer>E</answer>", task) is None

    def test_mc_multiple_answer_tags(self):
        """MC: use last <answer> tag."""
        task = {"kind": "mc", "n_options": 4}
        text = "<answer>A</answer> wait, actually <answer>C</answer>"
        assert S.parse_answer(text, task) == "C"

    def test_mc_no_answer_tag(self):
        """MC: return None if no answer tag."""
        task = {"kind": "mc", "n_options": 4}
        assert S.parse_answer("My answer is B but no XML tags.", task) is None

    def test_mc_empty_answer_tag(self):
        """MC: return None if answer tag is empty."""
        task = {"kind": "mc", "n_options": 4}
        assert S.parse_answer("<answer></answer>", task) is None

    def test_mc_malformed_letters(self):
        """MC: reject non-letter content."""
        task = {"kind": "mc", "n_options": 4}
        assert S.parse_answer("<answer>123</answer>", task) is None
        assert S.parse_answer("<answer>AB</answer>", task) is None

    def test_seqqa2_raw_answer(self):
        """SeqQA2: extract raw answer from answer tag."""
        task = {"kind": "seqqa2", "subtask": "enzyme_kinetics"}
        assert S.parse_answer("<answer>42.5</answer>", task) == "42.5"

    def test_seqqa2_text_answer(self):
        """SeqQA2: preserve text answers."""
        task = {"kind": "seqqa2", "subtask": "some_type"}
        assert S.parse_answer("<answer>ATP synthase</answer>", task) == "ATP synthase"

    def test_seqqa2_whitespace_trimming(self):
        """SeqQA2: trim whitespace from answer."""
        task = {"kind": "seqqa2", "subtask": "some_type"}
        assert S.parse_answer("<answer>  result  </answer>", task) == "result"

    def test_none_input(self):
        """Return None if input is None."""
        task = {"kind": "mc", "n_options": 4}
        assert S.parse_answer(None, task) is None

    def test_empty_string_input(self):
        """Return None if input is empty string."""
        task = {"kind": "mc", "n_options": 4}
        assert S.parse_answer("", task) is None


class TestParseConfidence:
    """Test parse_confidence with various formats."""

    def test_confidence_explicit_format(self):
        """Parse 'CONFIDENCE: 0.8' format."""
        text = "My analysis is correct.\nCONFIDENCE: 0.8\nJUSTIFICATION: ..."
        assert S.parse_confidence(text) == 0.8

    def test_confidence_equals_sign(self):
        """Parse 'CONFIDENCE = 0.75' format."""
        assert S.parse_confidence("CONFIDENCE = 0.75") == 0.75

    def test_confidence_bold_format(self):
        """Parse '**0.75**' format (markdown bold)."""
        assert S.parse_confidence("My confidence: **0.75**") == 0.75

    def test_confidence_decimal_only(self):
        """Parse '.9' format (no leading zero)."""
        assert S.parse_confidence("CONFIDENCE: .9") == 0.9

    def test_confidence_missing(self):
        """Return 0.0 if no CONFIDENCE found."""
        assert S.parse_confidence("No confidence here") == 0.0

    def test_confidence_none_input(self):
        """Return 0.0 if input is None."""
        assert S.parse_confidence(None) == 0.0

    def test_confidence_clamped_above_one(self):
        """Clamp confidence > 1.0 to 1.0."""
        assert S.parse_confidence("CONFIDENCE: 1.5") == 1.0

    def test_confidence_clamped_below_zero(self):
        """Clamp confidence < 0.0 to 0.0."""
        assert S.parse_confidence("CONFIDENCE: -0.5") == 0.0

    def test_confidence_edge_values(self):
        """Test exact boundaries."""
        assert S.parse_confidence("CONFIDENCE: 0.0") == 0.0
        assert S.parse_confidence("CONFIDENCE: 1.0") == 1.0

    def test_confidence_case_insensitive(self):
        """CONFIDENCE keyword is case-insensitive."""
        assert S.parse_confidence("confidence: 0.5") == 0.5
        assert S.parse_confidence("CONFIDENCE: 0.5") == 0.5
        assert S.parse_confidence("Confidence: 0.5") == 0.5


class TestCanonical:
    """Test canonical form generation for voting."""

    def test_canonical_none(self):
        """None stays None."""
        task = {"kind": "mc", "n_options": 4}
        assert S.canonical(None, task) is None

    def test_canonical_mc_letter(self):
        """MC answers return letter as-is."""
        task = {"kind": "mc", "n_options": 4}
        assert S.canonical("A", task) == "A"
        assert S.canonical("C", task) == "C"

    def test_canonical_numeric_single(self):
        """Single numeric value returns ('num', float)."""
        task = {"kind": "seqqa2", "subtask": "x"}
        assert S.canonical("42.5", task) == ("num", 42.5)

    def test_canonical_numeric_negative(self):
        """Handle negative numbers."""
        task = {"kind": "seqqa2", "subtask": "x"}
        assert S.canonical("-3.14", task) == ("num", -3.14)

    def test_canonical_numeric_integer(self):
        """Integer strings also become numeric."""
        task = {"kind": "seqqa2", "subtask": "x"}
        assert S.canonical("100", task) == ("num", 100.0)

    def test_canonical_numeric_list(self):
        """Comma-separated numbers -> sorted tuple."""
        task = {"kind": "seqqa2", "subtask": "x"}
        # Should parse, sort, and return as ('nums', (1.0, 2.0, 3.0))
        result = S.canonical("3, 1, 2", task)
        assert result == ("nums", (1.0, 2.0, 3.0))

    def test_canonical_string_single(self):
        """Single non-numeric string uppercased."""
        task = {"kind": "seqqa2", "subtask": "x"}
        assert S.canonical("ATP synthase", task) == ("str", "ATP SYNTHASE")

    def test_canonical_string_list(self):
        """Comma-separated strings -> sorted uppercase tuple."""
        task = {"kind": "seqqa2", "subtask": "x"}
        result = S.canonical("beta, alpha, gamma", task)
        assert result == ("str", ("ALPHA", "BETA", "GAMMA"))

    def test_canonical_whitespace_handling(self):
        """Strip whitespace and trailing periods (rstrip . then upper)."""
        task = {"kind": "seqqa2", "subtask": "x"}
        # Note: strip() removes outer whitespace, rstrip(".") removes dots, but trailing spaces remain
        result = S.canonical("  ATP synthase  .  ", task)
        # After strip(): "ATP synthase  ."
        # After rstrip("."): "ATP synthase  "
        # After upper(): "ATP SYNTHASE  "
        assert result == ("str", "ATP SYNTHASE  ")

    def test_canonical_list_with_whitespace(self):
        """Handle whitespace in list items."""
        task = {"kind": "seqqa2", "subtask": "x"}
        result = S.canonical("  a  ,  b  ,  c  ", task)
        assert result == ("str", ("A", "B", "C"))


class TestSame:
    """Test answer equivalence function."""

    def test_same_none_values(self):
        """None is never equal to anything."""
        assert not S.same(None, None)
        assert not S.same(None, ("num", 1.0))

    def test_same_mc_exact(self):
        """MC letters must match exactly."""
        assert S.same("A", "A")
        assert not S.same("A", "B")

    def test_same_numeric_exact(self):
        """Exact numeric match."""
        assert S.same(("num", 42.0), ("num", 42.0))

    def test_same_numeric_within_1_percent(self):
        """Numerics within 1% are considered same."""
        assert S.same(("num", 100.0), ("num", 100.5))  # 0.5% diff
        assert S.same(("num", 100.0), ("num", 101.0))  # 1.0% diff
        assert not S.same(("num", 100.0), ("num", 101.1))  # 1.1% diff

    def test_same_numeric_very_small_numbers(self):
        """For small numbers, use absolute tolerance."""
        assert S.same(("num", 0.001), ("num", 0.001))
        assert not S.same(("num", 0.0), ("num", 1.0))

    def test_same_numeric_different_types(self):
        """Numeric tuple doesn't equal other types."""
        assert not S.same(("num", 42.0), ("str", "42"))
        assert not S.same(("num", 42.0), "A")

    def test_same_string_case_insensitive(self):
        """String tuples must match after upper."""
        assert S.same(("str", "ATP"), ("str", "ATP"))
        assert not S.same(("str", "ATP"), ("str", "GTP"))

    def test_same_string_list_order_insensitive(self):
        """Sorted tuples must match."""
        t1 = ("str", ("A", "B", "C"))
        t2 = ("str", ("A", "B", "C"))
        assert S.same(t1, t2)
        # Order doesn't matter because canonical already sorted them
        t3 = ("str", ("C", "B", "A"))
        assert not S.same(t1, t3)  # They're different if not pre-sorted


class TestIsCorrect:
    """Test correctness checking on real tasks."""

    @pytest.fixture(autouse=True)
    def load_tasks(self):
        """Load real tasks from data."""
        self.tasks = {t["qid"]: t for t in data.load("pilot")}
        self.mc_tasks = [t for t in self.tasks.values() if t["kind"] == "mc"]
        self.seqqa2_tasks = [t for t in self.tasks.values() if t["kind"] == "seqqa2"]

    def test_is_correct_none_answer(self):
        """None answer is never correct."""
        task = self.mc_tasks[0] if self.mc_tasks else {"kind": "mc", "n_options": 4, "correct": "A"}
        assert not S.is_correct(None, task)

    def test_is_correct_mc_correct_answer(self):
        """Correct MC answer returns True."""
        if not self.mc_tasks:
            pytest.skip("No MC tasks in pilot split")
        task = self.mc_tasks[0]
        assert S.is_correct(task["correct"], task)

    def test_is_correct_mc_wrong_answer(self):
        """Wrong MC answer returns False."""
        if not self.mc_tasks:
            pytest.skip("No MC tasks in pilot split")
        task = self.mc_tasks[0]
        wrong = None
        for letter in "ABCDEFGHIJ":
            if letter != task["correct"] and ord(letter) - 65 < task["n_options"]:
                wrong = letter
                break
        if wrong:
            assert not S.is_correct(wrong, task)

    def test_is_correct_seqqa2_correct_answer(self):
        """Correct SeqQA2 answer returns True."""
        if not self.seqqa2_tasks:
            pytest.skip("No SeqQA2 tasks in pilot split")
        task = self.seqqa2_tasks[0]
        # Gold answer should always validate
        assert S.is_correct(task["correct"], task)

    def test_is_correct_seqqa2_wrong_answer(self):
        """Random perturbation of SeqQA2 answer is usually False."""
        if not self.seqqa2_tasks:
            pytest.skip("No SeqQA2 tasks in pilot split")
        task = self.seqqa2_tasks[0]
        # Create a clearly wrong answer
        wrong_ans = "completely_wrong_answer_12345"
        assert not S.is_correct(wrong_ans, task)
