# arXiv:2609.26637 — Forced-Reasoning 复现

[English](README.md) | 简体中文

复现 **《Capable yet Parsimonious: Extracting and Characterizing Hidden
Chain-of-Thought in Frontier Models》**（Luo 等，2026）。

协议要点：注册哑工具 `forced-reasoning(reasoning: string)`，首轮以命名
`tool_choice` 强制调用，记录 `reasoning` 参数，以固定 `Received` 回执返回，
随后恢复自动工具选择直至模型给出最终答案。本实现基于 OpenAI
Responses API。

## 调用流程

整个提取只需两次请求。关键在于构造一段会话历史，使模型认为
工具调用已经发生。

```
客户端                                          模型
  │── 请求①: 问题 + 工具定义 + 强制 tool_choice ──────▶│
  │◀── 响应①: function_call(reasoning="完整推导...") ──│  ← 轨迹位于此
  │                                                      │
  │   [客户端将工具调用与执行结果追加进会话历史]            │
  │                                                      │
  │── 请求②: 历史 + function_call + function_call_output ─▶│
  │◀── 响应②: message("the answer is 351") ──────────────│
```

**请求①——发起强制调用。** 普通 Responses 请求，区别在于
`tool_choice` 不是 `auto` 而是指定调用该工具：

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

三个关键设计：

- `reasoning.effort = "none"`（仅 Sol 支持）关闭原生隐藏推理通道，
  推理过程只能经由工具参数输出；
- `tool_choice` 指定 `forced-reasoning`，响应的第一个输出项必须是
  该工具的调用；
- 工具 description 要求模型将完整推理过程写入 `reasoning` 字符串。

**响应①——返回工具调用。** `output` 数组仅包含一个
`function_call`，提取目标位于 `arguments` 字段：

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

需要同时读取两个字段：`arguments.reasoning` 是提取到的轨迹文本；
`usage.output_tokens_details.reasoning_tokens` 是隐藏通道计量。
**等于 0** 表示提供商未对该请求计隐藏推理，工具参数文本承担了可见
的推理工作；**大于 0** 表示模型在生成工具文本的同时或之后仍在隐藏
通道中进行了推理，提取内容的纯度无法保证。

**请求②——回传工具结果。** 标准工具调用流程要求调用方将执行结果
返回给模型，因此将刚生成的 `function_call` 原样追加至 `input`，并
追加固定的执行结果：

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
  "tools": [ "...同请求①..." ],
  "tool_choice": "auto"
}
```

`function_call` 逐字复制响应①（`call_id` 必须保留，API 依此配对
调用与结果）；`function_call_output` 的 `output` 固定为
`"Received"`，工具本身不执行任何操作。`tool_choice` 恢复 `"auto"`，
模型理论上可继续发起多轮调用，但在全部 70 次实测会话中均未出现
第二次调用，直接返回最终答案。

**响应②——最终答案。**

```json
{
  "output": [{"type": "message", "role": "assistant",
              "content": [{"type": "output_text", "text": "The answer is 351."}]}],
  "usage": {"output_tokens": 28,
            "output_tokens_details": {"reasoning_tokens": 0}}
}
```

一次完整提取 = 轨迹（响应①的 `arguments`）+ 最终答案（响应②的
消息文本）+ 逐轮 reasoning tokens 计量。`forced_reasoning/protocol.py`
中的 `run_session()` 实现了上述全部逻辑。

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
