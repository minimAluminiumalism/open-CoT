# arXiv:2609.26637 — Forced-Reasoning 复现

[English](README.md) | 简体中文

复现 **《Capable yet Parsimonious: Extracting and Characterizing Hidden
Chain-of-Thought in Frontier Models》**（Luo 等，2026）。

协议要点：注册哑工具 `forced-reasoning(reasoning: string)`，首轮以命名
`tool_choice` 强制调用，记录 `reasoning` 参数，以固定 `Received` 回执返回，
随后恢复自动工具选择直至模型给出最终答案。本实现基于 OpenAI
Responses API。

## 文件

```
forced_reasoning/
  client.py     纯标准库 Responses API 客户端（OPENAI_API_KEY / OPENAI_BASE_URL）
  prompts.py    工具描述原文（default / maximal / think-here）
  protocol.py   协议主循环 -> run_session()
  problems.py   10 道竞赛题 + 程序化验证器 + 判分器
scripts/
  replay_cot.py   单会话驱动
  run_batch.py    题目 × {sol, astra} × {强制, 对照} 矩阵
  run_ladder.py   astra effort 阶梯（low/high/xhigh）+ continue 回执变体
results/          全部 90 次运行的原始 JSON
```

## 实验配置

| 模型 | `reasoning.effort` | 工具描述 |
|---|---|---|
| gpt-5.6-sol | `none` | maximal-deliberation（Box 1） |
| gpt-6-astra | `low` | think-here（Box 5） |

## 结果摘要

10 道已验证题目上的正确数（强制组含两轮）：

| | 对照 | 强制 |
|---|---|---|
| gpt-5.6-sol (effort none) | 9/10 | 19/20 |
| gpt-6-astra (effort low) | 8/10 | 20/20 |

全部强制会话均恰好一次工具调用；Sol 的所有强制运行在每一轮都报告
`reasoning_tokens = 0`；三次观察到最终答案与轨迹自身结论不一致。

详见[完整报告](../../docs/arxiv-2609.26637/report.zh-CN.html)，含 effort
阶梯、轨迹统计与一致性分析。
