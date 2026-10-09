# open-cot

[English](README.md) | 简体中文

面向闭源前沿模型（GPT、Claude 等不通过 API 暴露原生推理的模型）的
思维链（CoT）提取方法复现合集。

## 论文索引

| arXiv | 标题 | 方法 | 测试模型 | 状态 |
|---|---|---|---|---|
| [2609.26637](https://arxiv.org/abs/2609.26637) | Capable yet Parsimonious: Extracting and Characterizing Hidden Chain-of-Thought in Frontier Models | Forced-Reasoning（强制 tool_choice 的哑工具） | gpt-5.6-sol、gpt-6-astra | [已复现](papers/arxiv-2609.26637/) · [报告](docs/arxiv-2609.26637/report.zh-CN.html) |

## 快速开始

零依赖——仅需 Python 3.10+ 标准库。

```bash
export OPENAI_API_KEY=sk-...                     # 必填
export OPENAI_BASE_URL=https://...               # 可选，任何 OpenAI 兼容端点

# 单次强制推理会话
python papers/arxiv-2609.26637/scripts/replay_cot.py \
    gpt-5.6-sol none maximal "Let S = {1,...,1000}. Count subsets whose sum is divisible by 5."

# 完整基准矩阵（10 道可验证题目 × 2 模型 × 强制/对照）
python papers/arxiv-2609.26637/scripts/run_batch.py

# Astra effort 阶梯 + 回执变体
python papers/arxiv-2609.26637/scripts/run_ladder.py
```

## 主要结论（arXiv:2609.26637）

在 10 道程序化验证的竞赛级题目上、共 90 次调用测得：

- 两个模型都会把实质推理写进强制工具的参数；**gpt-5.6-sol 在全部
  20 次强制运行中 reasoning tokens 恒为零**。
- 强制协议在两个模型上的正确率均不低于无工具对照
  （Sol 9→10、Astra 8→10；Astra 强制总计 50/50）。
- **协议循环实际上从不循环**——70 次强制会话全部恰好一次工具调用，
  模型一次写完所有推理。
- **轨迹-答案脱钩真实存在**：三次出现最终答案与轨迹自身结论不一致，
  例如轨迹以 491 收尾而可见答案给出正确的 351。
- Astra 偶尔只写提纲式占位文本来应付强制调用，随后在原生通道中完成
  实质推理（回答轮 reasoning_tokens > 0）——在最难的题目上约占三分之一。

详见：[docs/arxiv-2609.26637/report.zh-CN.html](docs/arxiv-2609.26637/report.zh-CN.html)
（[pdf](docs/arxiv-2609.26637/report.zh-CN.pdf)）·
[English](docs/arxiv-2609.26637/report.en.html)
（[pdf](docs/arxiv-2609.26637/report.en.pdf)）

## 目录结构

```
papers/arxiv-2609.26637/   每篇论文一个目录
  forced_reasoning/        可复用协议库（client/prompts/protocol/problems）
  scripts/                 replay_cot.py · run_batch.py · run_ladder.py
  results/                 原始 JSON 记录（90 次运行）
docs/arxiv-2609.26637/     详细报告（中 / 英）
```

## 责任使用

这些技术以测量与研究为目的公开。原论文在发表前已向 OpenAI 与
Anthropic 进行披露；提取文本是内部推理的代理而非原始 CoT。
请遵守你所指向端点的服务条款。

## 许可证

MIT
