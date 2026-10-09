#!/usr/bin/env python3
"""Run a single Forced-Reasoning session and print the extracted trace.

Usage:
  python replay_cot.py <model> <effort> <desc> <question...>

  model  e.g. gpt-5.6-sol, gpt-6-astra
  effort none | low | medium | high | xhigh
  desc   default | maximal | thinkhere

Examples:
  python replay_cot.py gpt-5.6-sol none maximal "Prove that ..."
  python replay_cot.py gpt-6-astra low thinkhere "Prove that ..."
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forced_reasoning import (DESC_DEFAULT, DESC_MAXIMAL, DESC_THINK_HERE,
                              ResponsesClient, run_session)

DESCS = {"default": DESC_DEFAULT, "maximal": DESC_MAXIMAL,
         "thinkhere": DESC_THINK_HERE}


def main():
    if len(sys.argv) < 5 or sys.argv[3] not in DESCS:
        sys.exit(__doc__)
    model, effort, desc_key = sys.argv[1], sys.argv[2], sys.argv[3]
    question = " ".join(sys.argv[4:])

    r = run_session(ResponsesClient(), model, effort, question,
                    description=DESCS[desc_key])

    print(json.dumps({"calls": r["calls"],
                      "n_trace_chunks": len(r["traces"]),
                      "trace_chars": sum(len(t) for t in r["traces"]),
                      "error": r["error"]}, indent=1))
    for i, t in enumerate(r["traces"]):
        print(f"\n===== trace chunk {i} =====\n{t}")
    if r["answer"]:
        print(f"\n===== answer =====\n{r['answer']}")


if __name__ == "__main__":
    main()
