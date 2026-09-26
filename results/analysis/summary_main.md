# Results (main)

## gpt-oss-120b  (n = 118 questions)

| Strategy | Acc | 95% CI | tokens/q | out tok/q | correct/Mtok | trunc | parse-fail |
|---|---|---|---|---|---|---|---|
| Direct (1 call) | 0.466 | [0.381, 0.559] | 985 | 251 | 473 | 0 | 1 |
| Independent×3 (vote) | 0.475 | [0.381, 0.568] | 2909 | 708 | 163 | 0 | 3 |
| Solve→Critique→Revise | 0.441 | [0.347, 0.534] | 3210 | 753 | 137 | 0 | 4 |
| Two scientists + adjudicator | 0.492 | [0.398, 0.585] | 3195 | 810 | 154 | 0 | 0 |

| Paired contrast | Δacc | 95% CI | A-only | B-only | McNemar p |
|---|---|---|---|---|---|
| multi3-indep3 | +0.017 | [-0.059, +0.093] | 12 | 10 | 0.832 |
| critique3-indep3 | -0.034 | [-0.136, +0.068] | 17 | 21 | 0.627 |
| indep3-direct | +0.008 | [-0.051, +0.068] | 7 | 6 | 1.000 |
| multi3-direct | +0.025 | [-0.059, +0.110] | 14 | 11 | 0.690 |
| critique3-direct | -0.025 | [-0.127, +0.076] | 17 | 20 | 0.743 |
| multi3-critique3 | +0.051 | [-0.042, +0.144] | 18 | 12 | 0.362 |

**Disagreement subset** (independent samples not unanimous): 45 / 118 (38%)

| Strategy | acc on disagreement | acc on unanimous |
|---|---|---|
| Direct (1 call) | 0.311 (14/45) | 0.562 (41/73) |
| Independent×3 (vote) | 0.289 (13/45) | 0.589 (43/73) |
| Solve→Critique→Revise | 0.289 (13/45) | 0.534 (39/73) |
| Two scientists + adjudicator | 0.333 (15/45) | 0.589 (43/73) |

| vs Independent×3 vote | rescue P(correct | vote wrong) | corruption P(wrong | vote right) |
|---|---|---|
| critique3 | 0.274 (17/62) | 0.375 (21/56) |
| multi3 | 0.194 (12/62) | 0.179 (10/56) |
| direct | 0.097 (6/62) | 0.125 (7/56) |

| Category | n | direct | indep3 | critique3 | multi3 | disagree |
|---|---|---|---|---|---|---|
| ProtocolQA | 24 | 0.62 | 0.50 | 0.46 | 0.50 | 0.33 |
| SeqQA | 24 | 0.62 | 0.67 | 0.42 | 0.62 | 0.33 |
| DbQA | 23 | 0.39 | 0.43 | 0.48 | 0.35 | 0.35 |
| LitQA2 | 23 | 0.22 | 0.26 | 0.43 | 0.39 | 0.48 |
| SeqQA2 | 24 | 0.46 | 0.50 | 0.42 | 0.58 | 0.42 |

Single independent sample acc: 0.472; any-of-3 correct (oracle): 0.568
Critique revision: {"rescue": {"rate": 0.26229508196721313, "n": 61, "k": 16}, "corruption": {"rate": 0.3684210526315789, "n": 57, "k": 21}, "initial_acc": 0.4830508474576271}
Multi-agent adjudication: {"scientists_disagree": 44, "researcher_acc": 0.4915254237288136, "skeptic_acc": 0.4745762711864407, "adjudicator_acc_when_disagree": {"rate": 0.29545454545454547, "n": 44, "k": 13}, "either_scientist_correct_when_disagree": {"rate": 0.5, "n": 44, "k": 22}, "adjudicator_overrides_agreement": 3}

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
