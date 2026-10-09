"""Forced-Reasoning protocol (Responses API implementation).

Per arXiv:2609.26637 App. B:
  1. register forced-reasoning(reasoning: string)
  2. first call: named tool_choice forces the tool
  3. record arguments.reasoning, reply with a fixed ack ("Received")
  4. subsequent calls: tool_choice="auto" until a final message appears
"""
import json
import time

from .prompts import make_tool

DEFAULT_ACK = "Received"


def run_session(client, model, effort, question, description=None,
                mode="forced", ack=DEFAULT_ACK, max_rounds=25,
                max_output_tokens=16000):
    """Run one protocol session.

    mode="forced"  -> register the tool and force the first call
    mode="control" -> no tools, plain request at the same effort
    """
    tools = [make_tool(description)] if mode == "forced" else []
    inp = [{"role": "user", "content": [{"type": "input_text", "text": question}]}]
    traces, calls = [], []
    answer, error = None, None
    first = True
    try:
        for rnd in range(max_rounds):
            body = {"model": model, "input": inp,
                    "reasoning": {"effort": effort},
                    "max_output_tokens": max_output_tokens}
            if tools:
                body["tools"] = tools
                body["tool_choice"] = ({"type": "function",
                                       "name": "forced-reasoning"}
                                       if first else "auto")
            first = False
            t0 = time.time()
            resp = client.create(body)
            out = resp.get("output", [])
            usage = resp.get("usage", {})
            rt = (usage.get("output_tokens_details") or {}).get("reasoning_tokens")
            calls.append({
                "round": rnd,
                "status": resp.get("status"),
                "output_types": [o.get("type") for o in out],
                "output_tokens": usage.get("output_tokens"),
                "reasoning_tokens": rt,
                "sec": round(time.time() - t0, 1),
            })
            fcs = [o for o in out if o.get("type") == "function_call"]
            if not fcs:
                for o in out:
                    if o.get("type") == "message":
                        answer = "".join(c.get("text", "")
                                         for c in o.get("content", []))
                break
            inp = inp + out
            for fc in fcs:
                try:
                    traces.append(json.loads(fc["arguments"])["reasoning"])
                except Exception:
                    traces.append(fc.get("arguments", ""))
                inp.append({"type": "function_call_output",
                            "call_id": fc["call_id"], "output": ack})
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    return {"model": model, "effort": effort, "mode": mode,
            "traces": traces, "calls": calls, "answer": answer,
            "error": error}
