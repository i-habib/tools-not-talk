# Results (main)

## gpt-oss-120b  (n = 105 questions)

| Strategy | Acc | 95% CI | tokens/q | out tok/q | correct/Mtok | trunc | parse-fail |
|---|---|---|---|---|---|---|---|
| Direct (1 call) | 0.457 | [0.362, 0.552] | 996 | 253 | 459 | 0 | 1 |
| Independent×3 (vote) | 0.476 | [0.381, 0.571] | 2909 | 679 | 164 | 0 | 3 |
| Solve→Critique→Revise | 0.448 | [0.352, 0.543] | 3227 | 740 | 139 | 0 | 3 |
| Two scientists + adjudicator | 0.486 | [0.390, 0.581] | 3211 | 798 | 151 | 0 | 0 |

| Paired contrast | Δacc | 95% CI | A-only | B-only | McNemar p |
|---|---|---|---|---|---|
| multi3-indep3 | +0.010 | [-0.076, +0.095] | 11 | 10 | 1.000 |
| critique3-indep3 | -0.029 | [-0.143, +0.086] | 17 | 20 | 0.743 |
| indep3-direct | +0.019 | [-0.048, +0.086] | 7 | 5 | 0.774 |
| multi3-direct | +0.029 | [-0.057, +0.114] | 13 | 10 | 0.678 |
| critique3-direct | -0.010 | [-0.124, +0.105] | 17 | 18 | 1.000 |
| multi3-critique3 | +0.038 | [-0.057, +0.133] | 16 | 12 | 0.572 |

**Disagreement subset** (independent samples not unanimous): 39 / 105 (37%)

| Strategy | acc on disagreement | acc on unanimous |
|---|---|---|
| Direct (1 call) | 0.308 (12/39) | 0.545 (36/66) |
| Independent×3 (vote) | 0.308 (12/39) | 0.576 (38/66) |
| Solve→Critique→Revise | 0.333 (13/39) | 0.515 (34/66) |
| Two scientists + adjudicator | 0.333 (13/39) | 0.576 (38/66) |

| vs Independent×3 vote | rescue P(correct | vote wrong) | corruption P(wrong | vote right) |
|---|---|---|
| critique3 | 0.309 (17/55) | 0.400 (20/50) |
| multi3 | 0.200 (11/55) | 0.200 (10/50) |
| direct | 0.091 (5/55) | 0.140 (7/50) |

| Category | n | direct | indep3 | critique3 | multi3 | disagree |
|---|---|---|---|---|---|---|
| ProtocolQA | 21 | 0.62 | 0.52 | 0.48 | 0.52 | 0.29 |
| SeqQA | 21 | 0.57 | 0.62 | 0.38 | 0.57 | 0.33 |
| DbQA | 21 | 0.33 | 0.38 | 0.43 | 0.29 | 0.38 |
| LitQA2 | 21 | 0.24 | 0.29 | 0.48 | 0.43 | 0.52 |
| SeqQA2 | 21 | 0.52 | 0.57 | 0.48 | 0.62 | 0.33 |

Single independent sample acc: 0.470; any-of-3 correct (oracle): 0.562
Critique revision: {"rescue": {"rate": 0.3018867924528302, "n": 53, "k": 16}, "corruption": {"rate": 0.40384615384615385, "n": 52, "k": 21}, "initial_acc": 0.49523809523809526}
Multi-agent adjudication: {"scientists_disagree": 37, "researcher_acc": 0.5047619047619047, "skeptic_acc": 0.47619047619047616, "adjudicator_acc_when_disagree": {"rate": 0.2702702702702703, "n": 37, "k": 10}, "either_scientist_correct_when_disagree": {"rate": 0.5135135135135135, "n": 37, "k": 19}, "adjudicator_overrides_agreement": 3}

## gemma-4-31b  (n = 127 questions)

| Strategy | Acc | 95% CI | tokens/q | out tok/q | correct/Mtok | trunc | parse-fail |
|---|---|---|---|---|---|---|---|
| Direct (1 call) | 0.488 | [0.402, 0.575] | 1091 | 464 | 448 | 7 | 7 |
| Independent×3 (vote) | 0.496 | [0.409, 0.583] | 3233 | 1353 | 153 | 24 | 24 |
| Solve→Critique→Revise | 0.457 | [0.370, 0.543] | 3766 | 839 | 121 | 11 | 5 |
| Two scientists + adjudicator | 0.567 | [0.480, 0.654] | 4172 | 1249 | 136 | 19 | 2 |

| Paired contrast | Δacc | 95% CI | A-only | B-only | McNemar p |
|---|---|---|---|---|---|
| multi3-indep3 | +0.071 | [+0.000, +0.142] | 15 | 6 | 0.078 |
| critique3-indep3 | -0.039 | [-0.103, +0.024] | 7 | 12 | 0.359 |
| indep3-direct | +0.008 | [-0.055, +0.063] | 8 | 7 | 1.000 |
| multi3-direct | +0.079 | [+0.000, +0.157] | 17 | 7 | 0.064 |
| critique3-direct | -0.031 | [-0.087, +0.024] | 5 | 9 | 0.424 |
| multi3-critique3 | +0.110 | [+0.039, +0.181] | 18 | 4 | 0.004 |

**Disagreement subset** (independent samples not unanimous): 54 / 127 (43%)

| Strategy | acc on disagreement | acc on unanimous |
|---|---|---|
| Direct (1 call) | 0.315 (17/54) | 0.616 (45/73) |
| Independent×3 (vote) | 0.315 (17/54) | 0.630 (46/73) |
| Solve→Critique→Revise | 0.241 (13/54) | 0.616 (45/73) |
| Two scientists + adjudicator | 0.463 (25/54) | 0.644 (47/73) |

| vs Independent×3 vote | rescue P(correct | vote wrong) | corruption P(wrong | vote right) |
|---|---|---|
| critique3 | 0.109 (7/64) | 0.190 (12/63) |
| multi3 | 0.234 (15/64) | 0.095 (6/63) |
| direct | 0.109 (7/64) | 0.127 (8/63) |

| Category | n | direct | indep3 | critique3 | multi3 | disagree |
|---|---|---|---|---|---|---|
| ProtocolQA | 26 | 0.54 | 0.54 | 0.58 | 0.65 | 0.23 |
| SeqQA | 26 | 0.62 | 0.62 | 0.62 | 0.77 | 0.42 |
| DbQA | 26 | 0.54 | 0.50 | 0.35 | 0.54 | 0.38 |
| LitQA2 | 25 | 0.28 | 0.28 | 0.32 | 0.32 | 0.48 |
| SeqQA2 | 24 | 0.46 | 0.54 | 0.42 | 0.54 | 0.62 |

Single independent sample acc: 0.486; any-of-3 correct (oracle): 0.606
Critique revision: {"rescue": {"rate": 0.11594202898550725, "n": 69, "k": 8}, "corruption": {"rate": 0.13793103448275862, "n": 58, "k": 8}, "initial_acc": 0.4566929133858268}
Multi-agent adjudication: {"scientists_disagree": 43, "researcher_acc": 0.5118110236220472, "skeptic_acc": 0.5118110236220472, "adjudicator_acc_when_disagree": {"rate": 0.46511627906976744, "n": 43, "k": 20}, "either_scientist_correct_when_disagree": {"rate": 0.5581395348837209, "n": 43, "k": 24}, "adjudicator_overrides_agreement": 0}

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
