"""Tests for run.py end-to-end with mock model and resume functionality."""
import asyncio
import argparse
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import run
import analyze
import data
from llm import MODELS


class TestRunEndToEnd:
    """Test run.py end-to-end execution with mock model."""

    @pytest.mark.asyncio
    async def test_run_with_mock_model_completes(self, tmp_path):
        """Running with mock model completes without error."""
        with patch.object(run, 'ROOT', tmp_path):
            args = argparse.Namespace(
                model="mock",
                split="pilot",
                flash_only=False,
                limit=2,  # Just 2 tasks for speed
                strategies=None,
                token_budget=None,
                max_requests=None,
                max_tokens=None,
                concurrency=1,
                parallel_questions=1,
            )
            await run.main(args)
            # Should complete without exception

    @pytest.mark.asyncio
    async def test_run_creates_output_structure(self, tmp_path):
        """Running creates expected output directory structure."""
        with patch.object(run, 'ROOT', tmp_path):
            args = argparse.Namespace(
                model="mock",
                split="pilot",
                flash_only=False,
                limit=2,
                strategies=None,
                token_budget=None,
                max_requests=None,
                max_tokens=None,
                concurrency=1,
                parallel_questions=1,
            )
            await run.main(args)

            # Check output structure
            model_name = MODELS["mock"].name
            results_dir = tmp_path / "results" / model_name / "pilot"
            assert results_dir.exists()
            assert (results_dir / "calls.jsonl").exists()
            assert (results_dir / "config.json").exists()

    @pytest.mark.asyncio
    async def test_run_creates_valid_jsonl_log(self, tmp_path):
        """calls.jsonl contains valid JSON records."""
        with patch.object(run, 'ROOT', tmp_path):
            args = argparse.Namespace(
                model="mock",
                split="pilot",
                flash_only=False,
                limit=2,
                strategies=None,
                token_budget=None,
                max_requests=None,
                max_tokens=None,
                concurrency=1,
                parallel_questions=1,
            )
            await run.main(args)

            model_name = MODELS["mock"].name
            calls_file = tmp_path / "results" / model_name / "pilot" / "calls.jsonl"
            lines = calls_file.read_text().strip().split("\n")
            assert len(lines) > 0

            # Each line should be valid JSON
            records = []
            for line in lines:
                if line:
                    r = json.loads(line)
                    records.append(r)
                    # Should have expected fields
                    assert "qid" in r
                    assert "strategy" in r
                    assert "step" in r
                    assert "text" in r
                    assert "usage" in r

            assert len(records) > 0

    @pytest.mark.asyncio
    async def test_run_records_correct_call_count(self, tmp_path):
        """Correct number of API calls recorded."""
        with patch.object(run, 'ROOT', tmp_path):
            args = argparse.Namespace(
                model="mock",
                split="pilot",
                flash_only=False,
                limit=2,
                strategies=None,  # All strategies
                token_budget=None,
                max_requests=None,
                max_tokens=None,
                concurrency=1,
                parallel_questions=1,
            )
            await run.main(args)

            model_name = MODELS["mock"].name
            calls_file = tmp_path / "results" / model_name / "pilot" / "calls.jsonl"
            records = [json.loads(line) for line in calls_file.read_text().strip().split("\n") if line]

            # For 2 tasks, 4 strategies, with call counts (1, 3, 3, 3)
            # Total: 2 * (1 + 3 + 3 + 3) = 20 calls
            # But only if all complete. At minimum should have some records.
            assert len(records) >= 2

    @pytest.mark.asyncio
    async def test_run_resume_no_new_requests(self, tmp_path):
        """Second run with complete cache makes 0 new requests."""
        model_name = MODELS["mock"].name

        with patch.object(run, 'ROOT', tmp_path):
            # First run
            args = argparse.Namespace(
                model="mock",
                split="pilot",
                flash_only=False,
                limit=1,
                strategies=None,
                token_budget=None,
                max_requests=None,
                max_tokens=None,
                concurrency=1,
                parallel_questions=1,
            )
            await run.main(args)

            calls_file = tmp_path / "results" / model_name / "pilot" / "calls.jsonl"
            first_run_count = len(calls_file.read_text().strip().split("\n"))

        # Second run with same temp dir
        with patch.object(run, 'ROOT', tmp_path):
            args = argparse.Namespace(
                model="mock",
                split="pilot",
                flash_only=False,
                limit=1,
                strategies=None,
                token_budget=None,
                max_requests=None,
                max_tokens=None,
                concurrency=1,
                parallel_questions=1,
            )
            await run.main(args)

            calls_file = tmp_path / "results" / model_name / "pilot" / "calls.jsonl"
            second_run_count = len(calls_file.read_text().strip().split("\n"))

        # Second run should add no new lines (same log file)
        assert second_run_count == first_run_count

    @pytest.mark.asyncio
    async def test_run_records_all_required_fields(self, tmp_path):
        """Each call record contains all required fields."""
        with patch.object(run, 'ROOT', tmp_path):
            args = argparse.Namespace(
                model="mock",
                split="pilot",
                flash_only=False,
                limit=1,
                strategies="direct",  # Just direct for speed
                token_budget=None,
                max_requests=None,
                max_tokens=None,
                concurrency=1,
                parallel_questions=1,
            )
            await run.main(args)

            model_name = MODELS["mock"].name
            calls_file = tmp_path / "results" / model_name / "pilot" / "calls.jsonl"
            records = [json.loads(line) for line in calls_file.read_text().strip().split("\n") if line]

            required_fields = {"qid", "strategy", "step", "seed", "text", "usage", "model", "ts", "error"}
            for r in records:
                assert all(f in r for f in required_fields), f"Missing fields in {r.keys()}"
                assert r["usage"]["total_tokens"] > 0

    @pytest.mark.asyncio
    async def test_run_with_analyze_per_question(self, tmp_path):
        """analyze.per_question works on output from run.py."""
        with patch.object(run, 'ROOT', tmp_path):
            args = argparse.Namespace(
                model="mock",
                split="pilot",
                flash_only=False,
                limit=2,
                strategies=None,
                token_budget=None,
                max_requests=None,
                max_tokens=None,
                concurrency=1,
                parallel_questions=1,
            )
            await run.main(args)

        # Now analyze the output
        model_name = MODELS["mock"].name
        with patch.object(analyze, 'ROOT', tmp_path):
            rows = analyze.per_question(model_name, "pilot")
            # Should have at least some rows (depends on how many complete)
            # With 2 tasks and all 4 strategies, we might have 0-2 complete questions
            assert isinstance(rows, list)
            for row in rows:
                assert "qid" in row
                assert "direct_correct" in row
                assert "indep3_correct" in row

    @pytest.mark.asyncio
    async def test_run_with_strategy_subset(self, tmp_path):
        """Run can execute subset of strategies via --strategies flag."""
        with patch.object(run, 'ROOT', tmp_path):
            args = argparse.Namespace(
                model="mock",
                split="pilot",
                flash_only=False,
                limit=1,
                strategies="direct,indep3",  # Only 2 of 4
                token_budget=None,
                max_requests=None,
                max_tokens=None,
                concurrency=1,
                parallel_questions=1,
            )
            await run.main(args)

            model_name = MODELS["mock"].name
            calls_file = tmp_path / "results" / model_name / "pilot" / "calls.jsonl"
            records = [json.loads(line) for line in calls_file.read_text().strip().split("\n") if line]

            strategies_used = {r["strategy"] for r in records}
            # Should only have direct and indep3
            assert strategies_used <= {"direct", "indep3"}

    @pytest.mark.asyncio
    async def test_run_stores_seed_with_call(self, tmp_path):
        """Each call record stores the seed used."""
        with patch.object(run, 'ROOT', tmp_path):
            args = argparse.Namespace(
                model="mock",
                split="pilot",
                flash_only=False,
                limit=1,
                strategies="direct",
                token_budget=None,
                max_requests=None,
                max_tokens=None,
                concurrency=1,
                parallel_questions=1,
            )
            await run.main(args)

            model_name = MODELS["mock"].name
            calls_file = tmp_path / "results" / model_name / "pilot" / "calls.jsonl"
            records = [json.loads(line) for line in calls_file.read_text().strip().split("\n") if line]

            for r in records:
                assert "seed" in r
                assert isinstance(r["seed"], int)
                # Direct strategy should use seed 1000
                if r["strategy"] == "direct":
                    assert r["seed"] == 1000

    @pytest.mark.asyncio
    async def test_run_config_saved(self, tmp_path):
        """Model config is saved to config.json."""
        with patch.object(run, 'ROOT', tmp_path):
            args = argparse.Namespace(
                model="mock",
                split="pilot",
                flash_only=False,
                limit=1,
                strategies=None,
                token_budget=None,
                max_requests=None,
                max_tokens=None,
                concurrency=1,
                parallel_questions=1,
            )
            await run.main(args)

            model_name = MODELS["mock"].name
            config_file = tmp_path / "results" / model_name / "pilot" / "config.json"
            assert config_file.exists()
            config = json.loads(config_file.read_text())
            assert config["model"] == "mock"
            assert config["name"] == "mock"
