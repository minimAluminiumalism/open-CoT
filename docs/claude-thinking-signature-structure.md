# Claude thinking signature 结构与加密分析

---

## 一、概述

Claude 返回的 thinking 块包含 `signature` 字段。该字段为 Base64 编码的 protobuf 外层封装（英文原文为 envelope），内部由「明文 header + 加密载荷」两部分组成：header 承载元数据，包括模型名、块类型、渠道标识，旧格式中还包括时间戳与上下文哈希；载荷是被服务端密钥加密的原始推理文本，客户端无法解密。

外层封装按版本号区分。版本 2（下称 v2）保留丰富的明文元数据，版本 4（下称 v4）几乎清空明文元数据，仅保留块类型。由此得到两条实际可用的判断：对 v2 的 signature，可以直接读出生成它的模型，甚至推断所走的云通道；对 v4 的 signature，唯一可读的语义信息是「thinking 块还是 narration 块」，模型与渠道均读不出。

加密方式无法直接证明，只能依靠结构特征排除。最合理的推断是「96 位 nonce、固定 16 字节认证标签的 AES-256-GCM 信封加密」，但 ChaCha20-Poly1305 同样满足全部可观测特征，无法区分。

---

## 二、结构与字段

**处理流程。** 解码与解析均不需要密钥，只涉及 base64 解码与 protobuf 字段解析，不涉及任何解密。

```
signature 字符串
  └─ base64 解码 ──► 字节流
       └─ 按 protobuf 解析 ──► 外层封装（envelope）
            ├─ 明文 header  ──► 可读元数据
            └─ 密文载荷      ──► 不可解密
```

**嵌套结构。** 外层封装含三个字段，其中 `#2` 为内层消息（inner），inner 内部再分 header 与载荷。

```
外层封装（envelope）
  #1 varint        外层版本号（v2 为 2，v4 为 4；更早的格式没有这个字段）
  #2 inner message 载荷容器
     #1 header     明文元数据
     #2 12 字节    nonce（推断）
     #3 12 字节    nonce（推断）
     #4 48 字节    可能是被主密钥包裹的数据密钥
     #5 N 字节     AEAD 密文，即被加密的 thinking 原文
  #3 varint = 1    结尾常量
```

**逐字节示例。** 样本为 Opus 5.5 的 thinking signature，base64 长度 1180 字符，解码后 884 字节。其 base64 开头 160 字符如下：

```
CAQS7QYKEAgSGAI4AUIIdGhpbmtpbmcSDNAc23Lh8MT0MkgsHBoMR+XH4ofJ1iaQFPkAIjCEZ1xoXrdBHa3jczMeTv/1vfLUxmT+9Pm/INBdst7395nFtPDXxGCECB3F9ztqarYqigZq01CiVurVdZwXDMpE2uTY
```

在 base64 前缀中可直接辨认出 `dGhpbmtpbmc`，即英文单词 `thinking` 的编码结果，由此可知 header 以明文存放。逐字节布局如下：

| 偏移 | 字节 | 对应 base64 片段 | 含义 |
| --- | --- | --- | --- |
| 0–1 | `08 04` | `CAQ` | 外层封装 `#1` = 4，外层版本 |
| 2–4 | `12 ed 06` | `S7QY` | 外层封装 `#2`，长度 877，后面 877 字节是 inner |
| 5–6 | `0a 10` | `KE` | inner `#1`，长度 16，后面 16 字节是 header |
| 7–8 | `08 12` | `AgS` | header `#1` = 18 |
| 9–10 | `18 02` | `GAI` | header `#3` = 2 |
| 11–12 | `38 01` | `4AU` | header `#7` = 1 |
| 13–22 | `42 08` + `thinking` | `IIdGhpbmtpbmc` | header `#8`，长度 8，内容 `thinking` |
| 23–36 | `12 0c` + 12 字节 | `SDNAc23Lh8MT0Mkgs` | inner `#2` |
| 37–50 | `1a 0c` + 12 字节 | `HBoMR+XH4ofJ1iaQ` | inner `#3` |
| 51–100 | `22 30` + 48 字节 | `FPkAIjCEZ1xo...` | inner `#4` |
| 101–103 | `2a 8a 06` | — | inner `#5`，长度 778 |
| 104–881 | 778 字节密文 | — | inner `#5` |
| 882–883 | `18 01` | `GAE=` | 外层封装 `#3` = 1 |

base64 每 4 字符对应 3 字节，字符边界与字段边界不对齐，因此表中 base64 片段只表示大致位置，相邻字段会共用边界字符。

**无需解析即可判定的特征。** 其一，看开头判版本：`CAQS` 为 v4（Opus 5.5、Fable 5.1），`CAIS` 为 v2（Opus 5、Fable 5），以 `E` 开头的是没有版本字段的更早格式（Opus 4.6、4.7、4.8）。其二，看 `#8` 判块类型：`...AUIIdGhpbmtpbmc` 为 `thinking`，`...AUIJbmFycmF0aW9u` 为 `narration`。其三，v4 恒以 `GAE=` 结尾，对应外层封装 `#3` = 1。

**v2 格式字段**（外层封装 `#1` = 2）。样本为 Opus 5 经 Bedrock 路径，header 约 110–170 字节。

| 位置 | 字段 | 观测内容 | 解读 |
| --- | --- | --- | --- |
| header | `#1` varint | 16 | 疑为密钥版本，未确认 |
| header | `#2` varint | 1 | 只在代号路径出现，公开名路径无此字段 |
| header | `#3` varint | 2 | 恒定，疑为算法编号 |
| header | `#5` | 64 字节 | 哈希或 MAC 类数据 |
| header | `#6` str | `claude-honey` / `claude-opus-5` | 明文绑定的模型名 |
| header | `#7` varint | 0 或 1 | 与模型代际对应，见第三节 |
| header | `#8` str | `thinking` / `narration` | 块类型 |
| header | `#11` str | 12 位数字，或 UUID | 代号路径为 12 位数字，公开名路径为 UUID |
| inner | `#2` `#3` | 各 12 字节 | nonce（推断） |
| inner | `#4` | 48 字节 | 疑为被包裹的数据密钥（推断） |
| inner | `#5` | N 字节 | AEAD 密文 |

Fable 5 的 header 比上表更长，另含 `#14`（16 字节）、`#17`（=1）、`#21`（Unix 时间戳）、`#22`（=2）、`#24`（61–70 字节）、`#27`（96 或 160 字节）。其中两项已部分解开：`#21` 的数值换算后正好等于请求发起时刻，可判定为时间戳；`#27` 本身是嵌套 protobuf，其 `#1` 为字符串 `prefix_before_block_v1`，`#2` 与 `#6` 各 32 字节，`#9` = 3，两个 32 字节正是 SHA-256 的摘要长度，结合字段名推测它记录「本块之前那段对话」的哈希，用于把 signature 绑定到具体上下文、防止被复用到别的对话，此为推断，未验证。`#24` 内部主要是小整数与 4 字节值，无可读字符串，含义不明。

**v4 格式字段**（外层封装 `#1` = 4）。Opus 5.5 与 Fable 5.1 的 header 逐字段相同，取值亦一致。

| 位置 | 字段 | 观测内容 | 说明 |
| --- | --- | --- | --- |
| header | `#1` varint | 18 | 常量 |
| header | `#3` varint | 2 | 常量 |
| header | `#7` varint | 1 | 常量 |
| header | `#8` str | `thinking` / `narration` | 唯一的可变字段 |

header 总长 16 字节（thinking）或 17 字节（narration），差 1 字节即 `narration` 与 `thinking` 的字符数之差。一个 v4 header 的完整十六进制为：

```
08 12                             #1 = 18
18 02                             #3 = 2
38 01                             #7 = 1
42 08 74 68 69 6e 6b 69 6e 67     #8 = "thinking"
```

v4 相对 v2 移除的字段为 `#2`、`#5`（64 字节哈希）、`#6`（模型名）、`#11`（渠道 ID）、`#14`、`#17`、`#21`（时间戳）、`#22`、`#24`、`#27`（上下文哈希）。

**两者对照。** v4 中唯一可读的语义信息就是 `#8`。`#1`=18、`#3`=2、`#7`=1 在全部样本中为常量；inner `#2`、`#3`、`#4` 的熵分别为 3.54、3.54、5.41 比特每字节，接近 12 字节与 48 字节随机数据的理论上限（约 3.58、5.58），不含嵌套字符串；`#5` 为密文。在整条解码后的字节流内检索 `claude`、`opus`、`anthropic`、`honey`，零命中。

---

## 三、版本划分与模型代号

| 版本 | 外层封装 `#1` | 代表模型 | header 明文元数据 | 能否认出模型与渠道 |
| --- | --- | --- | --- | --- |
| 更早格式 | 无此字段 | Opus 4.6 / 4.7 / 4.8 | 有，结构最简单 | 能 |
| v2 | 2 | Opus 5、Fable 5 | 最丰富（模型名、账号、时间戳、上下文哈希） | 能 |
| v4 | 4 | Opus 5.5、Fable 5.1 | 仅块类型 | 不能 |

分界依据为模型代际，而非渠道。同一次测试、同一渠道下，Fable 5 输出 v2，Fable 5.1 输出 v4；v4 header 在 nevermore 与 appintheloop 两个渠道上完全一致，因此判断该格式与渠道无关。v4 的「模型名消失」并非解析器提前停止造成的假象，核验方式是用「必须恰好读完整个缓冲区、遇未知 wire type 立即报错」的严格解析器重跑，207 条 Opus 5.5 样本全部通过。

样本覆盖存在缺口：v4 样本全部来自 nevermore 与 appintheloop 两个渠道，没有一条确定走 Bedrock 的 v4 样本，因此不能排除 Bedrock 路径上仍携带 `#6` 或 `#11`。模型名是被移入密文、改为由密钥隐式绑定，还是彻底不再记录，从外部无法判断。

模型代号与公开名称的对应关系如下。

| 公开模型 | Bedrock 路径上的 `#6` | 原生 `/v1/messages` 路径上的 `#6` |
| --- | --- | --- |
| Opus 5 | `claude-honey` | `claude-opus-5` |
| Opus 4.8 | `claude-quince` | `claude-opus-4-8` |
| Fable 5 | `claude-fir` | `claude-fable-5` |

`claude-fir` 是本机数据中新发现的映射，未见于公开资料。`claude-honey` 另有第三方独立证据：AWS 官方示例 notebook 请求 `anthropic.claude-opus-5` 并附带 computer-use beta 时返回 400，报错文本为

```
'claude-honey' does not support tool types: computer_20251124.
```

即 Bedrock 在报错信息中将 Opus 5 自身的名称显示为 `claude-honey`；同一批请求中，Haiku 4.5 的报错显示的是其公开 ID `claude-haiku-4-5-20251001`，可作对照。社区曾于 2026-07-08 观察到 Cursor 模型列表中短暂出现 "Claude Honeycomb EAP"，一般认为即后来的 Opus 5，但 Anthropic 从未确认二者的对应关系，此项仅为推断。

在本机约 1.6 万条真实 signature 上按「请求模型 / `#6` / `#2` / `#11`」四列汇总，结果如下。

| 请求模型 | header `#6` | 条数 | header `#2` | header `#11` |
| --- | --- | --- | --- | --- |
| claude-opus-5 | `claude-honey` | 2802 | 1 | 12 位数字 |
| claude-opus-5 | `claude-opus-5` | 2157 | 无 | UUID |
| claude-opus-4-8 | `claude-quince` | 6423 | 1 | 12 位数字 |
| claude-opus-4-8 | `claude-opus-4-8` | 663 | 无 | UUID |
| claude-fable-5 | `claude-fir` | 551 | 1 | 12 位数字 |
| claude-fable-5 | `claude-fable-5` | 145 | 无 | UUID |
| claude-opus-4-7 | `claude-opus-4-7` | 869 | 无或 1 | 两种都有 |
| claude-opus-5-5 | 无 `#6` | 205 | 无 | 无 |

由此得到三条规律。第一，代号只出现在 `#2` = 1 且 `#11` 为 12 位数字的样本里；公开名那一组 `#11` 为 UUID，且无 `#2`，两组特征高度相关，可作为渠道的可观测标记。第二，该 12 位数字很可能是 AWS 账号 ID，依据是位数吻合、保留前导零（如 `0070xxx4409`）、同一个 ID 会同时出现在 `claude-honey` 与 `claude-quince` 之下（如 `4814xxx6896`、`3304xxx0341`），同一账号调用不同模型比按模型分配更符合账号 ID 的语义，此为推断。第三，「走 Bedrock 必然出代号」并不成立：Opus 4.7 即使 `#11` 带 12 位数字，`#6` 仍是公开名 `claude-opus-4-7`，代号化看起来从 4.8 才开始；另有 1 条请求模型名为 `jp.anthropic.claude-opus-4-8`、但 signature 内 `#6` 为公开名且 `#11` 为 UUID 的样本，可能是中转层做了模型名映射，也可能走的是 Anthropic 自运营的 Claude Platform on AWS 通道，原因无法判定。此外，140 条 appintheloop 渠道下的 claude-opus-5 signature 完全不是这种 protobuf 格式，推测为中转层自行生成或改写，未深入追查。

上述映射可用于渠道核查。signature 中出现 `claude-honey`，说明该请求实际由 Bedrock 上的 Opus 5 生成，即便调用方书写的模型名是别的；若网关配置指向 Anthropic 直连而 signature 显示代号，即为配置与实际路由不一致，应核查渠道配置。出现 `claude-quince` 即 Bedrock 上的 Opus 4.8。此方法对 v4 格式失效。

---

## 四、narration 块

`narration` 是一类被包装成 thinking 块的解说内容。在 API 响应中它的块类型同样为 `type: "thinking"`，只有解码 signature 并查看 header `#8` 才能与普通 thinking 区分。它出现的位置与通常的 `text` 块相同，即模型在发起工具调用前面向用户输出的说明文字；内部推理仍保留在 thinking 块中。

同一轮请求内两条 signature 的并排比较（Opus 5.5，v4）如下。

| 项 | thinking | narration |
| --- | --- | --- |
| base64 长度 | 1180 字符 | 1224 字符 |
| 解码后字节数 | 884 | 917 |
| 外层封装 `#1` | 4 | 4 |
| header 长度 | 16 字节 | 17 字节 |
| header `#8` | `thinking` | `narration` |
| inner `#2` / `#3` / `#4` | 12 / 12 / 48 字节 | 12 / 12 / 48 字节 |
| inner `#5` 密文 | 778 字节 | 810 字节 |

两者结构完全一致，唯一差别是 `#8`，也因此 narration 的所有字段偏移整体后移 1 字节。Fable 5（v2）的对照结果同理。

已确认产生该块类型的模型有三种。

| 模型 | 结论 | 证据 |
| --- | --- | --- |
| claude-fable-5 | 会 | 本机 696 条中 177 条为 narration |
| claude-opus-5-5 | 会 | 本机 23 条，另有实测 2 条 |
| claude-fable-5-1 | 会 | 实测获得 1 条（约 1/30） |
| claude-opus-5 | 未观察到 | 本机 4959 条全部为 thinking |
| claude-opus-4-8 / 4-7 | 未观察到 | 本机合计 7955 条全部为 thinking |

Opus 5 尚不能定论。其 header `#7` 为 1，与三个确认会产生 narration 的模型一致；而 Opus 4.7 与 4.8 全部为 `#7` = 0，且历史数据中从未出现 narration。`#7` 可能是「该模型是否支持 narration 块」之类的标志，但仅凭现有样本不足以定论。

出现条件的可重复规律是：narration 集中出现在工具输出异常之后，模型先在 thinking 中判定输出不完整、不足以采信，再以 narration 向用户说明情况，随即发起下一次工具调用；正常情形下这段说明会以普通 `text` 块输出。出现频率不高且样本量有限，Fable 5.1 约 1/30，Opus 5.5 在相同条件下约 2/11。

---

## 五、长度与加密方式

**长度口径。** 被封存原文的长度为 UTF-8 编码后的字节数，即 `len(text.encode("utf-8"))`，而非字符数；英文占 1 字节，中文一般 3 字节，emoji 通常 4 字节。计算方式为

```
明文字节数 = 密文长度 - 16
```

前例中 inner `#5` 为 778 字节，故原文 762 字节。nonce 单独存放在 inner `#2` 与 `#3`，不占密文长度，因此只需减去认证标签。该公式依赖若干前提：加密确为 AEAD 且标签 16 字节、明文未经压缩、密文内只含原文而无额外包装数据。这些前提在旧格式上已由逐字节还原验证成立，对 v4 尚无独立验证。

**加密方式。** 不能直接证明：signature 中没有任何字段明写算法名称，没有密钥也无法校验认证标签，可做的仅是结构上的排除法。支持「流式 AEAD」的特征有四条。其一，无块填充：13972 条密文长度对 16 取余，余数在 0 到 15 之间均匀分布，各约 800–930 条，若为 CBC、ECB 这类需填充至 16 字节整数倍的模式，余数应完全一致，故为按字节输出的流式模式，GCM、ChaCha20-Poly1305、CTR+MAC 均符合。其二，nonce 长度吻合：inner `#2` 与 `#3` 恒为 12 字节（96 位），正是 GCM 与 ChaCha20-Poly1305 的标准长度，而 CBC 的 IV 为 16 字节，与观测不符。其三，`#4` 恒为 48 字节，恰好等于 32 字节 AES-256 密钥加 16 字节标签，一种自洽的解读是信封加密：先生成随机数据密钥加密 thinking，再用服务端主密钥包裹该数据密钥，两个 12 字节 nonce 分别用于两次加密。其四，密文熵接近每字节 8 位，与随机数据无差别，最短密文 37 字节，大于 16 字节标签开销。

最强的一项证据来自 replay 实验而非 signature 本身：旧格式上让模型在 replay 后逐字复述原文，复述结果的 UTF-8 字节数恰好等于「密文长度 − 16」，Opus 5 上 15 例中有 10 例逐字节吻合。这证明加密开销固定为 16 字节、原文未被压缩，但 ChaCha20-Poly1305 的标签同样为 16 字节，仍无法区分两者。

结论应分层表述：可以确定的是流式 AEAD、每条密文固定 16 字节开销、96 位 nonce、外层另有包裹数据密钥的结构；最可能是 AES-256-GCM 信封加密；无法排除 ChaCha20-Poly1305。

---

## 六、结论的适用边界

**可见文本不能用于推算封存内容。** `display: summarized` 下返回的可见文本是另行生成的摘要，与密文中的原文并非同一份文字，两者的字节数之间不存在固定对应关系。实测差值如下。

| 模型（格式） | 样本数 | 密文长度 − 16 − 可见文本字节数 |
| --- | --- | --- |
| Fable 5（v2） | 177 | −69 至 +595，中位数 +32 |
| Opus 5.5（v4） | 29 | +566 至 +1383，中位数 +664 |
| Fable 5.1（v4） | 1 | +637 |

差值既有正也有负，且分布分散。narration 的可见文本同样经过 summarized 流程，其内容仍被完整加密进 signature，在这一点上应与 thinking 块同等看待。因此封存原文的长度只能由密文长度推算，无法由可见文本反推；v4 的 762 字节系按旧格式规律外推所得，尚无独立验证。

**尚未验证的事项。** 对 v4 而言，「密文长度 − 16 = 原文字节数」尚无验证。此处所指为尚无任何工作对 v4 的 signature 做过 replay 还原，而非 v4 的 signature 里没有长度；长度可直接从 inner `#5` 读出。唯一可行的验证路径是 replay：把 signature 放回请求，让服务端解密并注入上下文，再让模型逐字复述，比对复述结果的 UTF-8 字节数是否恰为密文长度减 16。迄今完成的还原验证均针对旧格式，Fable 5 的尝试被服务端的 `reasoning_extraction` 分类器拦截，未能完成。

此外，`#1`、`#3`、`#4`、`#5`（64 字节）、`#24` 等字段的含义仍属推测；`#2` 与 `#3` 被称为 nonce、`#4` 为被包裹的数据密钥，均依据长度与熵推断，未获官方确认。
