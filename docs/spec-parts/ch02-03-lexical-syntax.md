# Coze 工作流语言规范 — 第 2-3 章

> **版本**: 1.0  
> **提取来源**: `coze-studio` 前端表单规则 (form-meta-rules.json)、后端规则 (backend-rules.json)、验证分层标准 (validation-layers.md)  
> **对应编译器层级**: Layer 1 (Syntax) + Layer 2 (Static Sema)

---

# 2. 词法分析 (Lexical Analysis)

本章定义 Coze 工作流语言中所有合法的词法单元（token）及其构成规则。词法分析阶段仅需源文件本身，不依赖任何外部信息（Checkability: `OFFLINE`）。

## 2.1 Token 类型

Coze 工作流以 YAML/JSON 为传输格式。词法分析器从 YAML/JSON 解析树中提取以下 token 类型：

| Token 类型 | 说明 | 来源字段 |
|---|---|---|
| `NODE_ID` | 节点唯一标识符 | `nodes[].id` |
| `NODE_TYPE` | 节点类型标识（数字字符串或别名） | `nodes[].type` |
| `NODE_TYPE_ID` | 节点类型的数字 ID | `nodes[].type` 解析后 |
| `EDGE_SOURCE` | 边的源节点 ID | `edges[].sourceNodeID` |
| `EDGE_TARGET` | 边的目标节点 ID | `edges[].targetNodeID` |
| `EDGE_SOURCE_PORT` | 边的源端口 ID | `edges[].sourcePortID` |
| `PARAM_NAME` | 输入参数名 | `inputs.inputParameters[].name` |
| `OUTPUT_VAR_NAME` | 输出变量名 | `outputs[].name` |
| `VALUE_EXPR_TYPE` | 值表达式类型标记 | `input.type` |
| `VALUE_EXPR_CONTENT` | 值表达式内容 | `input.content` |
| `REF_SOURCE` | 引用来源标记 | `input.content.source` |
| `REF_BLOCK_ID` | 引用的块 ID | `input.content.blockID` |
| `REF_NAME` | 引用的变量名 | `input.content.name` |
| `TITLE` | 节点标题 | `nodeMeta.title` |
| `CONDITION_OP` | 条件操作符 | `branches[].conditions[].operator` |
| `VARIABLE_TYPE` | 变量类型标记 | 全局变量的 `type` 字段 |

> **NOTE**: Coze 工作流不使用传统编译器的字符级 lexer/tokenizer。传输格式（YAML/JSON）由标准解析器处理，词法规则作用于解析后的结构化字段值。

---

## 2.2 节点 ID 格式

节点 ID 是节点在工作流画布中的唯一标识符。

### 2.2.1 词法规则

```
NodeID ::
    NodeIDCharacters

NodeIDCharacters ::
    NodeIDCharacter
    NodeIDCharacters NodeIDCharacter

NodeIDCharacter ::
    ASCII_Letter       // A-Z, a-z
    Digit              // 0-9
    _                  // 下划线
    -                  // 连字符
```

**正则表达式**: `^[A-Za-z0-9_-]+$`

**约束**:
- 不得为空字符串（SYNTAX-005: `node ID is required`）
- 在同一画布（canvas）内不得重复（SYNTAX-005: `duplicate node ID "<id>" in canvas`）
- 必须为 YAML/JSON 对象类型（SYNTAX-005: `non-object node(s) in canvas`）

### 2.2.2 保留节点 ID

| ID | 用途 | 说明 |
|---|---|---|
| `100001` | 起始节点（Start） | 工作流入口，每个画布必须有且仅有一个 |
| `900001` | 终止节点（End） | 工作流出口 |

### 2.2.3 正确示例

```yaml
# ✅ 合法节点 ID
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "node-1"
    type: "3"
    data:
      nodeMeta:
        title: "LLM"
  - id: "if-1"
    type: "8"
    data:
      nodeMeta:
        title: "条件判断"
  - id: "batch_process_v2"
    type: "28"
    data:
      nodeMeta:
        title: "批量处理"
```

### 2.2.4 错误示例

```yaml
# ❌ 节点 ID 含空格
# 诊断: SYNTAX-005 — node ID 格式不合法
nodes:
  - id: "node 1"
    type: "3"
```

```yaml
# ❌ 节点 ID 为空字符串
# 诊断: SYNTAX-005 — node ID is required
nodes:
  - id: ""
    type: "3"
```

```yaml
# ❌ 节点 ID 缺失（字段不存在）
# 诊断: SYNTAX-005 — node ID is required
nodes:
  - type: "3"
    data:
      nodeMeta:
        title: "LLM"
```

```yaml
# ❌ 画布内节点 ID 重复
# 诊断: SYNTAX-005 — duplicate node ID "node-1" in canvas
nodes:
  - id: "node-1"
    type: "3"
    data:
      nodeMeta:
        title: "LLM 1"
  - id: "node-1"
    type: "5"
    data:
      nodeMeta:
        title: "Code 1"
```

---

## 2.3 参数名格式

参数名用于标识节点的输入参数（`inputs.inputParameters[].name`）和批量输入参数。

### 2.3.1 词法规则

```
ParamName ::
    ParamNameStart ParamNameContinue*

ParamNameStart ::
    ASCII_Letter       // A-Z, a-z
    _                  // 下划线

ParamNameContinue ::
    ASCII_Letter       // A-Z, a-z
    Digit              // 0-9
    _                  // 下划线
```

**正则表达式**: `^[A-Za-z_][A-Za-z0-9_]*$`

**约束**:
- 必须以字母或下划线开头（BE-CheckRefVariable-003）
- 仅允许字母、数字、下划线
- 不得为空

### 2.3.2 正确示例

```yaml
# ✅ 合法参数名
nodes:
  - id: "100002"
    type: "4"
    data:
      inputs:
        inputParameters:
          - name: "input_1"
            input:
              type: "literal"
              content: "hello"
          - name: "_private"
            input:
              type: "literal"
              content: "secret"
          - name: "maxTokens"
            input:
              type: "literal"
              content: "2048"
          - name: "API_KEY"
            input:
              type: "ref"
              content:
                source: "global_variable_system"
                blockID: ""
                name: "apiKey"
```

### 2.3.3 错误示例

```yaml
# ❌ 参数名以数字开头
# 诊断: BE-CheckRefVariable-003 — parameter name only allows number or alphabet,
#       and must begin with alphabet, but it's "123abc"
nodes:
  - id: "100002"
    type: "4"
    data:
      inputs:
        inputParameters:
          - name: "123abc"
            input:
              type: "literal"
              content: "value"
```

```yaml
# ❌ 参数名含连字符
# 诊断: BE-CheckRefVariable-003 — parameter name only allows number or alphabet,
#       and must begin with alphabet, but it's "my-var"
nodes:
  - id: "100002"
    type: "4"
    data:
      inputs:
        inputParameters:
          - name: "my-var"
            input:
              type: "literal"
              content: "value"
```

```yaml
# ❌ 参数名含空格
# 诊断: BE-CheckRefVariable-003 — parameter name only allows number or alphabet,
#       and must begin with alphabet, but it's "my param"
nodes:
  - id: "100002"
    type: "4"
    data:
      inputs:
        inputParameters:
          - name: "my param"
            input:
              type: "literal"
              content: "value"
```

---

## 2.4 输出变量名格式

输出变量名用于标识节点的输出变量（`outputs[].name`）。输出变量名有额外的保留字约束。

### 2.4.1 词法规则

```
OutputVarName ::
    OutputVarNameStart OutputVarNameContinue*

OutputVarNameStart ::
    ASCII_Letter       // A-Z, a-z
    _                  // 下划线

OutputVarNameContinue ::
    ASCII_Letter       // A-Z, a-z
    Digit              // 0-9
    _                  // 下划线
    $                  // 美元符号
```

**正则表达式**: `^[a-zA-Z_][a-zA-Z_$0-9]*$`

**约束**:
- 必须以字母或下划线开头
- 仅允许字母、数字、下划线、美元符号
- 不得为保留字（见 §2.4.2）
- 不得为空
- 同级兄弟节点名称不得重复（SPEC-OUT-006）
- `sys_` 前缀为系统保留（VAL-SYSTEM-VARIABLE-001）

### 2.4.2 保留字列表

以下标识符不得用作输出变量名：

| 保留字 | 类别 |
|---|---|
| `true` | 布尔字面量 |
| `false` | 布尔字面量 |
| `and` / `AND` | 逻辑运算符 |
| `or` / `OR` | 逻辑运算符 |
| `not` / `NOT` | 逻辑运算符 |
| `null` | 空值字面量 |
| `nil` | 空值字面量 |
| `If` | 控制结构关键字 |
| `Switch` | 控制结构关键字 |

> **NOTE**: 保留字检查使用完整的单词边界匹配（`/\b...\b/`），而非简单的字符串相等。

### 2.4.3 正确示例

```yaml
# ✅ 合法输出变量名
nodes:
  - id: "100003"
    type: "3"
    data:
      outputs:
        - name: "result"
          type: 1
        - name: "_output"
          type: 1
        - name: "data1"
          type: 1
        - name: "$temp"
          type: 1
```

### 2.4.4 错误示例

```yaml
# ❌ 输出变量名为保留字
# 诊断: SEMANTIC-FE-013 — output variable name "true" is a reserved word
nodes:
  - id: "100003"
    type: "3"
    data:
      outputs:
        - name: "true"
          type: 1
```

```yaml
# ❌ 输出变量名含空格
# 诊断: SEMANTIC-FE-013 — output variable name "my output" has invalid format
nodes:
  - id: "100003"
    type: "3"
    data:
      outputs:
        - name: "my output"
          type: 1
```

```yaml
# ❌ 输出变量名以数字开头
# 诊断: SEMANTIC-FE-013 — output variable name "1result" has invalid format
nodes:
  - id: "100003"
    type: "3"
    data:
      outputs:
        - name: "1result"
          type: 1
```

```yaml
# ❌ 输出变量名为系统保留前缀
# 诊断: VAL-SYSTEM-VARIABLE-001 — 不允许使用系统变量前缀
nodes:
  - id: "100003"
    type: "3"
    data:
      outputs:
        - name: "sys_custom"
          type: 1
```

```yaml
# ❌ 同级输出变量名重复
# 诊断: SPEC-OUT-006 — workflow_detail_node_error_variablename_duplicated
nodes:
  - id: "100003"
    type: "3"
    data:
      outputs:
        - name: "result"
          type: 1
        - name: "result"
          type: 1
```

---

## 2.5 值表达式类型

值表达式（ValueExpression）是参数值的核心载体。每个值表达式由 `type` 和 `content` 两个字段组成。

### 2.5.1 合法类型枚举

| Type 值 | 语义 | Content 结构 |
|---|---|---|
| `literal` | 字面量 | 直接字符串值 |
| `ref` | 变量引用 | `{ source, blockID, name, path? }` |
| `object_ref` | 对象引用 | `{ source, blockID, name, path }` |

**约束** (SYNTAX-019): 当 `type` 非 `literal` 时，`content.blockID` 不得为空。

### 2.5.2 引用来源枚举

当 `type` 为 `ref` 或 `object_ref` 时，`content.source` 必须为以下之一：

| Source 值 | 语义 |
|---|---|
| `block-output` | 引用上游节点的输出 |
| `global_variable_app` | 引用应用级全局变量 |
| `global_variable_system` | 引用系统级全局变量 |
| `global_variable_user` | 引用用户级全局变量 |

### 2.5.3 正确示例

```yaml
# ✅ literal 类型
input:
  type: "literal"
  content: "Hello, World!"
```

```yaml
# ✅ ref 类型 — 引用上游节点输出
input:
  type: "ref"
  content:
    source: "block-output"
    blockID: "100002"
    name: "result"
```

```yaml
# ✅ ref 类型 — 引用应用级全局变量
input:
  type: "ref"
  content:
    source: "global_variable_app"
    blockID: ""
    name: "user_name"
```

```yaml
# ✅ object_ref 类型 — 对象属性引用
input:
  type: "object_ref"
  content:
    source: "block-output"
    blockID: "100002"
    name: "response"
    path: ["data", "items", "0"]
```

### 2.5.4 错误示例

```yaml
# ❌ type 不在允许列表中
# 诊断: SYNTAX-019 / SEMANTIC-FE-001 — 值表达式 type 非法
input:
  type: "invalid_type"
  content: "value"
```

```yaml
# ❌ ref 类型缺少 blockID
# 诊断: SYNTAX-019 — parameter "input_1" ref must have blockID
input:
  type: "ref"
  content:
    source: "block-output"
    blockID: ""
    name: "result"
```

```yaml
# ❌ ref 来源不在允许列表中
# 诊断: SYNTAX-019 — ref source 非法
input:
  type: "ref"
  content:
    source: "invalid_source"
    blockID: "100002"
    name: "result"
```

---

## 2.6 节点标题格式

### 2.6.1 词法规则

**约束**:
- 不得为空（SEMANTIC-FE-009: `workflow_detail_node_name_error_empty`）
- 最大长度为 63 个字符（SEMANTIC-FE-010: `workflow_derail_node_detail_title_max`）
- 同一画布内标题不得重复（SEMANTIC-FE-011: `workflow_node_title_duplicated`）

### 2.6.2 正确示例

```yaml
# ✅ 合法标题
nodeMeta:
  title: "LLM 节点"
```

```yaml
# ✅ 最大长度标题（63 字符）
nodeMeta:
  title: "a]2345678901234567890123456789012345678901234567890123456789012"
```

### 2.6.3 错误示例

```yaml
# ❌ 标题为空
# 诊断: SEMANTIC-FE-009 — workflow_detail_node_name_error_empty
nodeMeta:
  title: ""
```

```yaml
# ❌ 标题超过 63 字符
# 诊断: SEMANTIC-FE-010 — workflow_derail_node_detail_title_max
nodeMeta:
  title: "这是一个非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常长的标题"
```

```yaml
# ❌ 同一画布内标题重复
# 诊断: SEMANTIC-FE-011 — workflow_node_title_duplicated
nodes:
  - id: "100002"
    type: "3"
    data:
      nodeMeta:
        title: "处理数据"
  - id: "100003"
    type: "3"
    data:
      nodeMeta:
        title: "处理数据"
```

---

## 2.7 变量类型标记

### 2.7.1 合法类型枚举

| 类型值 | 说明 |
|---|---|
| `string` | 字符串 |
| `integer` | 整数 |
| `float` | 浮点数 |
| `boolean` | 布尔值 |
| `object` | 对象（需提供 schema） |
| `list` | 列表（需提供 item type） |

**约束** (SYNTAX-020): 变量类型必须在允许列表中。
**约束** (SYNTAX-018): `object` 和 `list` 类型必须提供 schema 定义。

### 2.7.2 正确示例

```yaml
# ✅ 合法变量类型
- id: "11"
  type: "11"
  data:
    nodeMeta:
      title: "计数器"
    variableType: "integer"
```

```yaml
# ✅ object 类型带 schema
- id: "12"
  type: "11"
  data:
    nodeMeta:
      title: "用户信息"
    variableType: "object"
    schema:
      type: "object"
      properties:
        name:
          type: "string"
        age:
          type: "integer"
```

### 2.7.3 错误示例

```yaml
# ❌ 变量类型不在允许列表
# 诊断: SYNTAX-020 — variable type "number" is not allowed
- id: "11"
  type: "11"
  data:
    nodeMeta:
      title: "变量"
    variableType: "number"
```

```yaml
# ❌ object 类型缺少 schema
# 诊断: SYNTAX-018 — variable "config" of type object must have a schema
- id: "11"
  type: "11"
  data:
    nodeMeta:
      title: "配置"
    variableType: "object"
    variableName: "config"
```

```yaml
# ❌ list 类型缺少 item type
# 诊断: SYNTAX-018 — list variable "items" must specify item type in schema
- id: "11"
  type: "11"
  data:
    nodeMeta:
      title: "列表"
    variableType: "list"
    variableName: "items"
    schema:
      type: "list"
```

---

# 3. 语法分析 (Syntactic Analysis)

本章定义 Coze 工作流的语法结构。语法分析验证工作流文档的结构合法性，包括顶层结构、节点结构、边结构、分支结构和嵌套结构。

## 3.1 工作流顶层结构

### 3.1.1 文法定义

```
WorkflowDocument ::
    { CanvasBody }

CanvasBody ::
    nodes: [ Node, ... ]
    edges: [ Edge, ... ]
```

**约束**:
- 根对象必须是可解析为 Coze Canvas 的 YAML/JSON 对象（SYNTAX-001: `canvas root must be an object compatible with Coze Canvas`）
- 必须包含至少一个节点（SYNTAX-002: `workflow must contain at least one node`）
- 必须包含至少一条边（SYNTAX-003: `workflow must contain at least one edge`）
- `nodes` 数组中每个元素必须为 YAML/JSON 对象（SYNTAX-005: `non-object node(s) in canvas`）

### 3.1.2 正确示例

```yaml
# ✅ 合法工作流顶层结构
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "900001"
```

### 3.1.3 错误示例

```yaml
# ❌ 根对象不是合法的 Canvas 结构（为数组）
# 诊断: SYNTAX-001 — canvas root must be an object compatible with Coze Canvas
- id: "100001"
  type: "1"
```

```yaml
# ❌ 缺少节点
# 诊断: SYNTAX-002 — workflow must contain at least one node
edges:
  - sourceNodeID: "100001"
    targetNodeID: "900001"
```

```yaml
# ❌ 缺少边
# 诊断: SYNTAX-003 — workflow must contain at least one edge
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
```

---

## 3.2 节点结构

### 3.2.1 文法定义

```
Node ::
    {
        id: NodeID,                    // 必填
        type: NodeTypeID,              // 必填
        data: NodeData                 // 必填
    }

NodeData ::
    {
        nodeMeta: NodeMeta,            // 必填
        inputs: InputBlock,            // 可选，视节点类型
        outputs: [ OutputVar, ... ],   // 可选，视节点类型
        ...                            // 节点特定参数
    }

NodeMeta ::
    {
        title: string,                 // 必填，≤63 字符
        icon: string,                  // 可选
        subtitle: string,              // 可选
        description: string            // 可选
    }

InputBlock ::
    {
        inputParameters: [ InputParam, ... ]
    }

InputParam ::
    {
        name: ParamName,               // 必填，参见 §2.3
        input: ValueExpression          // 必填
    }

ValueExpression ::
    {
        type: "literal" | "ref" | "object_ref",
        content: string | RefContent
    }

RefContent ::
    {
        source: RefSource,             // 必填（ref/object_ref）
        blockID: string,               // 必填（ref/object_ref，除非 source 为 global_*）
        name: string,                  // 可选
        path: [ string, ... ]          // 可选（object_ref）
    }

OutputVar ::
    {
        name: OutputVarName,           // 必填，参见 §2.4
        type: integer,                 // 必填
        children: [ OutputVar, ... ]   // 可选，树形结构
    }
```

### 3.2.2 节点类型 ID 表

| 别名 | 数字 ID | 说明 |
|---|---|---|
| `Start` | `1` | 起始节点 |
| `End` | `2` | 终止节点 |
| `LLM` | `3` | 大语言模型节点 |
| `Api` | `4` | API 调用节点 |
| `Code` | `5` | 代码执行节点 |
| `Dataset` | `6` | 数据集检索节点 |
| `If` | `8` | 条件分支节点 |
| `SubWorkflow` | `9` | 子工作流节点 |
| `Variable` | `11` | 变量节点 |
| `Database` | `12` | 数据库节点 |
| `Output` | `13` | 输出节点 |
| `Imageflow` | `14` | 图像流节点 |
| `Text` | `15` | 文本处理节点 |
| `ImageGenerate` | `16` | 图像生成节点 |
| `Question` | `18` | 问题节点 |
| `Break` | `19` | 循环中断节点 |
| `SetVariable` | `20` | 设置变量节点 |
| `Loop` | `21` | 循环节点 |
| `Intent` | `22` | 意图识别节点 |
| `Batch` | `28` | 批量处理节点 |
| `Continue` | `29` | 循环继续节点 |
| `Input` | `30` | 输入节点 |
| `Comment` | `31` | 注释节点 |
| `VariableAssign` | `40` | 变量赋值节点 |
| `Http` | `45` | HTTP 请求节点 |
| `DatabaseCreate` | `46` | 数据库创建节点 |
| `DatabaseQuery` | `43` | 数据库查询节点 |
| `DatabaseUpdate` | `42` | 数据库更新节点 |
| `DatabaseDelete` | `44` | 数据库删除节点 |

> **约束** (SYNTAX-006): `type` 字段不得为空。
> **约束** (SYNTAX-021): `type` 值必须为已知节点类型 ID（warning 级别）。

### 3.2.3 特定节点类型字段约束

| 节点类型 | 约束 | 规则 ID |
|---|---|---|
| 所有节点 | `nodeMeta.title` 必填 | SEMANTIC-FE-009 |
| LLM (`3`) | `temperature` ∈ [0.0, 2.0] | SEMANTIC-FE-001 |
| LLM (`3`) | `maxTokens` ≥ 1 | SEMANTIC-FE-001 |
| Code (`5`) | `codeParams` 不得为空 | FORM-code-003 |
| Variable (`11`) | 必须有 `variableName` | SYNTAX-016 |
| Variable (`11`) | 必须有 `variableType` | SYNTAX-017 |
| DatabaseQuery (`43`) | `queryLimit` ∈ [1, 1000] | SEMANTIC-FE-001 |
| Question (`18`) | 选项内容不得为空 | SPEC-QUES-001 |
| Question (`18`) | 选项内容不得重复 | SPEC-QUES-002 |
| End (`2`) | 至少一个 `inputParameters` | SEMANTIC-FE-001 |
| Output (`13`) | 至少一个 `inputParameters` | SEMANTIC-FE-001 |
| Intent (`22`) | 第一个 `inputParameters` 必须有值 | SEMANTIC-FE-001 |
| If (`8`) | 必须有 `branches` 定义 | SEMANTIC-FE-001 |

### 3.2.4 正确示例

```yaml
# ✅ LLM 节点完整结构
- id: "100002"
  type: "3"
  data:
    nodeMeta:
      title: "GPT-4 对话"
    inputs:
      inputParameters:
        - name: "prompt"
          input:
            type: "literal"
            content: "请总结以下内容："
        - name: "maxTokens"
          input:
            type: "literal"
            content: "2048"
    llmParam:
      temperature:
        type: "literal"
        content: "0.7"
    outputs:
      - name: "response"
        type: 1
```

```yaml
# ✅ Variable 节点
- id: "100003"
  type: "11"
  data:
    nodeMeta:
      title: "用户变量"
    variableName: "user_name"
    variableType: "string"
```

### 3.2.5 错误示例

```yaml
# ❌ 缺少 type 字段
# 诊断: SYNTAX-006 — node type is required
- id: "100002"
  data:
    nodeMeta:
      title: "节点"
```

```yaml
# ❌ 缺少 nodeMeta.title
# 诊断: SEMANTIC-FE-009 — workflow_detail_node_name_error_empty
- id: "100002"
  type: "3"
  data:
    inputs:
      inputParameters: []
```

```yaml
# ❌ LLM temperature 超出范围
# 诊断: SEMANTIC-FE-001 — temperature 超出 [0, 2]
- id: "100002"
  type: "3"
  data:
    nodeMeta:
      title: "LLM"
    llmParam:
      temperature:
        type: "literal"
        content: "3.5"
```

```yaml
# ❌ Variable 节点缺少 variableName
# 诊断: SYNTAX-016 — variable node "100003" must have a name
- id: "100003"
  type: "11"
  data:
    nodeMeta:
      title: "变量"
    variableType: "string"
```

```yaml
# ❌ Variable 节点缺少 variableType
# 诊断: SYNTAX-017 — variable node "100003" must have a type
- id: "100003"
  type: "11"
  data:
    nodeMeta:
      title: "变量"
    variableName: "count"
```

```yaml
# ❌ Question 选项内容为空
# 诊断: SPEC-QUES-001 — workflow_ques_option_notempty
- id: "100004"
  type: "18"
  data:
    nodeMeta:
      title: "选择"
    options:
      - name: ""
      - name: "选项 A"
```

```yaml
# ❌ Question 选项内容重复
# 诊断: SPEC-QUES-002 — workflow_ques_ans_testrun_dulpicate
- id: "100004"
  type: "18"
  data:
    nodeMeta:
      title: "选择"
    options:
      - name: "选项 A"
      - name: "选项 A"
```

---

## 3.3 边结构

### 3.3.1 文法定义

```
Edge ::
    {
        sourceNodeID: NodeID,          // 必填
        targetNodeID: NodeID,          // 必填
        sourcePortID: string           // 可选（分支节点必填）
    }
```

**约束**:
- `sourceNodeID` 不得为空（SYNTAX-010: `edge sourceNodeID is required`）
- `targetNodeID` 不得为空（SYNTAX-011: `edge targetNodeID is required`）
- 源节点为分支节点时，`sourcePortID` 应存在（SYNTAX-012: `edge from branch node "<id>" should have sourcePortID`）

### 3.3.2 正确示例

```yaml
# ✅ 普通边
edges:
  - sourceNodeID: "100001"
    targetNodeID: "100002"
```

```yaml
# ✅ 分支节点的边（带 sourcePortID）
edges:
  - sourceNodeID: "if-1"
    targetNodeID: "100003"
    sourcePortID: "true"
  - sourceNodeID: "if-1"
    targetNodeID: "100004"
    sourcePortID: "false"
```

```yaml
# ✅ Intent 节点的边
edges:
  - sourceNodeID: "intent-1"
    targetNodeID: "handler-1"
    sourcePortID: "intent_0"
  - sourceNodeID: "intent-1"
    targetNodeID: "handler-2"
    sourcePortID: "intent_1"
```

### 3.3.3 错误示例

```yaml
# ❌ 缺少 sourceNodeID
# 诊断: SYNTAX-010 — edge sourceNodeID is required
edges:
  - targetNodeID: "100002"
```

```yaml
# ❌ 缺少 targetNodeID
# 诊断: SYNTAX-011 — edge targetNodeID is required
edges:
  - sourceNodeID: "100001"
```

```yaml
# ❌ 分支节点的边缺少 sourcePortID
# 诊断: SYNTAX-012 (warning) — edge from branch node "if-1" should have sourcePortID
edges:
  - sourceNodeID: "if-1"
    targetNodeID: "100003"
```

```yaml
# ❌ 引用不存在的节点 ID（边的目标节点）
# 诊断: SYNTAX-011 — 边引用的节点不存在（由语义层检查）
edges:
  - sourceNodeID: "100001"
    targetNodeID: "nonexistent"
```

---

## 3.4 分支结构

### 3.4.1 If 节点分支

If 节点通过 `branches` 字段定义条件分支。每个分支包含条件表达式。

```
IfNode ::
    {
        id: "if-<n>",
        type: "8",
        data: {
            nodeMeta: NodeMeta,
            branches: [ Branch, ... ]
        }
    }

Branch ::
    {
        condition: ConditionExpr
    }

ConditionExpr ::
    {
        conditions: [ ConditionBranch, ... ]
    }

ConditionBranch ::
    {
        left: ValueExpression,         // 必填
        operator: ConditionOperator,   // 必填（数字字符串）
        right: ValueExpression         // 二元运算符必填，一元运算符忽略
    }
```

#### 3.4.1.1 条件操作符枚举

| 操作符 ID | 名称 | 类型 | 说明 |
|---|---|---|---|
| `1` | Equal | 二元 | 等于 |
| `2` | NotEqual | 二元 | 不等于 |
| `3` | LengthGt | 二元 | 长度大于 |
| `4` | LengthGtEqual | 二元 | 长度大于等于 |
| `5` | LengthLt | 二元 | 长度小于 |
| `6` | LengthLtEqual | 二元 | 长度小于等于 |
| `7` | Contains | 二元 | 包含 |
| `8` | NotContains | 二元 | 不包含 |
| `9` | Null | **一元** | 为空 |
| `10` | NotNull | **一元** | 不为空 |
| `11` | True | **一元** | 为真 |
| `12` | False | **一元** | 为假 |
| `13` | Gt | 二元 | 大于 |
| `14` | GtEqual | 二元 | 大于等于 |
| `15` | Lt | 二元 | 小于 |
| `16` | LtEqual | 二元 | 小于等于 |

**约束**:
- `left` 不得为空（SPEC-COND-001: `workflow_detail_condition_error_refer_empty`）
- `operator` 不得为空（SPEC-COND-002: `workflow_detail_condition_condition_empty`）
- 二元运算符的 `right` 不得为空（SPEC-COND-003: `workflow_detail_condition_error_enter_comparison`）
- 一元运算符（9, 10, 11, 12）不需要 `right`

#### 3.4.1.2 正确示例

```yaml
# ✅ If 节点 — 二元条件
- id: "if-1"
  type: "8"
  data:
    nodeMeta:
      title: "判断分数"
    branches:
      - condition:
          conditions:
            - left:
                type: "ref"
                content:
                  source: "block-output"
                  blockID: "100002"
                  name: "score"
              operator: "13"    # Gt
              right:
                type: "literal"
                content: "60"
```

```yaml
# ✅ If 节点 — 一元条件（不需要 right）
- id: "if-2"
  type: "8"
  data:
    nodeMeta:
      title: "判断空值"
    branches:
      - condition:
          conditions:
            - left:
                type: "ref"
                content:
                  source: "block-output"
                  blockID: "100002"
                  name: "result"
              operator: "10"    # NotNull
```

```yaml
# ✅ If 节点 — 多条件组合（AND 语义）
- id: "if-3"
  type: "8"
  data:
    nodeMeta:
      title: "复合条件"
    branches:
      - condition:
          conditions:
            - left:
                type: "ref"
                content:
                  source: "block-output"
                  blockID: "100002"
                  name: "age"
              operator: "14"    # GtEqual
              right:
                type: "literal"
                content: "18"
            - left:
                type: "ref"
                content:
                  source: "block-output"
                  blockID: "100002"
                  name: "verified"
              operator: "11"    # True
```

#### 3.4.1.3 错误示例

```yaml
# ❌ 条件 left 为空
# 诊断: SPEC-COND-001 — workflow_detail_condition_error_refer_empty
- id: "if-1"
  type: "8"
  data:
    nodeMeta:
      title: "条件"
    branches:
      - condition:
          conditions:
            - left: null
              operator: "1"
              right:
                type: "literal"
                content: "hello"
```

```yaml
# ❌ 条件 operator 缺失
# 诊断: SPEC-COND-002 — workflow_detail_condition_condition_empty
- id: "if-1"
  type: "8"
  data:
    nodeMeta:
      title: "条件"
    branches:
      - condition:
          conditions:
            - left:
                type: "ref"
                content:
                  source: "block-output"
                  blockID: "100002"
                  name: "value"
              operator: null
              right:
                type: "literal"
                content: "hello"
```

```yaml
# ❌ 二元运算符缺少 right
# 诊断: SPEC-COND-003 — workflow_detail_condition_error_enter_comparison
- id: "if-1"
  type: "8"
  data:
    nodeMeta:
      title: "条件"
    branches:
      - condition:
          conditions:
            - left:
                type: "ref"
                content:
                  source: "block-output"
                  blockID: "100002"
                  name: "value"
              operator: "1"     # Equal（二元）
              right: null
```

### 3.4.2 Intent 节点分支

Intent 节点用于意图识别，每个意图对应一个分支端口。

```
IntentNode ::
    {
        id: "intent-<n>",
        type: "22",
        data: {
            nodeMeta: NodeMeta,
            inputs: {
                inputParameters: [ InputParam, ... ]   // 第一个必填
            }
        }
    }
```

**约束**:
- 第一个 `inputParameter` 必须有值（SEMANTIC-FE-001: `REQUIRE_FIRST_INPUT_NODE_TYPES`）
- 每个意图端口应有对应的出边

### 3.4.3 Question 节点分支

Question 节点用于向用户提问，选项即为分支。

```
QuestionNode ::
    {
        id: "question-<n>",
        type: "18",
        data: {
            nodeMeta: NodeMeta,
            options: [ Option, ... ]
        }
    }

Option ::
    {
        name: string                   // 非空且不重复
    }
```

---

## 3.5 嵌套结构（Loop / Batch）

### 3.5.1 文法定义

Loop 和 Batch 节点是复合节点（composite nodes），包含内部子画布（sub-canvas）。

```
CompositeNode ::
    {
        id: NodeID,
        type: "21" | "28",             // Loop=21, Batch=28
        data: {
            nodeMeta: NodeMeta,
            ...
        },
        blocks: [ Node, ... ],         // 内部节点
        edges: [ Edge, ... ]           // 内部边
    }
```

**约束**:
- 复合节点内的子节点遵循与顶层节点相同的词法和语法规则
- 复合节点**不得嵌套**（BE-ValidateNestedFlows-001: `composite nodes such as batch/loop cannot be nested`）
- 即 Loop 内不得再包含 Loop 或 Batch，Batch 内不得再包含 Loop 或 Batch

### 3.5.2 Loop 节点端口

Loop 节点有固定的内部端口：

| 端口 ID | 说明 |
|---|---|
| `loop-function-inline-input` | 循环体输入端口 |
| `loop-function-inline-output` | 循环体输出端口 |

### 3.5.3 Batch 节点端口

Batch 节点有固定的内部端口：

| 端口 ID | 说明 |
|---|---|
| `batch-function-inline-input` | 批量处理输入端口 |
| `batch-function-inline-output` | 批量处理输出端口 |

### 3.5.4 正确示例

```yaml
# ✅ Loop 节点
- id: "loop-1"
  type: "21"
  data:
    nodeMeta:
      title: "遍历列表"
  blocks:
    - id: "inner-1"
      type: "3"
      data:
        nodeMeta:
          title: "处理每一项"
    - id: "inner-2"
      type: "5"
      data:
        nodeMeta:
          title: "代码处理"
  edges:
    - sourceNodeID: "loop-function-inline-input"
      targetNodeID: "inner-1"
    - sourceNodeID: "inner-1"
      targetNodeID: "inner-2"
    - sourceNodeID: "inner-2"
      targetNodeID: "loop-function-inline-output"
```

```yaml
# ✅ Batch 节点
- id: "batch-1"
  type: "28"
  data:
    nodeMeta:
      title: "批量调用 API"
    inputs:
      inputParameters:
        - name: "url"
          input:
            type: "literal"
            content: "https://api.example.com"
  blocks:
    - id: "batch-inner-1"
      type: "4"
      data:
        nodeMeta:
          title: "HTTP 请求"
  edges:
    - sourceNodeID: "batch-function-inline-input"
      targetNodeID: "batch-inner-1"
    - sourceNodeID: "batch-inner-1"
      targetNodeID: "batch-function-inline-output"
```

### 3.5.5 错误示例

```yaml
# ❌ Loop 嵌套 Loop
# 诊断: BE-ValidateNestedFlows-001 — composite nodes such as batch/loop cannot be nested
- id: "loop-1"
  type: "21"
  data:
    nodeMeta:
      title: "外层循环"
  blocks:
    - id: "loop-2"
      type: "21"
      data:
        nodeMeta:
          title: "内层循环"
      blocks:
        - id: "inner-1"
          type: "3"
          data:
            nodeMeta:
              title: "处理"
  edges: []
```

```yaml
# ❌ Batch 嵌套 Loop
# 诊断: BE-ValidateNestedFlows-001 — composite nodes such as batch/loop cannot be nested
- id: "batch-1"
  type: "28"
  data:
    nodeMeta:
      title: "批量处理"
  blocks:
    - id: "loop-1"
      type: "21"
      data:
        nodeMeta:
          title: "内层循环"
      blocks:
        - id: "inner-1"
          type: "3"
          data:
            nodeMeta:
              title: "处理"
  edges: []
```

---

## 3.6 图结构约束

以下约束属于 Layer 3（Graph），仅需拓扑结构即可验证。

### 3.6.1 起始节点连通性

**规则** (BE-validateConnections-001): 起始节点（`type: "1"`）必须至少有一条出边。

```yaml
# ✅ Start 节点有出边
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "100002"
    type: "3"
    data:
      nodeMeta:
        title: "LLM"
edges:
  - sourceNodeID: "100001"
    targetNodeID: "100002"
```

```yaml
# ❌ Start 节点无出边（死节点）
# 诊断: BE-validateConnections-001 — node "start" not connected
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "100002"
    type: "2"
    data:
      nodeMeta:
        title: "End"
edges: []
```

### 3.6.2 普通节点连通性

**规则** (BE-validateConnections-003): 非分支、非终端、非 Break/Continue 的普通节点必须至少有一条出边。

```yaml
# ❌ LLM 节点无出边（死节点）
# 诊断: BE-validateConnections-003 — node "100002" not connected
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: "Start"
  - id: "100002"
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
    targetNodeID: "100002"
  # 100002 没有出边
```

### 3.6.3 分支端口连通性

**规则** (BE-validateConnections-002): 分支节点（If/Intent）的每个端口都必须至少有一条出边。

```yaml
# ❌ If 节点只连接了 true 分支，false 分支未连接
# 诊断: BE-validateConnections-002 — node "if-1"'s port "false" not connected
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
        title: "条件"
      branches:
        - condition:
            conditions:
              - left:
                  type: "ref"
                  content:
                    source: "block-output"
                    blockID: "100001"
                    name: "output"
                operator: "11"
  - id: "100003"
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
    targetNodeID: "if-1"
  - sourceNodeID: "if-1"
    targetNodeID: "100003"
    sourcePortID: "true"
  # false 端口未连接
```

### 3.6.4 禁止环路

**规则** (BE-DetectCycles-001): 工作流图中不得存在环路。

```yaml
# ❌ 环路: A → B → C → A
# 诊断: BE-DetectCycles-001 — line connections do not allow parallel lines
#       to intersect and form loops with each other
nodes:
  - id: "A"
    type: "3"
    data:
      nodeMeta:
        title: "节点 A"
  - id: "B"
    type: "3"
    data:
      nodeMeta:
        title: "节点 B"
  - id: "C"
    type: "3"
    data:
      nodeMeta:
        title: "节点 C"
edges:
  - sourceNodeID: "A"
    targetNodeID: "B"
  - sourceNodeID: "B"
    targetNodeID: "C"
  - sourceNodeID: "C"
    targetNodeID: "A"
```

---

## 3.7 引用变量验证

以下约束属于 Layer 4（Link），部分需要外部定义。

### 3.7.1 引用的 blockID 不得为空

**规则** (BE-CheckRefVariable-001): 当值表达式为 `ref` 类型且 `source` 为 `block-output` 时，`blockID` 不得为空。

```yaml
# ❌ ref 的 blockID 为空
# 诊断: BE-CheckRefVariable-001 — ref block error,[blockID] is empty
input:
  type: "ref"
  content:
    source: "block-output"
    blockID: ""
    name: "result"
```

### 3.7.2 引用的节点必须存在

**规则** (BE-CheckRefVariable-002): 引用的 `blockID` 对应的节点必须在可达图中存在。

```yaml
# ❌ 引用不存在的节点
# 诊断: BE-CheckRefVariable-002 — the node id "deleted-node" on which node
#       id "100002" depends does not exist
input:
  type: "ref"
  content:
    source: "block-output"
    blockID: "deleted-node"
    name: "result"
```

### 3.7.3 全局变量类型匹配

**规则** (BE-CheckGlobalVariables-001): 变量赋值的类型必须与全局变量声明的类型一致。

```yaml
# ❌ 全局变量声明为 string，赋值为 integer
# 诊断: BE-CheckGlobalVariables-001 — node name %v, param [%s], type mismatch
# （需要外部全局变量定义来验证）
```

---

## 3.8 异常处理结构

### 3.8.1 文法定义

```
OnErrorConfig ::
    {
        settingOnErrorIsOpen: boolean,
        processType: string,           // "RETURN" | 其他
        settingOnErrorJSON: string     // processType 为 RETURN 时必填
    }
```

**约束** (SEMANTIC-FE-012): 当 `settingOnErrorIsOpen` 为 `true` 且 `processType` 为 `RETURN` 时，`settingOnErrorJSON` 必须为合法 JSON。

### 3.8.2 正确示例

```yaml
# ✅ 合法异常处理配置
- id: "100002"
  type: "3"
  data:
    nodeMeta:
      title: "LLM"
    onErrorConfig:
      settingOnErrorIsOpen: true
      processType: "RETURN"
      settingOnErrorJSON: '{"error": "处理失败"}'
```

### 3.8.3 错误示例

```yaml
# ❌ 异常处理 JSON 格式错误
# 诊断: SEMANTIC-FE-012 — setting-on-error RETURN JSON is not parseable
- id: "100002"
  type: "3"
  data:
    nodeMeta:
      title: "LLM"
    onErrorConfig:
      settingOnErrorIsOpen: true
      processType: "RETURN"
      settingOnErrorJSON: '{invalid json}'
```

---

## 3.9 诊断规则 ID 索引

| 规则 ID | 层级 | 严重级别 | 摘要 |
|---|---|---|---|
| SYNTAX-001 | Layer 1 | violation | 根对象必须是合法的 Canvas 对象 |
| SYNTAX-002 | Layer 1 | violation | 工作流必须包含至少一个节点 |
| SYNTAX-003 | Layer 1 | violation | 工作流必须包含至少一条边 |
| SYNTAX-004 | Layer 1 | violation | versions 必须为对象类型 |
| SYNTAX-005 | Layer 1 | violation | 节点 ID 必填、非对象节点、重复 ID |
| SYNTAX-006 | Layer 1 | violation | 节点类型必填 |
| SYNTAX-010 | Layer 1 | violation | 边的 sourceNodeID 必填 |
| SYNTAX-011 | Layer 1 | violation | 边的 targetNodeID 必填 |
| SYNTAX-012 | Layer 1 | warning | 分支节点的边应有 sourcePortID |
| SYNTAX-016 | Layer 1 | violation | 变量节点必须有 variableName |
| SYNTAX-017 | Layer 1 | violation | 变量节点必须有 variableType |
| SYNTAX-018 | Layer 1 | violation | object/list 类型必须有 schema |
| SYNTAX-019 | Layer 1 | violation | ref 类型必须有 blockID |
| SYNTAX-020 | Layer 1 | violation | 变量类型不在允许列表 |
| SYNTAX-021 | Layer 1 | warning | 节点类型未知 |
| SEMANTIC-FE-001 | Layer 2 | violation | 节点特定字段验证 |
| SEMANTIC-FE-009 | Layer 2 | violation | 节点标题必填 |
| SEMANTIC-FE-010 | Layer 2 | violation | 节点标题长度 ≤63 |
| SEMANTIC-FE-011 | Layer 2 | violation | 节点标题唯一 |
| SEMANTIC-FE-012 | Layer 2 | violation | 异常处理 JSON 可解析 |
| SEMANTIC-FE-013 | Layer 2 | violation | 输出变量名格式和保留字 |
| BE-001 / validateConnections-001 | Layer 3 | NodeErr | 起始节点必须有出边 |
| BE-002 / validateConnections-003 | Layer 3 | NodeErr | 普通节点必须有出边 |
| BE-010 / validateConnections-002 | Layer 3 | NodeErr | 分支端口必须连接 |
| BE-015 / DetectCycles-001 | Layer 3 | PathErr | 禁止环路 |
| BE-016 / ValidateNestedFlows-001 | Layer 3 | NodeErr | 禁止嵌套复合节点 |
| BE-CheckRefVariable-001 | Layer 4 | NodeErr | ref 的 blockID 不得为空 |
| BE-CheckRefVariable-002 | Layer 4 | NodeErr | 引用的节点必须存在 |
| BE-CheckRefVariable-003 | Layer 4 | NodeErr | 参数名格式验证 |
| BE-CheckGlobalVariables-001 | Layer 4 | NodeErr | 全局变量类型匹配 |
| SPEC-COND-001 | Layer 2 | violation | 条件左值必填 |
| SPEC-COND-002 | Layer 2 | violation | 条件操作符必填 |
| SPEC-COND-003 | Layer 2 | violation | 条件右值必填（二元运算符） |
| SPEC-QUES-001 | Layer 2 | violation | Question 选项非空 |
| SPEC-QUES-002 | Layer 2 | violation | Question 选项不重复 |
| SPEC-OUT-006 | Layer 2 | violation | 输出变量名同级唯一 |
| VAL-SYSTEM-VARIABLE-001 | Layer 2 | violation | 禁止 sys_ 前缀 |

---

> **下一章**: [第 4 章：静态语义分析](./ch04-05-static-sema-graph.md) — 涵盖类型系统、作用域、引用解析和图结构验证
