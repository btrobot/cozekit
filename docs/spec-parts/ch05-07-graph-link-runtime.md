# Coze 工作流语言规范 — 第 5-7 章

> **版本**: 1.0
> **提取来源**: `coze-studio` 后端验证器 (`canvas_validate.go`)、验证分层标准 (`validation-layers.md`)、编译器语义分析器 (`semantic_pass.py`)
> **对应编译器层级**: Layer 3 (Graph) + Layer 4 (Link) + Layer 5 (Runtime)

---

# 5. 图结构语义分析 (Graph Semantic Analysis)

本章定义基于工作流有向图拓扑结构的静态验证规则。图结构验证仅依赖节点和边的拓扑关系，不需要任何外部定义或运行时环境（Checkability: `OFFLINE`）。

图结构验证在编译器中的执行位置为 `SemanticPass._check_graph_*` 系列方法，对应后端 `ValidateTree` 中的 `ValidateConnections`、`DetectCycles`、`ValidateNestedFlows` 等函数。

## 5.1 连通性检查 (Connectivity)

### 5.1.1 Start 节点必须有出边 (SEMANTIC-BE-001)

Start 节点（ID = `100001`）是工作流的唯一入口。如果 Start 节点没有出边，工作流无法执行任何后续逻辑。

| 属性 | 值 |
|------|-----|
| 规则 ID | `SEMANTIC-BE-001` |
| 错误类别 | `violation` |
| Checkability | `OFFLINE` |
| 后端对应 | `BE-validateConnections-001` — `ValidateConnections` |
| 后端错误消息 | `"node \"start\" not connected"` |
| 源码位置 | `canvas_validate.go:529` |

**算法描述**:

```
1. 查找 ID 为 "100001" 的节点
2. 检查该节点是否存在至少一条以它为 source 的边
3. 如果没有出边，报告 SEMANTIC-BE-001
```

**正确示例**:

```yaml
# ✅ Start 节点有出边
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "llm-1"
    type: "3"
    data:
      nodeMeta:
        title: "LLM"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "llm-1"
  - sourceNodeID: "llm-1"
    targetNodeID: "900001"
```

**错误示例**:

```yaml
# ❌ Start 节点无出边
# 诊断: SEMANTIC-BE-001 — start node must have at least one outgoing edge
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "llm-1"
    type: "3"
    data:
      nodeMeta:
        title: "LLM"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "llm-1"
    targetNodeID: "900001"
# 问题: 没有从 100001 出发的边
```

---

### 5.1.2 非终端节点必须有出边 (SEMANTIC-BE-002)

除 Start、End、Comment 节点外，所有节点必须至少有一条出边。没有出边的节点形成"死节点"，工作流执行到该节点后无法继续。

| 属性 | 值 |
|------|-----|
| 规则 ID | `SEMANTIC-BE-002` |
| 错误类别 | `violation` |
| Checkability | `OFFLINE` |
| 后端对应 | `BE-validateConnections-003` — `ValidateConnections` |
| 后端错误消息 | `"node \"%v\" not connected"` |
| 源码位置 | `canvas_validate.go:559` |

**排除的节点类型**:

| 节点类型 | type ID | 排除原因 |
|---------|---------|---------|
| Start | `"1"` | 入口节点，由 BE-001 单独检查 |
| End | `"2"` | 终端节点，不需要出边 |
| Comment | `"31"` | 视觉注释，不影响执行流 |
| Break | — | 循环中断，由循环上下文处理 |
| Continue | — | 循环继续，由循环上下文处理 |

**算法描述**:

```
1. 遍历画布中所有节点
2. 跳过 type ∈ {Start, End, Comment, Break, Continue} 的节点
3. 对每个节点检查：是否存在以它为 source 的边
4. 如果没有出边，报告 SEMANTIC-BE-002
```

**正确示例**:

```yaml
# ✅ 所有非终端节点都有出边
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "llm-1"
    type: "3"
    data:
      nodeMeta:
        title: "LLM"
  - id: "code-1"
    type: "5"
    data:
      nodeMeta:
        title: "Code"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "llm-1"
  - sourceNodeID: "llm-1"
    targetNodeID: "code-1"
  - sourceNodeID: "code-1"
    targetNodeID: "900001"
```

**错误示例**:

```yaml
# ❌ LLM 节点无出边（死节点）
# 诊断: SEMANTIC-BE-002 — node "llm-1" has no outgoing edges
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "llm-1"
    type: "3"
    data:
      nodeMeta:
        title: "LLM"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "llm-1"
# 问题: llm-1 没有出边连接到后续节点
```

```yaml
# ❌ 节点无入边（孤立节点）
# 诊断: SEMANTIC-BE-002 — node "code-1" has no incoming edges
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "code-1"
    type: "5"
    data:
      nodeMeta:
        title: "Code"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "900001"
# 问题: code-1 既无入边也无出边，是孤立节点
```

---

### 5.1.3 分支端口必须连接 (SEMANTIC-BE-010)

具有分支端口的节点（如 If、Intent）的每个输出端口都必须至少连接一条出边。未连接的分支端口会导致执行路径断裂。

| 属性 | 值 |
|------|-----|
| 规则 ID | `SEMANTIC-BE-010` |
| 错误类别 | `violation` |
| Checkability | `PARTIAL` |
| 后端对应 | `BE-validateConnections-002` — `ValidateConnections` |
| 后端错误消息 | `"node \"%v\"'s port \"%v\" not connected;"` |
| 源码位置 | `canvas_validate.go:538` |

> **NOTE**: Checkability 为 `PARTIAL`，因为静态分析可以检测已声明的端口是否连接，但某些端口（如异常处理端口）的可用性取决于节点的具体配置，需要运行时信息确认。

**分支节点类型及其必需端口**:

| 节点类型 | type ID | 必需端口 | 说明 |
|---------|---------|---------|------|
| If | `"8"` | `true`, `false` | 条件分支的两个出口 |
| Intent | `"22"` | 每个已声明的意图 | 意图匹配节点的各意图出口 |

**算法描述**:

```
1. 遍历画布中所有节点
2. 如果节点是 If 类型:
   a. 收集该节点所有出边的 sourcePortID 集合
   b. 检查集合中是否包含 "true" 和 "false"
   c. 缺失的端口报告 SEMANTIC-BE-010
3. 如果节点是 Intent 类型:
   a. 检查是否有任何出边
   b. 如果没有出边，报告 SEMANTIC-BE-010
```

**正确示例 — If 节点**:

```yaml
# ✅ If 节点的 true 和 false 端口都已连接
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "if-1"
    type: "8"
    data:
      nodeMeta:
        title: "条件判断"
  - id: "llm-true"
    type: "3"
    data:
      nodeMeta:
        title: "True 分支"
  - id: "llm-false"
    type: "3"
    data:
      nodeMeta:
        title: "False 分支"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "if-1"
  - sourceNodeID: "if-1"
    targetNodeID: "llm-true"
    sourcePortID: "true"
  - sourceNodeID: "if-1"
    targetNodeID: "llm-false"
    sourcePortID: "false"
  - sourceNodeID: "llm-true"
    targetNodeID: "900001"
  - sourceNodeID: "llm-false"
    targetNodeID: "900001"
```

**错误示例 — If 节点缺少端口**:

```yaml
# ❌ If 节点只连接了 true 端口，false 端口未连接
# 诊断: SEMANTIC-BE-010 — required branch/exception outgoing ports are not connected: false
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "if-1"
    type: "8"
    data:
      nodeMeta:
        title: "条件判断"
  - id: "llm-true"
    type: "3"
    data:
      nodeMeta:
        title: "True 分支"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "if-1"
  - sourceNodeID: "if-1"
    targetNodeID: "llm-true"
    sourcePortID: "true"
  - sourceNodeID: "llm-true"
    targetNodeID: "900001"
# 问题: 缺少 sourcePortID: "false" 的出边
```

**错误示例 — Intent 节点无出边**:

```yaml
# ❌ Intent 节点无任何出边
# 诊断: SEMANTIC-BE-010 — required branch/exception outgoing ports are not connected: intent
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "intent-1"
    type: "22"
    data:
      nodeMeta:
        title: "意图识别"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "intent-1"
# 问题: intent-1 没有任何出边
```

---

## 5.2 环路检测 (Cycle Detection)

### 5.2.1 禁止有向环 (SEMANTIC-BE-015)

工作流图中不允许存在有向环。环会导致无限循环，使工作流永远无法完成执行。

| 属性 | 值 |
|------|-----|
| 规则 ID | `SEMANTIC-BE-015` |
| 错误类别 | `violation` |
| Checkability | `OFFLINE` |
| 后端对应 | `BE-DetectCycles-001` — `DetectCycles` |
| 后端错误消息 | `"line connections do not allow parallel lines to intersect and form loops with each other"` |
| 源码位置 | `canvas_validate.go:114` |

**算法描述 — DFS 环路检测**:

```
1. 构建邻接表: adjacency[source] = [target1, target2, ...]
2. 初始化: visited = ∅, in_stack = ∅
3. 对每个未访问节点 node_id 执行 DFS:
   a. 如果 node_id ∈ in_stack: 发现环，返回 true
   b. 如果 node_id ∈ visited: 跳过
   c. 标记 visited.add(node_id), in_stack.add(node_id)
   d. 递归访问所有邻接节点
   e. 回溯: in_stack.discard(node_id)
4. 如果任一 DFS 返回 true，报告 SEMANTIC-BE-015
```

> **NOTE**: 后端 `DetectCycles` 使用反向邻接表（`controlSuccessors`），对环中的每条边分别报告 PathErr。编译器使用标准 DFS 三色标记法（白/灰/黑），仅报告一次。

**正确示例**:

```yaml
# ✅ 无环的有向图
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "llm-1"
    type: "3"
    data:
      nodeMeta:
        title: "LLM 1"
  - id: "llm-2"
    type: "3"
    data:
      nodeMeta:
        title: "LLM 2"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "llm-1"
  - sourceNodeID: "llm-1"
    targetNodeID: "llm-2"
  - sourceNodeID: "llm-2"
    targetNodeID: "900001"
# 拓扑: Start → LLM 1 → LLM 2 → End（无环）
```

**错误示例**:

```yaml
# ❌ 存在有向环: llm-1 → llm-2 → llm-1
# 诊断: SEMANTIC-BE-015 — workflow contains a cycle
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "llm-1"
    type: "3"
    data:
      nodeMeta:
        title: "LLM 1"
  - id: "llm-2"
    type: "3"
    data:
      nodeMeta:
        title: "LLM 2"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "llm-1"
  - sourceNodeID: "llm-1"
    targetNodeID: "llm-2"
  - sourceNodeID: "llm-2"
    targetNodeID: "llm-1"   # ← 回边，形成环
  - sourceNodeID: "llm-2"
    targetNodeID: "900001"
# 问题: llm-1 → llm-2 → llm-1 构成有向环
```

```yaml
# ❌ 自环
# 诊断: SEMANTIC-BE-015 — workflow contains a cycle
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "llm-1"
    type: "3"
    data:
      nodeMeta:
        title: "LLM"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "llm-1"
  - sourceNodeID: "llm-1"
    targetNodeID: "llm-1"   # ← 自环
  - sourceNodeID: "llm-1"
    targetNodeID: "900001"
# 问题: llm-1 指向自身形成自环
```

---

## 5.3 嵌套检查 (Nesting Constraint)

### 5.3.1 复合节点禁止嵌套 (SEMANTIC-BE-016)

复合节点（Loop、Batch）内部不能再嵌套其他复合节点。这一约束确保执行引擎只需要处理单层嵌套作用域，简化了变量解析和迭代控制逻辑。

| 属性 | 值 |
|------|-----|
| 规则 ID | `SEMANTIC-BE-016` |
| 错误类别 | `violation` |
| Checkability | `OFFLINE` |
| 后端对应 | `BE-ValidateNestedFlows-001` — `ValidateNestedFlows` |
| 后端错误消息 | `"composite nodes such as batch/loop cannot be nested"` |
| 源码位置 | `canvas_validate.go:254` |

**受约束的复合节点类型**:

| 节点类型 | type ID | 说明 |
|---------|---------|------|
| Loop | `"25"` | 循环节点 |
| Batch | `"28"` | 批处理节点 |

> **NOTE**: If 节点（type `"8"`）在编译器中也被归类为 `COMPOSITE_TYPES`（因为包含子画布），但嵌套检查仅针对 `COMPOSITE_NODE_TYPES`（Loop + Batch）。If 节点内部允许包含 Loop/Batch。

**算法描述**:

```
1. 遍历画布中所有节点
2. 如果节点 type ∈ {Loop, Batch} 且存在子节点 (blocks):
   a. 遍历子节点
   b. 如果任意子节点的 type ∈ {Loop, Batch}，报告 SEMANTIC-BE-016
```

**正确示例**:

```yaml
# ✅ Loop 内部不包含 Loop 或 Batch
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "loop-1"
    type: "25"
    data:
      nodeMeta:
        title: "循环处理"
    blocks:
      - id: "llm-inner"
        type: "3"
        data:
          nodeMeta:
            title: "循环内 LLM"
      - id: "code-inner"
        type: "5"
        data:
          nodeMeta:
            title: "循环内 Code"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "loop-1"
  - sourceNodeID: "loop-1"
    targetNodeID: "900001"
```

**错误示例**:

```yaml
# ❌ Loop 内嵌套 Loop
# 诊断: SEMANTIC-BE-016 — composite nodes such as batch/loop cannot be nested
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "loop-outer"
    type: "25"
    data:
      nodeMeta:
        title: "外层循环"
    blocks:
      - id: "loop-inner"
        type: "25"
        data:
          nodeMeta:
            title: "内层循环"  # ← 嵌套的 Loop
      - id: "llm-inner"
        type: "3"
        data:
          nodeMeta:
            title: "循环内 LLM"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "loop-outer"
  - sourceNodeID: "loop-outer"
    targetNodeID: "900001"
# 问题: loop-outer 内部包含 loop-inner
```

```yaml
# ❌ Batch 内嵌套 Loop
# 诊断: SEMANTIC-BE-016 — composite nodes such as batch/loop cannot be nested
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "batch-1"
    type: "28"
    data:
      nodeMeta:
        title: "批处理"
    blocks:
      - id: "loop-inner"
        type: "25"
        data:
          nodeMeta:
            title: "内层循环"  # ← Batch 内嵌套 Loop
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "batch-1"
  - sourceNodeID: "batch-1"
    targetNodeID: "900001"
# 问题: batch-1 内部包含 loop-inner
```

---

## 5.4 引用完整性检查 (Reference Integrity)

### 5.4.1 引用的 blockID 必须指向存在的节点 (SEMANTIC-BE-017)

当节点的输入参数通过引用（`Ref` 类型，`source: BlockOutput`）引用另一个节点的输出时，被引用的 blockID 必须在可达节点集合中存在。

| 属性 | 值 |
|------|-----|
| 规则 ID | `SEMANTIC-BE-017` |
| 错误类别 | `violation` |
| Checkability | `OFFLINE` |
| 后端对应 | `BE-CheckRefVariable-001` / `BE-CheckRefVariable-002` — `CheckRefVariable` |
| 后端错误消息 (001) | `"ref block error,[blockID] is empty"` |
| 后端错误消息 (002) | `"the node id \"%s\" on which node id \"%s\" depends does not exist"` |
| 源码位置 | `canvas_validate.go:168, 179` |

**算法描述**:

```
1. 遍历所有节点的输入参数 (inputParameters)
2. 对于 type=Ref, source=BlockOutput 的参数:
   a. 如果 blockID 为空字符串，报告 SEMANTIC-BE-017（空引用）
   b. 如果 blockID 不在可达节点集合中，报告 SEMANTIC-BE-017（悬空引用）
3. 同样检查 variable_parameters 和 branch conditions 中的引用
```

**引用结构说明**:

```yaml
# 引用格式
inputParameters:
  - name: "prompt"
    input:
      type: "reference"
      content:
        source: "BlockOutput"     # 引用来源
        blockID: "llm-1"          # 被引用的节点 ID
        name: "output_text"       # 被引用的输出变量名
```

**正确示例**:

```yaml
# ✅ blockID 指向存在的节点
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "llm-1"
    type: "3"
    data:
      nodeMeta:
        title: "LLM"
  - id: "code-1"
    type: "5"
    data:
      nodeMeta:
        title: "Code"
      inputs:
        inputParameters:
          - name: "prompt"
            input:
              type: "reference"
              content:
                source: "BlockOutput"
                blockID: "llm-1"       # ← 指向存在的节点
                name: "output_text"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "llm-1"
  - sourceNodeID: "llm-1"
    targetNodeID: "code-1"
  - sourceNodeID: "code-1"
    targetNodeID: "900001"
```

**错误示例 — 悬空引用**:

```yaml
# ❌ blockID 指向不存在的节点
# 诊断: SEMANTIC-BE-017 — reference blockID "deleted-node" does not point to an existing node
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "code-1"
    type: "5"
    data:
      nodeMeta:
        title: "Code"
      inputs:
        inputParameters:
          - name: "prompt"
            input:
              type: "reference"
              content:
                source: "BlockOutput"
                blockID: "deleted-node"  # ← 不存在的节点
                name: "output_text"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "code-1"
  - sourceNodeID: "code-1"
    targetNodeID: "900001"
# 问题: "deleted-node" 在图中不存在
```

**错误示例 — 空 blockID**:

```yaml
# ❌ blockID 为空字符串
# 诊断: SEMANTIC-BE-017 — reference blockID is empty
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "code-1"
    type: "5"
    data:
      nodeMeta:
        title: "Code"
      inputs:
        inputParameters:
          - name: "prompt"
            input:
              type: "reference"
              content:
                source: "BlockOutput"
                blockID: ""            # ← 空 blockID
                name: "output_text"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "code-1"
  - sourceNodeID: "code-1"
    targetNodeID: "900001"
# 问题: blockID 为空，无法解析引用目标
```

### 5.4.2 输入参数名必须符合标识符规范 (SEMANTIC-BE-019)

所有输入参数的名称必须符合标识符命名规范，以确保运行时变量解析的一致性。

| 属性 | 值 |
|------|-----|
| 规则 ID | `SEMANTIC-BE-019` |
| 错误类别 | `violation` |
| Checkability | `OFFLINE` |
| 后端对应 | `BE-CheckRefVariable-003` — `CheckRefVariable` |
| 后端错误消息 | `"parameter name only allows number or alphabet, and must begin with alphabet, but it's \"%s\""` |
| 源码位置 | `canvas_validate.go:197` |

**标识符规范**:

```
ParamName ::
    NameStartChar NameChars?

NameStartChar ::
    ASCII_Letter       // A-Z, a-z
    _                  // 下划线

NameChars ::
    NameChar
    NameChars NameChar

NameChar ::
    NameStartChar
    Digit              // 0-9
```

**正则表达式**: `^[A-Za-z_][A-Za-z0-9_]*$`

**正确示例**:

```yaml
# ✅ 合法参数名
inputParameters:
  - name: "prompt"           # 字母开头
    input:
      type: "literal"
      content: "Hello"
  - name: "_private_var"     # 下划线开头
    input:
      type: "literal"
      content: "value"
  - name: "input_2"          # 包含数字
    input:
      type: "literal"
      content: "value"
```

**错误示例**:

```yaml
# ❌ 参数名以数字开头
# 诊断: SEMANTIC-BE-019 — parameter name only allows valid identifier syntax
inputParameters:
  - name: "123abc"
    input:
      type: "literal"
      content: "value"
```

```yaml
# ❌ 参数名包含连字符
# 诊断: SEMANTIC-BE-019 — parameter name only allows valid identifier syntax
inputParameters:
  - name: "my-var"
    input:
      type: "literal"
      content: "value"
```

---

# 6. 链接时分析 (Link-time Analysis)

本章定义需要外部定义信息才能完成的验证规则。链接时验证需要访问工作流之外的资源（全局变量定义、子工作流定义、API 定义等），因此不能仅凭源文件静态完成。

| Checkability | 含义 |
|-------------|------|
| `OFFLINE` | 不需要外部信息，可静态完成（如 BE-017/018） |
| `PARTIAL` | 部分可静态完成，部分需要外部信息 |
| `REQUIRES_LIVE_VALIDATION` | 完全需要外部服务，无法静态完成 |

> **NOTE**: 本章中 `SEMANTIC-BE-017` 和 `SEMANTIC-BE-018` 虽然在后端被分类为 `runtime` check_type，但其核心逻辑（检查 blockID 存在性）不依赖外部服务，编译器已实现为 `OFFLINE`。只有类型匹配等扩展检查才需要外部信息。

## 6.1 全局变量类型检查 (SEMANTIC-BE-020)

VariableAssigner 节点在赋值时，必须确保赋值类型与全局变量的声明类型一致。全局变量定义存储在应用或 Agent 级别的元数据中，需要通过 API 获取。

| 属性 | 值 |
|------|-----|
| 规则 ID | `SEMANTIC-BE-020` |
| 错误类别 | `violation` |
| Checkability | `PARTIAL` |
| 后端对应 | `BE-CheckGlobalVariables-001` / `BE-CheckGlobalVariables-002` — `CheckGlobalVariables` |
| 后端错误消息 (类型不匹配) | `"node name %v, param [%s], type mismatch"` |
| 后端错误消息 (数组元素不匹配) | `"node name %v, param [%s], array element type mismatch"` |
| 源码位置 | `canvas_validate.go:314, 324` |

**编译器实现能力**:

| 检查项 | 能力 | 说明 |
|--------|------|------|
| 全局变量定义必须声明类型 | `OFFLINE` | 检查全局变量节点是否缺少 type 字段 |
| 赋值类型与声明类型匹配 | `REQUIRES_LIVE` | 需要 API 获取全局变量元数据 |
| 数组元素类型匹配 | `REQUIRES_LIVE` | 需要 API 获取全局变量元数据 |

**算法描述**:

```
1. 遍历所有 VariableAssigner 节点
2. 对每个赋值目标:
   a. 获取全局变量的声明类型（需要 API）
   b. 获取赋值表达式的推导类型
   c. 比较两者:
      - 标量类型: 直接比较
      - 数组类型: 比较元素类型
   d. 类型不匹配则报告 SEMANTIC-BE-020
```

**正确示例**:

```yaml
# ✅ 全局变量声明为 string，赋值也为 string
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "var-assign"
    type: "11"
    data:
      nodeMeta:
        title: "变量赋值"
      inputs:
        variableParameters:
          - name: "global_user_name"
            input:
              type: "literal"
              content: "张三"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
# 前提: 全局变量 global_user_name 声明类型为 string
# 结果: 类型匹配，验证通过
```

**错误示例 — 标量类型不匹配**:

```yaml
# ❌ 全局变量声明为 number，赋值为 string
# 诊断: SEMANTIC-BE-020 — node name 变量赋值, param [global_counter], type mismatch
nodes:
  - id: "var-assign"
    type: "11"
    data:
      nodeMeta:
        title: "变量赋值"
      inputs:
        variableParameters:
          - name: "global_counter"
            input:
              type: "literal"
              content: "not_a_number"  # ← string，但全局变量声明为 number
# 前提: 全局变量 global_counter 声明类型为 number
# 问题: 赋值类型 string 与声明类型 number 不匹配
```

**错误示例 — 数组元素类型不匹配**:

```yaml
# ❌ 全局变量声明为 array<string>，赋值为 array<number>
# 诊断: SEMANTIC-BE-020 — node name 变量赋值, param [global_tags], array element type mismatch
nodes:
  - id: "var-assign"
    type: "11"
    data:
      nodeMeta:
        title: "变量赋值"
      inputs:
        variableParameters:
          - name: "global_tags"
            input:
              type: "reference"
              content:
                source: "BlockOutput"
                blockID: "code-1"
                name: "number_array"  # ← array<number>，但全局变量声明为 array<string>
# 前提: 全局变量 global_tags 声明类型为 array<string>
# 问题: 数组元素类型 number 与声明元素类型 string 不匹配
```

---

## 6.2 子工作流终止计划类型检查 (SEMANTIC-BE-022)

子工作流节点（SubWorkflow）引用另一个工作流定义。当子工作流被修改后，其终止计划（TerminatePlan）可能与父工作流期望的不一致，需要重新验证。

| 属性 | 值 |
|------|-----|
| 规则 ID | `SEMANTIC-BE-022` |
| 错误类别 | `violation` |
| Checkability | `REQUIRES_LIVE_VALIDATION` |
| 后端对应 | `BE-CheckSubWorkFlowTerminatePlanType-001` / `BE-CheckSubWorkFlowTerminatePlanType-002` |
| 后端错误消息 | `"sub workflow has been modified, please refresh the page"` |
| 源码位置 | `canvas_validate.go:423, 437` |

**为什么需要运行时验证**:

1. 子工作流的画布数据存储在远端（通过 draft ID 或 versioned ID 引用）
2. 需要调用 API 获取子工作流的 End 节点终止计划
3. 需要比较父节点的 `TerminationType` 与子工作流 End 节点的 `TerminatePlan`

**后端验证逻辑**:

```
1. 收集所有 SubWorkflow 节点
2. 对每个子工作流节点:
   a. 通过 draft ID 或 versioned ID 解析引用的工作流画布
   b. 如果画布不存在 → 报告 "sub workflow has been modified"
   c. 获取子工作流的 End 节点
   d. 比较 End 节点的 TerminatePlan 与父节点的 TerminationType
   e. 如果不匹配 → 报告 "sub workflow has been modified"
```

**编译器处理**:

编译器遇到 SubWorkflow 节点时，生成 `REQUIRES_LIVE_VALIDATION` 诊断，提示用户该检查需要在 Coze 平台上完成。

```yaml
# ⚠️ SubWorkflow 节点 — 编译器标记需要运行时验证
# 诊断: SEMANTIC-BE-022 — subworkflow termination/version checks require live Coze validation
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "sub-1"
    type: "21"
    data:
      nodeMeta:
        title: "子工作流"
      inputs:
        workflowID: "wf-12345"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "sub-1"
  - sourceNodeID: "sub-1"
    targetNodeID: "900001"
# 注意: 子工作流的终止计划一致性无法静态验证
# 需要在 Coze 平台上运行 validateSchemaV2 API 完成检查
```

---

## 6.3 Plugin API 定义检查

Plugin 节点和部分内置节点（如 SubWorkflow）的输入参数可能有 `required` 约束。这些约束定义在 Plugin 的 API schema 或子工作流的输入定义中，无法从工作流源文件本身推导。

| 检查项 | Checkability | 说明 |
|--------|-------------|------|
| Plugin 输入必填字段 | `REQUIRES_LIVE_VALIDATION` | 需要 Plugin API 定义 |
| SubWorkflow 输入必填字段 | `REQUIRES_LIVE_VALIDATION` | 需要子工作流输入定义 |
| Plugin 输出格式 | `REQUIRES_LIVE_VALIDATION` | 需要 Plugin 返回 schema |

**编译器处理策略**:

编译器对 Plugin 节点的输入执行基础格式检查（参见 Layer 2），但不检查 `required` 约束，因为这需要外部 API 定义。用户应在 Coze 平台上通过 `validateSchemaV2` API 完成最终验证。

---

# 7. 运行时语义 (Runtime Semantics)

本章描述需要执行环境才能验证的语义规则。这些规则**无法通过静态分析完成**，编译器不实现这些检查，但在此记录其逻辑以确保规范完整性。

| 属性 | 值 |
|------|-----|
| Checkability | `REQUIRES_LIVE_VALIDATION` |
| 编译器实现 | 不实现（设计决策） |
| 验证位置 | Coze 平台运行时引擎 |

## 7.1 变量值验证

运行时引擎在执行工作流时，需要验证变量的实际值是否符合预期类型。

| 检查项 | 示例 | 为什么需要运行时 |
|--------|------|-----------------|
| 字符串长度 | `temperature = "abc"` | 值在运行时才确定 |
| 数值范围 | `loopCount = -1` | 值可能来自上游节点输出 |
| 枚举值 | `model = "gpt-99"` | 值可能来自变量引用 |
| 正则匹配 | `email = "not-email"` | 值在运行时才确定 |

**后端对应规则**:

| 规则 ID | 说明 |
|---------|------|
| `BE-CheckRefVariable-001` | blockID 非空检查（编译器已实现为 `OFFLINE`） |
| `BE-CheckRefVariable-002` | blockID 存在性检查（编译器已实现为 `OFFLINE`） |
| `BE-CheckRefVariable-003` | 参数名格式检查（编译器已实现为 `OFFLINE`） |

> **NOTE**: 后端将 `CheckRefVariable` 标记为 `runtime` check_type，但其核心逻辑不依赖外部服务。编译器已将这些规则提升为 `OFFLINE` 实现。真正的运行时验证（如值类型检查）不在后端验证器的职责范围内。

## 7.2 API 调用验证

Plugin 节点在执行时会调用外部 API。API 的返回格式、错误处理、超时行为等只能在运行时验证。

| 检查项 | 说明 |
|--------|------|
| 返回格式匹配 | API 返回的 JSON 结构是否匹配输出定义 |
| 错误处理 | API 调用失败时的异常处理是否正确 |
| 超时配置 | API 调用超时是否在合理范围内 |
| 鉴权有效性 | API Token 是否过期或权限不足 |

## 7.3 循环边界检查

Loop 和 Batch 节点的迭代次数在编译时无法确定，因为通常来自上游节点的输出或变量引用。

| 检查项 | 说明 |
|--------|------|
| 迭代次数非负 | `loopCount` 必须 ≥ 0 |
| 最大迭代上限 | `loopCount` 不超过平台限制 |
| 数组长度 | Batch 的输入数组长度验证 |
| 资源消耗 | 循环内的 API 调用次数限制 |

## 7.4 表达式求值

条件表达式（If 节点的 `left op right`）在运行时需要实际值才能求值。

| 检查项 | 说明 |
|--------|------|
| 操作数类型兼容 | `left` 和 `right` 的类型是否可比较 |
| 操作符合法性 | `operator` 是否适用于操作数类型 |
| 空值处理 | 操作数为 null 时的行为 |
| 短路求值 | AND/OR 条件的短路行为 |

---

# 附录

## 附录 A. 静态/运行时能力矩阵

以下矩阵汇总第 5-7 章所有验证规则的静态检查能力。

| 规则 ID | 描述 | Layer | Checkability | 编译器实现 | 后端实现 |
|---------|------|-------|-------------|-----------|---------|
| SEMANTIC-BE-001 | Start 节点必须有出边 | 3 (Graph) | `OFFLINE` | ✅ | ✅ |
| SEMANTIC-BE-002 | 非终端节点必须有出边 | 3 (Graph) | `OFFLINE` | ✅ | ✅ |
| SEMANTIC-BE-010 | 分支端口必须连接 | 3 (Graph) | `PARTIAL` | ✅ | ✅ |
| SEMANTIC-BE-015 | 禁止有向环 | 3 (Graph) | `OFFLINE` | ✅ | ✅ |
| SEMANTIC-BE-016 | 复合节点禁止嵌套 | 3 (Graph) | `OFFLINE` | ✅ | ✅ |
| SEMANTIC-BE-017 | 引用 blockID 必须存在 | 4 (Link) | `OFFLINE` | ✅ | ✅ |
| SEMANTIC-BE-018 | 引用变量名必须存在 | 4 (Link) | `OFFLINE` | ✅ | ✅ |
| SEMANTIC-BE-019 | 参数名标识符规范 | 3 (Graph) | `OFFLINE` | ✅ | ✅ |
| SEMANTIC-BE-020 | 全局变量类型匹配 | 4 (Link) | `PARTIAL` | ⚠️ 部分 | ✅ |
| SEMANTIC-BE-021 | 全局数组元素类型 | 4 (Link) | `REQUIRES_LIVE` | ⚠️ 部分 | ✅ |
| SEMANTIC-BE-022 | 子工作流终止计划 | 4 (Link) | `REQUIRES_LIVE` | ⚠️ 标记 | ✅ |
| — | Plugin required 字段 | 4 (Link) | `REQUIRES_LIVE` | ❌ | ✅ |
| — | 变量实际值验证 | 5 (Runtime) | `REQUIRES_LIVE` | ❌ | ❌ |
| — | API 调用结果验证 | 5 (Runtime) | `REQUIRES_LIVE` | ❌ | ❌ |
| — | 循环边界检查 | 5 (Runtime) | `REQUIRES_LIVE` | ❌ | ❌ |
| — | 表达式求值 | 5 (Runtime) | `REQUIRES_LIVE` | ❌ | ❌ |

### 能力层级说明

| Checkability | 含义 | 编译器行为 |
|-------------|------|-----------|
| `OFFLINE` | 纯静态可完成 | 实现为编译错误 |
| `PARTIAL` | 部分可静态完成 | 可检查的部分报编译错误，其余跳过 |
| `REQUIRES_LIVE` | 完全需要外部服务 | 生成 `REQUIRES_LIVE_VALIDATION` 诊断 |

### 与后端验证器的差异

| 差异点 | 后端 | 编译器 |
|--------|------|--------|
| BE-017/018 分类 | `runtime` check_type | `OFFLINE`（提升为静态检查） |
| BE-015 报告粒度 | 每条环边单独报告 PathErr | 整个环报告一次 |
| BE-016 节点范围 | 仅 Loop/Batch | 仅 Loop/Batch（If 排除） |
| BE-022 处理 | 实际调用 API 验证 | 标记 `REQUIRES_LIVE_VALIDATION` |

---

## 附录 B. 后端 ValidateTree 调用链

以下为 `coze-studio` 后端验证器 `ValidateTree` 函数的调用链，展示了图结构和链接验证的完整执行顺序。

```
ValidateTree
├── ValidateConnections                    ← Layer 3: 连通性
│   ├── [BE-001] entry node outDegree > 0  ← Start 节点出边检查
│   ├── [BE-010] branch ports connected    ← 分支端口连接检查
│   │   ├── If: true/false ports
│   │   ├── Intent: intent ports
│   │   └── Error handling: exception ports
│   └── [BE-002] non-terminal outDegree > 0 ← 非终端节点出边检查
│       └── 排除: entry, exit, break, continue
│
├── DetectCycles                           ← Layer 3: 环路检测
│   └── [BE-015] DFS cycle detection
│       ├── 构建反向邻接表 (controlSuccessors)
│       ├── 对每个未访问节点执行 DFS
│       └── 对环中每条边报告 PathErr
│
├── ValidateNestedFlows                    ← Layer 3: 嵌套检查
│   └── [BE-016] composite node nesting
│       └── 检查 Loop/Batch 内部是否包含 Loop/Batch
│
├── CheckRefVariable                       ← Layer 4: 引用检查
│   ├── [BE-017] blockID 非空检查
│   ├── [BE-017] blockID 存在性检查（可达节点集合）
│   └── [BE-019] 参数名格式检查 (^[A-Za-z_][A-Za-z0-9_]*$)
│
├── CheckGlobalVariables                   ← Layer 4: 全局变量检查
│   ├── [BE-020] 标量类型匹配
│   └── [BE-020] 数组元素类型匹配
│
└── CheckSubWorkFlowTerminatePlanType      ← Layer 4: 子工作流检查
    ├── [BE-022] 子工作流画布存在性
    └── [BE-022] 终止计划类型匹配
```

### 编译器 SemanticPass 对应调用链

```
SemanticPass.run
├── _check_canvas_shape                    ← BE-006: 画布结构
├── _check_parameter_names                 ← BE-019: 参数名格式
├── _check_nested_composites               ← BE-016: 复合节点嵌套
├── _check_global_variable_types           ← BE-020: 全局变量类型
├── _check_type_compatibility              ← BE-021: 类型兼容性
├── _check_start_connectivity              ← BE-001: Start 出边
├── _check_node_connectivity               ← BE-002: 节点连通性
├── _check_edge_endpoints                  ← BE-003: 边端点存在性
├── _check_start_end_existence             ← BE-004/005: Start/End 存在
├── _check_cycles                          ← BE-015: 环路检测
├── _check_ref_block_ids                   ← BE-017/018: 引用完整性
├── _check_subworkflow_live_validation     ← BE-022: 子工作流（标记）
├── _check_contract_consistency            ← BE-023: 契约一致性
└── _check_global_array_element_type       ← BE-021: 数组元素类型
```

---

> **规范维护说明**: 本章规则数据提取自 `backend-rules.json`、`validation-layers.md`、`validation-layers-status.md`，并交叉验证了编译器 `semantic_pass.py` 的实际实现。
