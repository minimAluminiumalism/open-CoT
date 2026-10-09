#!/usr/bin/env python3
"""Run the full benchmark matrix: problems x models x {forced, control}.

Writes one JSON per run into results/ next to this package and prints a
per-run summary line as each finishes.
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forced_reasoning import (DESC_MAXIMAL, DESC_THINK_HERE, ResponsesClient,
                              run_session)
from forced_reasoning.problems import PROBLEMS, ground_truth, judge

OUTDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "results")


def work(job):
    p, model, effort, mode, desc = job
    r = run_session(ResponsesClient(), model, effort, p["q"],
                    description=desc, mode=mode)
    r["problem"] = p["id"]
    r["correct"] = judge(r["answer"], p, p["expect"])
    tag = f"{p['id']}_{model.split('-')[-1]}_{mode}"
    with open(os.path.join(OUTDIR, f"{tag}.json"), "w") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    rt = sum(c["reasoning_tokens"] or 0 for c in r["calls"])
    nfc = sum(t == "function_call" for c in r["calls"] for t in c["output_types"])
    print(f"[done] {tag:38s} calls={len(r['calls'])} fc={nfc} "
          f"trace_chars={sum(len(t) for t in r['traces']):6d} "
          f"rt={rt:5d} correct={r['correct']} err={r['error']}", flush=True)
    return r


def main():
    for p in PROBLEMS:
        p["expect"] = ground_truth(p)
        print(f"  {p['id']:16s} expect={p['expect']}")
    jobs = []
    for p in PROBLEMS:
        jobs.append((p, "gpt-5.6-sol", "none", "forced", DESC_MAXIMAL))
        jobs.append((p, "gpt-5.6-sol", "none", "control", None))
        jobs.append((p, "gpt-6-astra", "low", "forced", DESC_THINK_HERE))
        jobs.append((p, "gpt-6-astra", "low", "control", None))
    os.makedirs(OUTDIR, exist_ok=True)
    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(work, jobs))
    print("ALL DONE")


if __name__ == "__main__":
    main()
