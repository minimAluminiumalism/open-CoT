# open-cot

English | [简体中文](README.zh-CN.md)

Engineering reproductions of methods for eliciting chain-of-thought (CoT)
from closed frontier models — GPT, Claude, and other reasoning models whose
native reasoning is not exposed through the API.

## Papers

| arXiv | Title | Method | Models tested | Status |
|---|---|---|---|---|
| [2609.26637](https://arxiv.org/abs/2609.26637) | Capable yet Parsimonious: Extracting and Characterizing Hidden Chain-of-Thought in Frontier Models | Forced-Reasoning (dummy tool with forced `tool_choice`) | gpt-5.6-sol, gpt-6-astra | [Reproduced](papers/arxiv-2609.26637/) · [Report](docs/arxiv-2609.26637/report.en.html) |

## Quick start

Zero dependencies — Python 3.10+ standard library only.

```bash
export OPENAI_API_KEY=sk-...                     # required
export OPENAI_BASE_URL=https://...               # optional, OpenAI-compatible endpoint

# single forced-reasoning session
python papers/arxiv-2609.26637/scripts/replay_cot.py \
    gpt-5.6-sol none maximal "Let S = {1,...,1000}. Count subsets whose sum is divisible by 5."

# full benchmark matrix (10 verified problems x 2 models x forced/control)
python papers/arxiv-2609.26637/scripts/run_batch.py

# astra effort ladder + ack variant
python papers/arxiv-2609.26637/scripts/run_ladder.py
```

## Headline findings (arXiv:2609.26637)

Measured on 90 calls against 10 competition-level problems with
programmatic ground truth:

- Both models write genuine working into the forced tool argument;
  **gpt-5.6-sol reported zero reasoning tokens on all 20 forced runs**.
- Forced protocol outperformed the no-tool control on both models
  (Sol 9→10, Astra 8→10 problems correct; Astra 50/50 across all forced runs).
- **The protocol loop never actually loops** — all 70 forced sessions used
  exactly one tool call; the model writes everything in a single pass.
- **Trace–answer divergence is real**: three sessions produced a final
  answer inconsistent with the trace's own conclusion, e.g. a trace
  ending in 491 while the visible answer gave the correct 351.
- Astra occasionally writes a plan-only stub to satisfy the forced call,
  then does the real reasoning natively (reasoning_tokens > 0 on the
  answer round) — roughly a third of samples on the hardest problem.

Full details: [docs/arxiv-2609.26637/report.en.html](docs/arxiv-2609.26637/report.en.html)
([pdf](docs/arxiv-2609.26637/report.en.pdf)) ·
[中文](docs/arxiv-2609.26637/report.zh-CN.html)
([pdf](docs/arxiv-2609.26637/report.zh-CN.pdf))

## Repository layout

```
papers/arxiv-2609.26637/   one directory per paper
  forced_reasoning/        reusable protocol library (client/prompts/protocol/problems)
  scripts/                 replay_cot.py · run_batch.py · run_ladder.py
  results/                 raw JSON records (90 runs)
docs/arxiv-2609.26637/     detailed reports (en / zh-CN)
```

## Responsible use

These techniques are published for measurement and research. The source
paper disclosed the method to OpenAI and Anthropic before publication;
the extracted text is a *proxy* for internal reasoning, not raw CoT.
Respect the terms of service of whatever endpoint you point this at.

## License

MIT
