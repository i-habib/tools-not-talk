# Results (main)

## flash-lite  (n = 75 questions)

| Strategy | Acc | 95% CI | tokens/q | out tok/q | correct/Mtok | trunc | parse-fail |
|---|---|---|---|---|---|---|---|
| Direct (1 call) | 0.613 | [0.507, 0.720] | 1134 | 464 | 541 | 0 | 0 |
| Independent×3 (vote) | 0.627 | [0.520, 0.733] | 3143 | 1131 | 199 | 2 | 3 |
| Solve→Critique→Revise | 0.560 | [0.453, 0.667] | 3179 | 841 | 176 | 0 | 0 |
| Two scientists + adjudicator | 0.573 | [0.467, 0.680] | 3609 | 1347 | 159 | 0 | 0 |

| Paired contrast | Δacc | 95% CI | A-only | B-only | McNemar p |
|---|---|---|---|---|---|
| multi3-indep3 | -0.053 | [-0.133, +0.013] | 2 | 6 | 0.289 |
| critique3-indep3 | -0.067 | [-0.173, +0.040] | 7 | 12 | 0.359 |
| indep3-direct | +0.013 | [-0.040, +0.067] | 3 | 2 | 1.000 |
| multi3-direct | -0.040 | [-0.107, +0.027] | 2 | 5 | 0.453 |
| critique3-direct | -0.053 | [-0.160, +0.053] | 6 | 10 | 0.454 |
| multi3-critique3 | +0.013 | [-0.093, +0.120] | 9 | 8 | 1.000 |

**Disagreement subset** (independent samples not unanimous): 20 / 75 (27%)

| Strategy | acc on disagreement | acc on unanimous |
|---|---|---|
| Direct (1 call) | 0.300 (6/20) | 0.727 (40/55) |
| Independent×3 (vote) | 0.350 (7/20) | 0.727 (40/55) |
| Solve→Critique→Revise | 0.250 (5/20) | 0.673 (37/55) |
| Two scientists + adjudicator | 0.350 (7/20) | 0.655 (36/55) |

| vs Independent×3 vote | rescue P(correct | vote wrong) | corruption P(wrong | vote right) |
|---|---|---|
| critique3 | 0.250 (7/28) | 0.255 (12/47) |
| multi3 | 0.071 (2/28) | 0.128 (6/47) |
| direct | 0.071 (2/28) | 0.064 (3/47) |

| Category | n | direct | indep3 | critique3 | multi3 | disagree |
|---|---|---|---|---|---|---|
| ProtocolQA | 15 | 0.67 | 0.80 | 0.87 | 0.73 | 0.27 |
| SeqQA | 15 | 0.73 | 0.73 | 0.53 | 0.67 | 0.13 |
| DbQA | 15 | 0.40 | 0.40 | 0.40 | 0.33 | 0.27 |
| LitQA2 | 15 | 0.60 | 0.53 | 0.53 | 0.47 | 0.27 |
| SeqQA2 | 15 | 0.67 | 0.67 | 0.47 | 0.67 | 0.40 |

Single independent sample acc: 0.618; any-of-3 correct (oracle): 0.693
Critique revision: {"rescue": {"rate": 0.1935483870967742, "n": 31, "k": 6}, "corruption": {"rate": 0.18181818181818182, "n": 44, "k": 8}, "initial_acc": 0.5866666666666667}
Multi-agent adjudication: {"scientists_disagree": 21, "researcher_acc": 0.5866666666666667, "skeptic_acc": 0.6, "adjudicator_acc_when_disagree": {"rate": 0.19047619047619047, "n": 21, "k": 4}, "either_scientist_correct_when_disagree": {"rate": 0.5238095238095238, "n": 21, "k": 11}, "adjudicator_overrides_agreement": 0}
