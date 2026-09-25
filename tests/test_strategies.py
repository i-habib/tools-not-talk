"""Tests for strategies module: run_strategy with mock call recorder."""
import asyncio
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import strategies as ST


class MockCallRecorder:
    """Records all calls made during strategy execution."""

    def __init__(self):
        self.calls = []

    async def __call__(self, step, prompt, seed):
        """Record call and return mock text."""
        self.calls.append({
            "step": step,
            "prompt": prompt,
            "seed": seed,
        })
        # Return different text for different steps to verify prior outputs are included
        return f"<answer>response_{step}</answer>\nCONFIDENCE: 0.5"


class TestRunStrategy:
    """Test run_strategy with mock call recorder."""

    def create_task(self):
        """Create a minimal task for testing."""
        return {
            "qid": "test-qid",
            "kind": "mc",
            "n_options": 4,
            "question": "Test question?",
            "answer_instruction": "Choose A, B, C, or D.",
        }

    @pytest.mark.asyncio
    async def test_direct_single_call(self):
        """Direct strategy makes exactly 1 call with seed 1000."""
        task = self.create_task()
        recorder = MockCallRecorder()
        await ST.run_strategy("direct", task, recorder)

        assert len(recorder.calls) == 1
        assert recorder.calls[0]["step"] == 0
        assert recorder.calls[0]["seed"] == ST.SEEDS[("direct", 0)]

    @pytest.mark.asyncio
    async def test_indep3_three_calls(self):
        """Indep3 strategy makes exactly 3 calls with seeds 1001, 1002, 1003."""
        task = self.create_task()
        recorder = MockCallRecorder()
        await ST.run_strategy("indep3", task, recorder)

        assert len(recorder.calls) == 3
        steps = [c["step"] for c in recorder.calls]
        # All three steps should be present (order may vary due to gather)
        assert set(steps) == {0, 1, 2}

        # Verify correct seeds
        seeds = {c["step"]: c["seed"] for c in recorder.calls}
        assert seeds[0] == ST.SEEDS[("indep3", 0)]
        assert seeds[1] == ST.SEEDS[("indep3", 1)]
        assert seeds[2] == ST.SEEDS[("indep3", 2)]

    @pytest.mark.asyncio
    async def test_critique3_three_calls_sequential(self):
        """Critique3 makes 3 calls: solve, critique, revise (dependent)."""
        task = self.create_task()
        recorder = MockCallRecorder()
        await ST.run_strategy("critique3", task, recorder)

        assert len(recorder.calls) == 3
        # Order must be sequential: 0 (solve) -> 1 (critique) -> 2 (revise)
        assert recorder.calls[0]["step"] == 0
        assert recorder.calls[1]["step"] == 1
        assert recorder.calls[2]["step"] == 2

        # Verify seeds
        assert recorder.calls[0]["seed"] == ST.SEEDS[("critique3", 0)]
        assert recorder.calls[1]["seed"] == ST.SEEDS[("critique3", 1)]
        assert recorder.calls[2]["seed"] == ST.SEEDS[("critique3", 2)]

    @pytest.mark.asyncio
    async def test_critique3_prior_outputs_included(self):
        """Critique and revise prompts include outputs from prior steps."""
        task = self.create_task()
        recorder = MockCallRecorder()
        await ST.run_strategy("critique3", task, recorder)

        # Step 1 (critique) should include step 0's output in prompt
        critique_prompt = recorder.calls[1]["prompt"]
        assert "response_0" in critique_prompt

        # Step 2 (revise) should include both step 0 and step 1's outputs
        revise_prompt = recorder.calls[2]["prompt"]
        assert "response_0" in revise_prompt
        assert "response_1" in revise_prompt

    @pytest.mark.asyncio
    async def test_multi3_three_calls(self):
        """Multi3 makes 3 calls: researcher, skeptic, adjudicate."""
        task = self.create_task()
        recorder = MockCallRecorder()
        await ST.run_strategy("multi3", task, recorder)

        assert len(recorder.calls) == 3
        steps = [c["step"] for c in recorder.calls]
        # First two are parallel (0, 1), then adjudicate (2)
        assert set(steps) == {0, 1, 2}

        # Verify seeds
        seeds = {c["step"]: c["seed"] for c in recorder.calls}
        assert seeds[0] == ST.SEEDS[("multi3", 0)]
        assert seeds[1] == ST.SEEDS[("multi3", 1)]
        assert seeds[2] == ST.SEEDS[("multi3", 2)]

    @pytest.mark.asyncio
    async def test_multi3_prior_outputs_included(self):
        """Adjudicate prompt includes researcher and skeptic outputs."""
        task = self.create_task()
        recorder = MockCallRecorder()
        await ST.run_strategy("multi3", task, recorder)

        # Find the adjudicate call (step 2)
        adjudicate_call = [c for c in recorder.calls if c["step"] == 2][0]
        adjudicate_prompt = adjudicate_call["prompt"]

        # Should contain outputs from both prior calls
        assert "response_0" in adjudicate_prompt
        assert "response_1" in adjudicate_prompt

    @pytest.mark.asyncio
    async def test_invalid_strategy_raises(self):
        """Invalid strategy raises ValueError."""
        task = self.create_task()
        recorder = MockCallRecorder()

        with pytest.raises(ValueError, match="invalid_strategy"):
            await ST.run_strategy("invalid_strategy", task, recorder)

    @pytest.mark.asyncio
    async def test_all_strategies_use_correct_seeds(self):
        """All strategies use pre-defined seeds from SEEDS dict."""
        task = self.create_task()

        for strategy in ST.STRATEGIES:
            recorder = MockCallRecorder()
            await ST.run_strategy(strategy, task, recorder)

            # Verify each call has the correct seed from SEEDS dict
            for call in recorder.calls:
                expected_seed = ST.SEEDS[(strategy, call["step"])]
                assert call["seed"] == expected_seed, \
                    f"{strategy} step {call['step']}: expected {expected_seed}, got {call['seed']}"

    @pytest.mark.asyncio
    async def test_all_strategies_call_count(self):
        """Verify all strategies make correct number of calls."""
        task = self.create_task()

        for strategy in ST.STRATEGIES:
            recorder = MockCallRecorder()
            await ST.run_strategy(strategy, task, recorder)

            expected_calls = ST.CALLS[strategy]
            assert len(recorder.calls) == expected_calls, \
                f"{strategy}: expected {expected_calls} calls, got {len(recorder.calls)}"

    @pytest.mark.asyncio
    async def test_prompts_are_strings(self):
        """All generated prompts are strings."""
        task = self.create_task()
        recorder = MockCallRecorder()

        for strategy in ST.STRATEGIES:
            recorder = MockCallRecorder()
            await ST.run_strategy(strategy, task, recorder)

            for call in recorder.calls:
                assert isinstance(call["prompt"], str)
                assert len(call["prompt"]) > 0

    @pytest.mark.asyncio
    async def test_solve_prompt_contains_question(self):
        """Solve prompts include the question."""
        task = self.create_task()
        task["question"] = "Unique question text 12345"

        recorder = MockCallRecorder()
        await ST.run_strategy("direct", task, recorder)

        assert recorder.calls[0]["prompt"] is not None
        # Solve prompt should contain the question (checking for "12345" since the full question might be formatted)
