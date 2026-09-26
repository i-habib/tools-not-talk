# Results (pilot)

## gpt-oss-120b  (n = 10 questions)

| Strategy | Acc | 95% CI | tokens/q | out tok/q | correct/Mtok | trunc | parse-fail |
|---|---|---|---|---|---|---|---|
| Direct (1 call) | 0.700 | [0.400, 1.000] | 578 | 170 | 1211 | 0 | 0 |
| Independent×3 (vote) | 0.800 | [0.500, 1.000] | 1745 | 520 | 458 | 0 | 0 |
| Solve→Critique→Revise | 0.600 | [0.300, 0.900] | 2009 | 536 | 299 | 0 | 0 |
| Two scientists + adjudicator | 0.700 | [0.400, 1.000] | 1983 | 569 | 353 | 0 | 0 |

| Paired contrast | Δacc | 95% CI | A-only | B-only | McNemar p |
|---|---|---|---|---|---|
| multi3-indep3 | -0.100 | [-0.300, +0.000] | 0 | 1 | 1.000 |
| critique3-indep3 | -0.200 | [-0.500, +0.000] | 0 | 2 | 0.500 |
| indep3-direct | +0.100 | [+0.000, +0.300] | 1 | 0 | 1.000 |
| multi3-direct | +0.000 | [+0.000, +0.000] | 0 | 0 | 1.000 |
| critique3-direct | -0.100 | [-0.300, +0.000] | 0 | 1 | 1.000 |
| multi3-critique3 | +0.100 | [+0.000, +0.300] | 1 | 0 | 1.000 |

**Disagreement subset** (independent samples not unanimous): 2 / 10 (20%)

| Strategy | acc on disagreement | acc on unanimous |
|---|---|---|
| Direct (1 call) | 0.000 (0/2) | 0.875 (7/8) |
| Independent×3 (vote) | 0.500 (1/2) | 0.875 (7/8) |
| Solve→Critique→Revise | 0.000 (0/2) | 0.750 (6/8) |
| Two scientists + adjudicator | 0.000 (0/2) | 0.875 (7/8) |

| vs Independent×3 vote | rescue P(correct | vote wrong) | corruption P(wrong | vote right) |
|---|---|---|
| critique3 | 0.000 (0/2) | 0.250 (2/8) |
| multi3 | 0.000 (0/2) | 0.125 (1/8) |
| direct | 0.000 (0/2) | 0.125 (1/8) |

| Category | n | direct | indep3 | critique3 | multi3 | disagree |
|---|---|---|---|---|---|---|
| ProtocolQA | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |
| SeqQA | 2 | 0.50 | 1.00 | 0.00 | 0.50 | 0.50 |
| DbQA | 2 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| LitQA2 | 2 | 0.50 | 0.50 | 0.50 | 0.50 | 0.00 |
| SeqQA2 | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |

Single independent sample acc: 0.767; any-of-3 correct (oracle): 0.800
Critique revision: {"rescue": {"rate": 0.0, "n": 3, "k": 0}, "corruption": {"rate": 0.14285714285714285, "n": 7, "k": 1}, "initial_acc": 0.7}
Multi-agent adjudication: {"scientists_disagree": 2, "researcher_acc": 0.8, "skeptic_acc": 0.7, "adjudicator_acc_when_disagree": {"rate": 0.0, "n": 2, "k": 0}, "either_scientist_correct_when_disagree": {"rate": 0.5, "n": 2, "k": 1}, "adjudicator_overrides_agreement": 0}

## gemma-4-31b  (n = 10 questions)

| Strategy | Acc | 95% CI | tokens/q | out tok/q | correct/Mtok | trunc | parse-fail |
|---|---|---|---|---|---|---|---|
| Direct (1 call) | 0.700 | [0.400, 1.000] | 676 | 334 | 1036 | 1 | 1 |
| Independent×3 (vote) | 0.700 | [0.400, 1.000] | 2016 | 993 | 347 | 3 | 3 |
| Solve→Critique→Revise | 0.800 | [0.500, 1.000] | 2308 | 549 | 347 | 0 | 0 |
| Two scientists + adjudicator | 0.900 | [0.700, 1.000] | 2643 | 869 | 340 | 1 | 0 |

| Paired contrast | Δacc | 95% CI | A-only | B-only | McNemar p |
|---|---|---|---|---|---|
| multi3-indep3 | +0.200 | [+0.000, +0.500] | 2 | 0 | 0.500 |
| critique3-indep3 | +0.100 | [+0.000, +0.300] | 1 | 0 | 1.000 |
| indep3-direct | +0.000 | [+0.000, +0.000] | 0 | 0 | 1.000 |
| multi3-direct | +0.200 | [+0.000, +0.500] | 2 | 0 | 0.500 |
| critique3-direct | +0.100 | [+0.000, +0.300] | 1 | 0 | 1.000 |
| multi3-critique3 | +0.100 | [+0.000, +0.300] | 1 | 0 | 1.000 |

**Disagreement subset** (independent samples not unanimous): 2 / 10 (20%)

| Strategy | acc on disagreement | acc on unanimous |
|---|---|---|
| Direct (1 call) | 0.000 (0/2) | 0.875 (7/8) |
| Independent×3 (vote) | 0.000 (0/2) | 0.875 (7/8) |
| Solve→Critique→Revise | 0.500 (1/2) | 0.875 (7/8) |
| Two scientists + adjudicator | 1.000 (2/2) | 0.875 (7/8) |

| vs Independent×3 vote | rescue P(correct | vote wrong) | corruption P(wrong | vote right) |
|---|---|---|
| critique3 | 0.333 (1/3) | 0.000 (0/7) |
| multi3 | 0.667 (2/3) | 0.000 (0/7) |
| direct | 0.000 (0/3) | 0.000 (0/7) |

| Category | n | direct | indep3 | critique3 | multi3 | disagree |
|---|---|---|---|---|---|---|
| ProtocolQA | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |
| SeqQA | 2 | 0.50 | 0.50 | 1.00 | 1.00 | 0.50 |
| DbQA | 2 | 0.50 | 0.50 | 0.50 | 0.50 | 0.00 |
| LitQA2 | 2 | 0.50 | 0.50 | 0.50 | 1.00 | 0.50 |
| SeqQA2 | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |

Single independent sample acc: 0.733; any-of-3 correct (oracle): 0.800
Critique revision: {"rescue": {"rate": 0.0, "n": 2, "k": 0}, "corruption": {"rate": 0.0, "n": 8, "k": 0}, "initial_acc": 0.8}
Multi-agent adjudication: {"scientists_disagree": 3, "researcher_acc": 0.8, "skeptic_acc": 0.8, "adjudicator_acc_when_disagree": {"rate": 0.6666666666666666, "n": 3, "k": 2}, "either_scientist_correct_when_disagree": {"rate": 0.6666666666666666, "n": 3, "k": 2}, "adjudicator_overrides_agreement": 0}

## flash-lite  (n = 10 questions)

| Strategy | Acc | 95% CI | tokens/q | out tok/q | correct/Mtok | trunc | parse-fail |
|---|---|---|---|---|---|---|---|
| Direct (1 call) | 0.900 | [0.700, 1.000] | 640 | 298 | 1407 | 0 | 0 |
| Independent×3 (vote) | 0.900 | [0.700, 1.000] | 1993 | 969 | 452 | 3 | 0 |
| Solve→Critique→Revise | 0.700 | [0.400, 1.000] | 1829 | 509 | 383 | 1 | 0 |
| Two scientists + adjudicator | 1.000 | [1.000, 1.000] | 2354 | 1073 | 425 | 1 | 0 |

| Paired contrast | Δacc | 95% CI | A-only | B-only | McNemar p |
|---|---|---|---|---|---|
| multi3-indep3 | +0.100 | [+0.000, +0.300] | 1 | 0 | 1.000 |
| critique3-indep3 | -0.200 | [-0.500, +0.000] | 0 | 2 | 0.500 |
| indep3-direct | +0.000 | [-0.300, +0.300] | 1 | 1 | 1.000 |
| multi3-direct | +0.100 | [+0.000, +0.300] | 1 | 0 | 1.000 |
| critique3-direct | -0.200 | [-0.500, +0.000] | 0 | 2 | 0.500 |
| multi3-critique3 | +0.300 | [+0.000, +0.600] | 3 | 0 | 0.250 |

**Disagreement subset** (independent samples not unanimous): 1 / 10 (10%)

| Strategy | acc on disagreement | acc on unanimous |
|---|---|---|
| Direct (1 call) | 1.000 (1/1) | 0.889 (8/9) |
| Independent×3 (vote) | 0.000 (0/1) | 1.000 (9/9) |
| Solve→Critique→Revise | 0.000 (0/1) | 0.778 (7/9) |
| Two scientists + adjudicator | 1.000 (1/1) | 1.000 (9/9) |

| vs Independent×3 vote | rescue P(correct | vote wrong) | corruption P(wrong | vote right) |
|---|---|---|
| critique3 | 0.000 (0/1) | 0.222 (2/9) |
| multi3 | 1.000 (1/1) | 0.000 (0/9) |
| direct | 1.000 (1/1) | 0.111 (1/9) |

| Category | n | direct | indep3 | critique3 | multi3 | disagree |
|---|---|---|---|---|---|---|
| ProtocolQA | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |
| SeqQA | 2 | 0.50 | 0.50 | 0.00 | 1.00 | 0.50 |
| DbQA | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |
| LitQA2 | 2 | 1.00 | 1.00 | 0.50 | 1.00 | 0.00 |
| SeqQA2 | 2 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |

Single independent sample acc: 0.933; any-of-3 correct (oracle): 1.000
Critique revision: {"rescue": {"rate": null, "n": 0, "k": 0}, "corruption": {"rate": 0.3, "n": 10, "k": 3}, "initial_acc": 1.0}
Multi-agent adjudication: {"scientists_disagree": 2, "researcher_acc": 0.9, "skeptic_acc": 0.9, "adjudicator_acc_when_disagree": {"rate": 1.0, "n": 2, "k": 2}, "either_scientist_correct_when_disagree": {"rate": 1.0, "n": 2, "k": 2}, "adjudicator_overrides_agreement": 0}
