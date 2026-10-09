# arXiv:2609.26637 — Forced-Reasoning reproduction

English | [简体中文](README.zh-CN.md)

Reproduction of **"Capable yet Parsimonious: Extracting and Characterizing
Hidden Chain-of-Thought in Frontier Models"** (Luo et al., 2026).

The protocol registers a dummy tool `forced-reasoning(reasoning: string)`,
forces the first tool call via named `tool_choice`, records the `reasoning`
argument, replies with a fixed `Received`, and continues with automatic tool
selection until the model produces a final answer. Implemented here against
the OpenAI Responses API.

## Files

```
forced_reasoning/
  client.py     stdlib-only Responses API client (OPENAI_API_KEY / OPENAI_BASE_URL)
  prompts.py    verbatim tool descriptions (default / maximal / think-here)
  protocol.py   the protocol loop -> run_session()
  problems.py   10 competition problems + programmatic verifiers + judge
scripts/
  replay_cot.py   single-session driver
  run_batch.py    problems x {sol, astra} x {forced, control} matrix
  run_ladder.py   astra effort ladder (low/high/xhigh) + continue-ack variant
results/          raw JSON for all 90 recorded runs
```

## Configuration used

| Model | `reasoning.effort` | Tool description |
|---|---|---|
| gpt-5.6-sol | `none` | maximal-deliberation (Box 1) |
| gpt-6-astra | `low` | think-here (Box 5) |

## Results snapshot

Correct answers out of 10 verified problems (two rounds for forced):

| | control | forced |
|---|---|---|
| gpt-5.6-sol (effort none) | 9/10 | 19/20 |
| gpt-6-astra (effort low) | 8/10 | 20/20 |

All forced sessions made exactly one tool call. Every Sol forced run
reported `reasoning_tokens = 0` on every round. Three sessions showed the
final answer diverging from the trace's own conclusion.

See the [full report](../../docs/arxiv-2609.26637/report.en.html) for the
effort ladder, trace statistics, and consistency analysis.
