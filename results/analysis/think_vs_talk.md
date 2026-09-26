# Think longer, not together (first 30 main questions)

## Flash-Lite
| arm | acc | generated tok/q |
|---|---|---|
| direct@low | 0.700 | 478 |
| direct@high | 0.667 | 2539 |
| indep3@low | 0.700 | 1141 |
| critique3@low | 0.633 | 1004 |
| multi3@low | 0.667 | 1440 |
- Direct@high − indep3@low: -0.033 [-0.200, +0.133], McNemar p=1.000
- Direct@high − critique3@low: +0.033 [-0.100, +0.200], McNemar p=1.000
- Direct@high − multi3@low: +0.000 [-0.167, +0.167], McNemar p=1.000

## GPT-6 Luna
| arm | acc | generated tok/q |
|---|---|---|
| direct@low | 0.467 | 115 |
| direct@high | 0.600 | 1839 |
| indep3@low | 0.533 | 341 |
| indep3@high | 0.633 | 6016 |
| critique3@low | 0.533 | 217 |
| critique3@high | 0.633 | 5267 |
| multi3@low | 0.600 | 280 |
| multi3@high | 0.633 | 5809 |
- Direct@high − indep3@low: +0.067 [-0.100, +0.267], McNemar p=0.727
- Direct@high − critique3@low: +0.067 [-0.133, +0.267], McNemar p=0.754
- Direct@high − multi3@low: +0.000 [-0.167, +0.200], McNemar p=1.000
- indep3@high − Direct@high: +0.033 [-0.067, +0.133], p=1.000
- critique3@high − Direct@high: +0.033 [-0.100, +0.167], p=1.000
- multi3@high − Direct@high: +0.033 [-0.067, +0.167], p=1.000

## GPT-6 Sol
| arm | acc | generated tok/q |
|---|---|---|
| direct@high | 0.700 | 3228 |
| indep3@high | 0.700 | 8753 |
- indep3@high − Direct@high: +0.000 [-0.100, +0.100], p=1.000

## GPT-OSS-120B
| arm | acc | generated tok/q |
|---|---|---|
| direct@low | 0.500 | 284 |
| indep3@low | 0.500 | 836 |
| critique3@low | 0.367 | 945 |
| multi3@low | 0.467 | 1040 |

## Gemma 4 31B
| arm | acc | generated tok/q |
|---|---|---|
| direct@low | 0.633 | 520 |
| indep3@low | 0.633 | 1490 |
| critique3@low | 0.567 | 884 |
| multi3@low | 0.667 | 1378 |
