#!/usr/bin/env python3
"""Astra effort ladder: low / high / xhigh + a 'continue in scratchpad' ack variant."""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forced_reasoning import DESC_THINK_HERE, ResponsesClient, run_session
from forced_reasoning.problems import PROBLEMS, ground_truth, judge

ACK_CONTINUE = ("Received. If the problem is not fully worked out yet, keep working "
                "in the scratchpad with another call; only answer when done.")

OUTDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "results")


def work(job):
    p, effort, ack, tag = job
    r = run_session(ResponsesClient(), "gpt-6-astra", effort, p["q"],
                    description=DESC_THINK_HERE, ack=ack)
    r["problem"] = p["id"]
    r["correct"] = judge(r["answer"], p, p["expect"])
    name = f"{p['id']}_astra_{tag}"
    with open(os.path.join(OUTDIR, f"{name}.json"), "w") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    rt = [c["reasoning_tokens"] or 0 for c in r["calls"]]
    nfc = sum(t == "function_call" for c in r["calls"] for t in c["output_types"])
    print(f"[done] {name:36s} calls={len(r['calls'])} fc={nfc} "
          f"trace={sum(len(t) for t in r['traces']):6d} rt={rt} "
          f"ok={r['correct']} err={r['error']}", flush=True)


def main():
    for p in PROBLEMS:
        p["expect"] = ground_truth(p)
    jobs = []
    for p in PROBLEMS:
        jobs.append((p, "high", "Received", "high"))
        jobs.append((p, "xhigh", "Received", "xhigh"))
        jobs.append((p, "low", ACK_CONTINUE, "low_cont"))
    os.makedirs(OUTDIR, exist_ok=True)
    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(work, jobs))
    print("LADDER DONE")


if __name__ == "__main__":
    main()
