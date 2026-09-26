# Results (main)

## gpt-oss-120b  (n = 150 questions)

| Strategy | Acc | 95% CI | tokens/q | out tok/q | correct/Mtok | trunc | parse-fail |
|---|---|---|---|---|---|---|---|
| Direct (1 call) | 0.467 | [0.387, 0.547] | 959 | 257 | 487 | 1 | 2 |
| Independent×3 (vote) | 0.493 | [0.413, 0.573] | 2842 | 737 | 174 | 3 | 6 |
| Solve→Critique→Revise | 0.427 | [0.347, 0.507] | 3130 | 771 | 136 | 2 | 5 |
| Two scientists + adjudicator | 0.473 | [0.393, 0.553] | 3125 | 837 | 151 | 3 | 1 |

| Paired contrast | Δacc | 95% CI | A-only | B-only | McNemar p |
|---|---|---|---|---|---|
| multi3-indep3 | -0.020 | [-0.087, +0.047] | 12 | 15 | 0.701 |
| critique3-indep3 | -0.067 | [-0.153, +0.020] | 18 | 28 | 0.184 |
| indep3-direct | +0.027 | [-0.027, +0.080] | 11 | 7 | 0.481 |
| multi3-direct | +0.007 | [-0.060, +0.080] | 15 | 14 | 1.000 |
| critique3-direct | -0.040 | [-0.127, +0.047] | 20 | 26 | 0.461 |
| multi3-critique3 | +0.047 | [-0.033, +0.127] | 22 | 15 | 0.324 |

**Disagreement subset** (independent samples not unanimous): 57 / 150 (38%)

| Strategy | acc on disagreement | acc on unanimous |
|---|---|---|
| Direct (1 call) | 0.316 (18/57) | 0.559 (52/93) |
| Independent×3 (vote) | 0.333 (19/57) | 0.591 (55/93) |
| Solve→Critique→Revise | 0.263 (15/57) | 0.527 (49/93) |
| Two scientists + adjudicator | 0.281 (16/57) | 0.591 (55/93) |

| vs Independent×3 vote | rescue P(correct | vote wrong) | corruption P(wrong | vote right) |
|---|---|---|
| critique3 | 0.237 (18/76) | 0.378 (28/74) |
| multi3 | 0.158 (12/76) | 0.203 (15/74) |
| direct | 0.092 (7/76) | 0.149 (11/74) |

| Category | n | direct | indep3 | critique3 | multi3 | disagree |
|---|---|---|---|---|---|---|
| ProtocolQA | 30 | 0.57 | 0.50 | 0.43 | 0.47 | 0.33 |
| SeqQA | 30 | 0.63 | 0.67 | 0.43 | 0.60 | 0.33 |
| DbQA | 30 | 0.47 | 0.47 | 0.43 | 0.37 | 0.37 |
| LitQA2 | 30 | 0.20 | 0.30 | 0.40 | 0.37 | 0.43 |
| SeqQA2 | 30 | 0.47 | 0.53 | 0.43 | 0.57 | 0.43 |

Single independent sample acc: 0.480; any-of-3 correct (oracle): 0.573
Critique revision: {"rescue": {"rate": 0.2236842105263158, "n": 76, "k": 17}, "corruption": {"rate": 0.36486486486486486, "n": 74, "k": 27}, "initial_acc": 0.49333333333333335}
Multi-agent adjudication: {"scientists_disagree": 54, "researcher_acc": 0.4866666666666667, "skeptic_acc": 0.48, "adjudicator_acc_when_disagree": {"rate": 0.25925925925925924, "n": 54, "k": 14}, "either_scientist_correct_when_disagree": {"rate": 0.5, "n": 54, "k": 27}, "adjudicator_overrides_agreement": 4}

## gemma-4-31b  (n = 150 questions)

| Strategy | Acc | 95% CI | tokens/q | out tok/q | correct/Mtok | trunc | parse-fail |
|---|---|---|---|---|---|---|---|
| Direct (1 call) | 0.487 | [0.407, 0.567] | 1079 | 452 | 451 | 7 | 7 |
| Independent×3 (vote) | 0.487 | [0.407, 0.567] | 3280 | 1399 | 148 | 30 | 30 |
| Solve→Critique→Revise | 0.473 | [0.393, 0.553] | 3825 | 869 | 124 | 12 | 5 |
| Two scientists + adjudicator | 0.573 | [0.493, 0.653] | 4231 | 1285 | 136 | 25 | 4 |

| Paired contrast | Δacc | 95% CI | A-only | B-only | McNemar p |
|---|---|---|---|---|---|
| multi3-indep3 | +0.087 | [+0.020, +0.153] | 19 | 6 | 0.015 |
| critique3-indep3 | -0.013 | [-0.073, +0.047] | 10 | 12 | 0.832 |
| indep3-direct | +0.000 | [-0.053, +0.053] | 8 | 8 | 1.000 |
| multi3-direct | +0.087 | [+0.020, +0.153] | 20 | 7 | 0.019 |
| critique3-direct | -0.013 | [-0.067, +0.040] | 8 | 10 | 0.815 |
| multi3-critique3 | +0.100 | [+0.033, +0.167] | 21 | 6 | 0.006 |

**Disagreement subset** (independent samples not unanimous): 63 / 150 (42%)

| Strategy | acc on disagreement | acc on unanimous |
|---|---|---|
| Direct (1 call) | 0.286 (18/63) | 0.632 (55/87) |
| Independent×3 (vote) | 0.270 (17/63) | 0.644 (56/87) |
| Solve→Critique→Revise | 0.254 (16/63) | 0.632 (55/87) |
| Two scientists + adjudicator | 0.444 (28/63) | 0.667 (58/87) |

| vs Independent×3 vote | rescue P(correct | vote wrong) | corruption P(wrong | vote right) |
|---|---|---|
| critique3 | 0.130 (10/77) | 0.164 (12/73) |
| multi3 | 0.247 (19/77) | 0.082 (6/73) |
| direct | 0.104 (8/77) | 0.110 (8/73) |

| Category | n | direct | indep3 | critique3 | multi3 | disagree |
|---|---|---|---|---|---|---|
| ProtocolQA | 30 | 0.57 | 0.57 | 0.60 | 0.70 | 0.20 |
| SeqQA | 30 | 0.57 | 0.57 | 0.67 | 0.73 | 0.47 |
| DbQA | 30 | 0.57 | 0.53 | 0.40 | 0.57 | 0.33 |
| LitQA2 | 30 | 0.33 | 0.30 | 0.33 | 0.37 | 0.47 |
| SeqQA2 | 30 | 0.40 | 0.47 | 0.37 | 0.50 | 0.63 |

Single independent sample acc: 0.482; any-of-3 correct (oracle): 0.593
Critique revision: {"rescue": {"rate": 0.11392405063291139, "n": 79, "k": 9}, "corruption": {"rate": 0.1267605633802817, "n": 71, "k": 9}, "initial_acc": 0.47333333333333333}
Multi-agent adjudication: {"scientists_disagree": 49, "researcher_acc": 0.5133333333333333, "skeptic_acc": 0.52, "adjudicator_acc_when_disagree": {"rate": 0.4489795918367347, "n": 49, "k": 22}, "either_scientist_correct_when_disagree": {"rate": 0.5102040816326531, "n": 49, "k": 25}, "adjudicator_overrides_agreement": 0}

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
