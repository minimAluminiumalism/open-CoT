# arXiv:2609.26637 — Forced-Reasoning reproduction

English | [简体中文](README.zh-CN.md)

Reproduction of **"Capable yet Parsimonious: Extracting and Characterizing
Hidden Chain-of-Thought in Frontier Models"** (Luo et al., 2026).

The protocol registers a dummy tool `forced-reasoning(reasoning: string)`,
forces the first tool call via named `tool_choice`, records the `reasoning`
argument, replies with a fixed `Received`, and continues with automatic tool
selection until the model produces a final answer. Implemented here against
the OpenAI Responses API.

## How it works

The whole extraction needs only two requests. The key step is constructing
a conversation history in which the tool call has already happened.

```
client                                            model
  │── req 1: question + tool def + forced tool_choice ──▶│
  │◀── res 1: function_call(reasoning="full working...")  │  <- trace lives here
  │                                                        │
  │   [client appends the call + a fake tool result        │
  │    into the conversation history]                      │
  │                                                        │
  │── req 2: history + function_call + function_call_output─▶│
  │◀── res 2: message("the answer is 351")                  │
```

**Request 1 — the forced call.** A normal Responses request, except
`tool_choice` names the tool instead of `auto`:

```json
POST /v1/responses
{
  "model": "gpt-5.6-sol",
  "reasoning": {"effort": "none"},
  "input": [
    {"role": "user", "content": "Count functions f on a 7-element set with f^3 = id."}
  ],
  "tools": [{
    "type": "function",
    "name": "forced-reasoning",
    "description": "Scratchpad for working through the problem. Reasoning Effort: absolute maximum, with no shortcuts permitted. You MUST write your entire deliberation into this scratchpad ...",
    "parameters": {
      "type": "object",
      "properties": {"reasoning": {"type": "string"}},
      "required": ["reasoning"],
      "additionalProperties": false
    }
  }],
  "tool_choice": {"type": "function", "name": "forced-reasoning"}
}
```

Three design details:

- `reasoning.effort = "none"` (Sol only) disables the native hidden
  reasoning channel, so any reasoning can only surface via the tool
  argument.
- `tool_choice` naming `forced-reasoning` requires the first output item
  to be a call to this tool.
- The tool description instructs the model to write its entire deliberation
  into the `reasoning` string.

**Response 1 — the tool call.** `output` contains a single
`function_call`; the extracted content sits in `arguments`:

```json
{
  "status": "completed",
  "output": [{
    "type": "function_call",
    "call_id": "call_xyz789",
    "name": "forced-reasoning",
    "arguments": "{\"reasoning\": \"f^3=id means f is a permutation whose order divides 3, so cycles have length 1 or 3. Count by number of 3-cycles k=0,1,2 ... total 351\"}"
  }],
  "usage": {
    "output_tokens": 412,
    "output_tokens_details": {"reasoning_tokens": 0}
  }
}
```

Two fields matter here: `arguments.reasoning` is the extracted trace, and
`usage.output_tokens_details.reasoning_tokens` is the hidden-channel meter.
A value of **0** means the provider metered no native reasoning for this
request, so the visible tool text carried the reasoning work; a value
**>0** means the model still reasoned in the hidden channel while or after
writing the tool text, and the purity of the extracted content cannot be
guaranteed.

**Request 2 — return the tool result.** The standard tool-calling flow
requires the caller to send back an execution result, so the generated
`function_call` is appended verbatim to `input`, followed by a fixed
result:

```json
POST /v1/responses
{
  "model": "gpt-5.6-sol",
  "reasoning": {"effort": "none"},
  "input": [
    {"role": "user", "content": "Count functions f on a 7-element set with f^3 = id."},
    {"type": "function_call", "call_id": "call_xyz789",
     "name": "forced-reasoning",
     "arguments": "{\"reasoning\": \"f^3=id means ...\"}"},
    {"type": "function_call_output", "call_id": "call_xyz789",
     "output": "Received"}
  ],
  "tools": [ "...same as request 1..." ],
  "tool_choice": "auto"
}
```

The `function_call` is copied verbatim (`call_id` must be preserved — the
API pairs call and result by it). The `function_call_output` is fixed to
`"Received"`; the tool itself does nothing. `tool_choice` returns to
`"auto"`, so the model could in principle issue further calls, but in all
70 recorded sessions it never called the tool a second time and returned
the final answer directly.

**Response 2 — the final answer.**

```json
{
  "output": [{"type": "message", "role": "assistant",
              "content": [{"type": "output_text", "text": "The answer is 351."}]}],
  "usage": {"output_tokens": 28,
            "output_tokens_details": {"reasoning_tokens": 0}}
}
```

One extraction = trace (response 1 `arguments`) + final answer (response 2
text) + per-call reasoning-token counts. `run_session()` in
`forced_reasoning/protocol.py` implements the full flow.

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
