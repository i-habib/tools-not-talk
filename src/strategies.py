"""The four inference strategies. B, C and D each make exactly three model calls per question.

Only the *visible* output of an earlier call is passed to a later call (never hidden reasoning).
Final answers are derived from logged outputs in analyze.py; here we only make and log the calls.
"""
from __future__ import annotations

FORMAT = """Respond in exactly this format and keep it short:
<answer>YOUR ANSWER</answer>
CONFIDENCE: <probability between 0 and 1 that your answer is correct>
JUSTIFICATION: <at most two sentences>"""


def _answer_block(task: dict) -> str:
    return f"{task['answer_instruction']}\n\n{FORMAT}"


def solve_prompt(task: dict, role: str | None = None) -> str:
    head = {
        None: "Solve the following biology research question.",
        "researcher": "You are a molecular biology researcher. Solve the following biology research question independently.",
        "skeptic": ("You are a skeptical scientific reviewer. Solve the following biology research question independently, "
                    "looking especially for subtle experimental, biological or computational errors and traps."),
    }[role]
    return f"{head}\n\n{task['question']}\n\n{_answer_block(task)}"


def critique_prompt(task: dict, solution: str) -> str:
    return (
        "Below are a biology research question and a proposed solution. Act as a critical reviewer: identify any "
        "scientific, computational or reasoning error in the solution. If you think the answer is wrong, say which "
        "answer you believe is correct and why. If you find no error, say so.\n\n"
        f"{task['question']}\n\nProposed solution:\n{solution.strip()}\n\n"
        "Respond with at most four sentences, starting with \"CRITIQUE:\"."
    )


def revise_prompt(task: dict, solution: str, critique: str) -> str:
    return (
        "Below are a biology research question, a first attempt at solving it, and a reviewer's critique of that "
        "attempt. Either may contain mistakes. Considering both, produce the final answer.\n\n"
        f"{task['question']}\n\nFirst attempt:\n{solution.strip()}\n\nReviewer's critique:\n{critique.strip()}\n\n"
        f"{_answer_block(task)}"
    )


def adjudicate_prompt(task: dict, a1: str, a2: str) -> str:
    return (
        "Two scientists independently analysed the biology research question below. Adjudicate between their "
        "analyses (either or both may be wrong) and submit the final answer.\n\n"
        f"{task['question']}\n\nAnalysis 1 (molecular biology researcher):\n{a1.strip()}\n\n"
        f"Analysis 2 (skeptical scientific reviewer):\n{a2.strip()}\n\n{_answer_block(task)}"
    )


STRATEGIES = ["direct", "indep3", "critique3", "multi3"]
CALLS = {"direct": 1, "indep3": 3, "critique3": 3, "multi3": 3}
SEEDS = {("direct", 0): 1000, ("indep3", 0): 1001, ("indep3", 1): 1002, ("indep3", 2): 1003,
         ("critique3", 0): 2001, ("critique3", 1): 2002, ("critique3", 2): 2003,
         ("multi3", 0): 3001, ("multi3", 1): 3002, ("multi3", 2): 3003}


async def run_strategy(strategy: str, task: dict, call):
    """`call(step, prompt, seed) -> text` logs/caches the call and returns visible text."""
    s = lambda i: SEEDS[(strategy, i)]  # noqa: E731
    if strategy == "direct":
        await call(0, solve_prompt(task), s(0))
    elif strategy == "indep3":
        import asyncio
        await asyncio.gather(*(call(i, solve_prompt(task), s(i)) for i in range(3)))
    elif strategy == "critique3":
        sol = await call(0, solve_prompt(task), s(0))
        crit = await call(1, critique_prompt(task, sol), s(1))
        await call(2, revise_prompt(task, sol, crit), s(2))
    elif strategy == "multi3":
        import asyncio
        a1, a2 = await asyncio.gather(call(0, solve_prompt(task, "researcher"), s(0)),
                                      call(1, solve_prompt(task, "skeptic"), s(1)))
        await call(2, adjudicate_prompt(task, a1, a2), s(2))
    else:
        raise ValueError(strategy)
