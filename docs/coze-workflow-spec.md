# Coze 工作流语言规范
## 基于 ECMA-262 风格的正式规范

**版本**: 1.0
**日期**: 2026-06-17
**状态**: Draft

---

# 1. 概述 (Overview)

## 1.1 语言定位

Coze 工作流是一种**声明式的有向图语言**，用于描述 AI 工作流的执行流程。其核心设计目标是：以结构化数据（YAML / JSON / `.flow`）作为传输格式，通过静态验证确保工作流定义在提交运行前即具备语法正确性、语义一致性和图结构完整性。

| 属性 | 值 |
|------|-----|
| 目标语言 | Coze 工作流 |
| 传输格式 | YAML / JSON / `.flow` |
| 产品角色 | 静态目标语言验证层（编译器前端） |
| 验证策略 | 纯静态优先，有外部定义时渐进扩展 |
| 参考实现 | `coze_yaml_compiler_v2` |

本规范不定义运行时行为，也不覆盖代码生成。它描述的是：什么样的工作流定义是合法的，什么样的不是，以及如何以确定的诊断信息告知用户。

## 1.2 与传统编译器的对应关系

Coze 工作流验证器的设计遵循传统编译器前端的架构，但不包含 IR 生成和后端优化，因为验证器只做检查，不生成代码。

| 传统编译器阶段 | Coze 验证器对应 | 职责 |
|---------------|----------------|------|
| Lexer / Parser | Transport + AST Builder | 将 YAML / JSON 解析为内部 AST |
| Sema (符号分析) | SymbolTable + ScopeTree | 构建符号表、作用域树，解析变量引用 |
| Passes (多遍扫描) | SyntaxPass + SemanticPass + PortabilityPass | 分层执行语法、语义、图结构、链接检查 |
| Report (诊断输出) | CompilerV2Report | 汇总诊断信息，生成结构化错误报告 |

```
传统编译器:
  Lexer → Parser → AST → Sema → IR → CodeGen

Coze 验证器:
  Transport → AST → Sema → Passes → Report
  (纯静态分析，不生成代码)
```

## 1.3 验证能力分层

验证器将所有检查规则分为五个层级，每个层级的可静态检查程度不同：

| 层级 | 名称 | 标识 | 可做性 | 说明 |
|------|------|------|--------|------|
| Layer 1 | 语法 (Syntax) | `OFFLINE` | ✅ 100% | 只需源文件，无需外部信息 |
| Layer 2 | 静态语义 (Static Sema) | `OFFLINE` | ✅ 大部分 | 只需 AST + 符号表 |
| Layer 3 | 图结构 (Graph) | `OFFLINE` | ✅ 可做 | 只需节点+边的拓扑结构 |
| Layer 4 | 链接 (Link) | `PARTIAL` | ⚠️ 部分 | 需要外部定义（API / 子工作流 / 全局变量） |
| Layer 5 | 运行时 (Runtime) | `REQUIRES_LIVE` | ❌ 不可做 | 需要执行环境 |

各层覆盖的验证点示例：

- **Layer 1**: YAML/JSON 结构合法性、节点 ID 格式、节点类型是否已知、边的 source/target 存在性、必填字段存在性。
- **Layer 2**: 节点标题长度/格式、参数名格式、值表达式格式、节点特定字段验证、条件分支结构、输出变量名保留字。
- **Layer 3**: Start 节点必须有出边、分支端口必须连接、非 End 节点必须有出边、禁止嵌套复合节点、禁止环路。
- **Layer 4**: 全局变量类型匹配、子工作流终止计划类型、Plugin 输入是否 required、SubWorkflow 输入是否 required。
- **Layer 5**: 变量实际值验证、API 调用结果验证、循环边界检查、表达式求值。

**设计原则**：纯静态优先，明确标记无法静态检查的规则，有外部定义时可渐进增强 Layer 4。

## 1.4 规则统计

本规范共收录 **223 条**验证规则，覆盖 **39 种**节点类型。

### 按来源分布

| 来源 | 规则数 | 说明 |
|------|--------|------|
| `frontend_form_meta` | 117 | 前端表单元数据验证（`form-meta.tsx`） |
| `frontend_validator` | 59 | 前端通用验证器（`validators/`） |
| `specialized` | 29 | 特化验证规则（条件、输出、问题节点等） |
| `backend` | 12 | 后端图结构验证（Go `ValidateTree`） |
| `syntax` | 6 | Transport 层语法验证 |
| **合计** | **223** | |

### 按验证层级分布

| 层级 | 规则数 | 占比 |
|------|--------|------|
| Layer 1 (语法) | 6 | 2.7% |
| Layer 2 (静态语义) | 205 | 91.9% |
| Layer 3 (图结构) | 2 | 0.9% |
| Layer 4 (链接) | 3 | 1.3% |
| Layer 5 (运行时) | 7 | 3.1% |

> **注**: Layer 2 规则数最多，因为前端表单验证和通用验证器大部分属于静态语义检查。Layer 5 规则虽然标记为运行时，但其逻辑结构已在规范中记录，供外部集成时参考。

### 覆盖率对照

| 检查类别 | coze-studio | 本验证器 | 差异 |
|---------|-------------|---------|------|
| 前端表单验证 | ✅ 40+ form-meta | ✅ FE-001 (25 种节点) | 覆盖率相当 |
| 图结构验证 | ✅ 后端 API | ✅ BE-001/002/010/015/016 | 完全对齐 |
| 链接验证 | ✅ 后端 API | ⚠️ BE-017/018 | 部分对齐 |
| 运行时验证 | ✅ 运行时 | ❌ 不可做 | 设计差异 |

---

# 附录

## 附录 A. 完整节点类型表

以下为 `STANDARD_NODE_TYPE_TABLE` 中定义的所有节点类型，按类型 ID 排序。

| 序号 | 节点类型 | 类型 ID | 传输格式名称 | 分类 |
|------|---------|---------|-------------|------|
| 1 | Start | (特殊) | `start` | 控制流 |
| 2 | End | (特殊) | `end` | 控制流 |
| 3 | LLM | `3` | — | AI |
| 4 | Api | `4` | — | 集成 |
| 5 | Code | `5` | `code` | 执行 |
| 6 | Dataset | `6` | `dataset-search` | AI |
| 8 | If | `8` | `if` | 控制流 |
| 9 | SubWorkflow | `9` | `sub-workflow` | 集成 |
| 11 | Variable | `11` | `variable` | 数据 |
| 12 | Database | `12` | `database` | 数据 |
| 13 | Output | `13` | `output` | I/O |
| 14 | Imageflow | `14` | `image-generate` | AI |
| 15 | Text | `15` | `text-process` | 数据 |
| 16 | ImageGenerate | `16` | `image-generate` | AI |
| 17 | ImageReference | `17` | — | AI |
| 18 | Question | `18` | `question` | I/O |
| 19 | Break | `19` | `break` | 控制流 |
| 20 | SetVariable | `20` | `set-variable` | 数据 |
| 21 | Loop | `21` | `loop` | 控制流 |
| 22 | Intent | `22` | `intent` | 控制流 |
| 23 | ImageCanvas | `23` | `image-canvas` | AI |
| 24 | SceneVariable | `24` | — | 场景 |
| 25 | SceneChat | `25` | — | 场景 |
| 26 | LTM | `26` | `ltm` | AI |
| 27 | DatasetWrite | `27` | `dataset-write` | AI |
| 28 | Batch | `28` | `batch` | 控制流 |
| 29 | Continue | `29` | `continue` | 控制流 |
| 30 | Input | `30` | `input` | I/O |
| 31 | Comment | `31` | — | 辅助 |
| 32 | VariableMerge | `32` | — | 数据 |
| 34 | TriggerUpsert | `34` | `trigger-upsert` | 触发器 |
| 35 | TriggerDelete | `35` | `trigger-delete` | 触发器 |
| 36 | TriggerRead | `36` | `trigger-read` | 触发器 |
| 37 | QueryMessageList | `37` | `query-message-list` | 会话 |
| 38 | ClearContext | `38` | `clear-conversation-history` | 会话 |
| 39 | CreateConversation | `39` | `create-conversation` | 会话 |
| 40 | VariableAssign | `40` | `variable-assign` | 数据 |
| 42 | DatabaseUpdate | `42` | — | 数据 |
| 43 | DatabaseQuery | `43` | — | 数据 |
| 44 | DatabaseDelete | `44` | — | 数据 |
| 45 | Http | `45` | `http` | 集成 |
| 46 | DatabaseCreate | `46` | — | 数据 |
| 51 | UpdateConversation | `51` | `update-conversation` | 会话 |
| 52 | DeleteConversation | `52` | `delete-conversation` | 会话 |
| 53 | QueryConversationList | `53` | `query-conversation-list` | 会话 |
| 54 | QueryConversationHistory | `54` | `query-conversation-history` | 会话 |
| 55 | CreateMessage | `55` | `create-message` | 会话 |
| 56 | UpdateMessage | `56` | `update-message` | 会话 |
| 57 | DeleteMessage | `57` | `delete-message` | 会话 |
| 58 | JsonStringify | `58` | `json-stringify` | 数据 |
| 59 | JsonParser | `59` | — | 数据 |

> **注**: 类型 ID `1`、`7`、`10`、`33`、`41`、`47`–`50` 未分配。Start 和 End 节点使用特殊常量，不在此表中。

## 附录 B. 条件运算符枚举 (ConditionType)

条件分支验证基于 `left / operator / right` 三元组结构。操作符定义来自 `ConditionType` 枚举，共 **16 种**。

### 二元运算符 (Binary Operators)

需要 `left` 和 `right` 两个操作数。

| ID | 名称 | 说明 |
|----|------|------|
| 1 | `Equal` | 等于 |
| 2 | `NotEqual` | 不等于 |
| 3 | `LengthGt` | 长度大于 |
| 4 | `LengthGtEqual` | 长度大于等于 |
| 5 | `LengthLt` | 长度小于 |
| 6 | `LengthLtEqual` | 长度小于等于 |
| 7 | `Contains` | 包含 |
| 8 | `NotContains` | 不包含 |
| 13 | `Gt` | 大于 |
| 14 | `GtEqual` | 大于等于 |
| 15 | `Lt` | 小于 |
| 16 | `LtEqual` | 小于等于 |

### 一元运算符 (Unary Operators)

只需要 `left` 操作数，`right` 输入禁用（验证时跳过右值检查）。

| ID | 名称 | 说明 |
|----|------|------|
| 9 | `Null` | 为空 |
| 10 | `NotNull` | 不为空 |
| 11 | `True` | 为真 |
| 12 | `False` | 为假 |

### 类型约束规则

- 数组类型的长度比较运算符（`LengthGt`、`LengthGtEqual`、`LengthLt`、`LengthLtEqual`）的右值约束为整数。
- 数组类型的包含操作（`Contains`、`NotContains`）的右值可以是元素类型或数组类型。
- 字符串长度比较时，右值类型：新数据为整数，历史数据兼容字符串。
- 布尔类型右值自动填充默认值 `false`。

## 附录 C. 输出变量名保留字

以下 **12 个**标识符在输出变量名中被保留，不得用作用户定义的输出变量名。

```
true      false     and       AND
or        OR        not       NOT
null      nil       If        Switch
```

### 验证规则

输出变量名必须同时满足以下两个条件：

1. **格式正则**: `^[a-zA-Z_][a-zA-Z_$0-9]*$`
   - 必须以字母或下划线开头
   - 后续字符可以是字母、数字、下划线或美元符号

2. **保留字排除**: 变量名不得包含上述保留字作为完整单词。
   - 合法: `my_true_value`（保留字不是完整单词）
   - 非法: `true`（完整单词匹配保留字）

验证器将格式正则和保留字排除合并为一条正则进行检查。

## 附录 D. 错误消息 i18n Key 映射

以下为验证器中使用的所有 i18n key 及其对应的验证器和错误含义。i18n key 用于国际化错误消息的查找和本地化。

### D.1 通用节点验证

| i18n Key | 验证器 | 错误含义 |
|----------|--------|---------|
| `workflow_detail_node_name_error_empty` | nodeMetaValidator | 节点名称不能为空 |
| `workflow_derail_node_detail_title_max` | nodeMetaValidator | 节点名称长度不能超过 63 |
| `workflow_node_title_duplicated` | nodeMetaValidator | 节点标题重复 |
| `workflow_detail_node_error_name_empty` | inputTreeValidator / outputTreeValidator / outputTreeMetaValidator | 变量名不能为空 |
| `workflow_detail_node_error_format` | inputTreeValidator / outputTreeValidator / 多个验证器 | 变量名格式错误 |
| `workflow_detail_node_error_empty` | createValueExpressionInputValidate / inputTreeValidator | 输入不能为空 |
| `workflow_detail_node_input_duplicated` | inputTreeValidator / createNodeInputNameValidate | 输入名重复 |
| `workflow_detail_node_error_variablename_duplicated` | outputTreeValidator / OutputTreeNodeSchema | 变量名重复 |

### D.2 条件分支验证

| i18n Key | 验证器 | 错误含义 |
|----------|--------|---------|
| `workflow_detail_condition_error_refer_empty` | conditionLeftValidator | 条件左值引用为空 |
| `workflow_detail_condition_condition_empty` | conditionOperatorValidator | 条件操作符为空 |
| `workflow_detail_condition_error_enter_comparison` | conditionRightValidator | 条件右值未填写 |

### D.3 特定节点验证

| i18n Key | 验证器 | 错误含义 |
|----------|--------|---------|
| `workflow_running_results_error_code` | codeEmptyValidator | 代码不能为空 |
| `workflow_debug_wrong_json` | outputTreeValidator / createOutputsValidator | JSON 格式错误 |
| `workflow_exception_ignore_json_error` | settingOnErrorValidator | 异常处理 JSON 格式错误 |
| `workflow_detail_variable_referenced_error` | createConditionValidator / createSelectAndSetFieldsValidator | 引用变量已删除 |
| `workflow_ques_option_notempty` | questionOptionValidator | 选项内容不可为空 |
| `workflow_ques_ans_testrun_dulpicate` | questionOptionValidator / validateIntentsName | 选项内容不可重复 |
| `workflow_intent_matchlist_error1` | validateIntentsName | 意图名验证错误 1 |
| `workflow_intent_matchlist_error2` | validateIntentsName | 意图名验证错误 2 |
| `workflow_250213_01` | llmOutputTreeMetaValidator | LLM 输出变量限制（reasoning_content 保留） |

### D.4 循环 / 变量验证

| i18n Key | 验证器 | 错误含义 |
|----------|--------|---------|
| `workflow_loop_name_no_index_wrong` | BatchInputNameValidator / LoopArrayNameValidator / LoopInputNameValidator | 不允许使用 index |
| `workflow_loop_set_variable_typewrong` | VariableAssignLeftValidator | 变量类型不匹配 |
| `workflow_loop_set_variable_samewrong` | VariableAssignLeftValidator | 不能赋值给自身 |
| `workflow_detail_variable_referenced_error` | VariableAssignLeftValidator | 引用变量已删除 |

### D.5 合并节点验证

| i18n Key | 验证器 | 错误含义 |
|----------|--------|---------|
| `workflow_var_merge_name_lengthmax` | groupNameValidator | 组名长度超限 |
| `workflow_var_merge_output_namedul` | groupNameValidator | 组名重复 |
| `workflow_var_merge_var_err_noempty` | variablesValidator | 变量不能为空 |
| `workflow_var_merge_var_err_sametype` | variableValidator | 变量类型必须一致 |

### D.6 系统级验证

| i18n Key | 验证器 | 错误含义 |
|----------|--------|---------|
| `variable_240416_01` | systemVariableValidator | 不允许使用系统变量前缀 |
| `workflow_250317_01` | llmInputNameValidator | LLM 输入名特殊限制 1 |
| `workflow_250317_02` | llmInputNameValidator | LLM 输入名特殊限制 2 |

---

> **规范维护说明**: 本附录数据提取自 `coze-workflow-language-spec.json`。完整的验证规则详见各规则的 JSON 定义文件。



---


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



---


# 4. 静态语义分析 (Static Semantic Analysis)

本章定义 Coze 工作流的所有静态语义规则。这些规则在编译时检查，不需要运行时环境。

**检查能力**: `offline` — 纯静态检查，只需 AST + 符号表。

---

## 4.1 通用语义规则 (Common Semantic Rules)

适用于所有节点类型的通用规则。

### 4.1.1 节点标题验证 (SEMANTIC-FE-009/010/011)

**规则**: 节点标题必须符合格式和长度要求。

| 检查项 | 规则 | 错误消息 |
|--------|------|----------|
| 标题长度 | `len(title) <= 63` | `node title exceeds maximum length of 63 characters` |
| 标题格式 | 非空，不包含特殊字符 | `node title contains invalid characters` |

**正确示例:**
```yaml
nodeMeta:
  title: LLM Node
```

**错误示例:**
```yaml
# SEMANTIC-FE-010: 标题超过 63 字符
nodeMeta:
  title: This is a very long node title that exceeds the maximum length limit of sixty-three characters
```

### 4.1.2 值表达式验证 (SEMANTIC-FE-001)

**规则**: 值表达式必须包含合法的 `type` 和 `content`。

| type 值 | 说明 | content 要求 |
|---------|------|-------------|
| `literal` | 字面量 | 字符串/数字/布尔值 |
| `ref` | 引用 | `{source, blockID, name}` |
| `object_ref` | 对象引用 | `{source, blockID, name, path}` |

**引用来源 (source)**:
- `block-output` — 引用其他节点的输出
- `global_variable_app` — 应用级全局变量
- `global_variable_system` — 系统级全局变量
- `global_variable_user` — 用户级全局变量

**正确示例:**
```yaml
# literal 类型
input:
  type: string
  value:
    type: literal
    content: 'hello world'

# ref 类型
input:
  type: string
  value:
    type: ref
    content:
      source: block-output
      blockID: '100001'
      name: 'input_1'
```

**错误示例:**
```yaml
# SEMANTIC-FE-001: type 不在合法列表中
input:
  type: string
  value:
    type: invalid_type
    content: 'hello'

# SEMANTIC-FE-001: ref 缺少 source
input:
  type: string
  value:
    type: ref
    content:
      blockID: '100001'
      name: 'input_1'
```

---

## 4.2 节点特定语义规则 (Node-Specific Semantic Rules)

每个节点类型的特定验证规则。共覆盖 **39 种节点类型**。

### 4.2.1 Batch 节点 (type: 28)

**描述**: 批量处理

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-batch-001` | `nodeMeta` | 节点元数据验证（标题等） |  |
| `FORM-batch-002` | `inputs.inputParameters.*.name` | 批量输入参数名称验证 |  |
| `FORM-batch-003` | `inputs.inputParameters.*.input` | 批量输入参数值验证 |  |
| `FORM-batch-004` | `outputs.*.name` | 批量输出参数名称验证 |  |
| `FORM-batch-005` | `outputs.*.input` | 批量输出参数值验证 |  |

### 4.2.2 Break 节点 (type: 19)

**描述**: 循环中断

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-break-001` | `nodeMeta` | 节点元数据验证 |  |

### 4.2.3 ? (type: ?)

**描述**: ?

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-clear-conversation-history-001` | `inputParameters.0.input` | 清除会话历史第一个输入参数必填 |  |

### 4.2.4 Code 节点 (type: 5)

**描述**: 自定义代码执行

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-code-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-code-002` | `codeParams (spread from createCodeInp...` | 代码节点输入参数验证（通过createCodeInputsValidator展开） |  |
| `FORM-code-003` | `codeParams` | 代码内容不能为空验证 |  |
| `FORM-code-004` | `outputs` | 输出树结构元数据验证 |  |

**正确示例:**
```yaml
inputs:
  code:
    - name: code
      input:
        type: string
        value:
          type: literal
          content: 'return {"result": input_1}'
```

**错误示例:**
```yaml
# SEMANTIC-FE-001: code 为空
inputs:
  code:
    - name: code
      input:
        type: string
        value:
          type: literal
          content: ''
```

### 4.2.5 Continue 节点 (type: 29)

**描述**: 循环继续

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-continue-001` | `nodeMeta` | 节点元数据验证 |  |

### 4.2.6 ? (type: ?)

**描述**: ?

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-create-conversation-001` | `inputParameters.0.input` | 创建会话第一个输入参数必填 |  |

### 4.2.7 ? (type: ?)

**描述**: ?

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-create-message-001` | `inputParameters.*.input` | 创建消息输入参数验证（conversationName/role/content均required） |  |

### 4.2.8 Database 节点 (type: 12)

**描述**: 数据库操作

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-database-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-database-002` | `inputParameters.*.name` | 数据库输入参数名称验证（去重检查） |  |
| `FORM-database-003` | `inputParameters.*.input` | 数据库输入参数值必填验证 |  |
| `FORM-database-004` | `sql` | SQL语句不能为空验证 | workflow_detail_node_error_empty |
| `FORM-database-005` | `databaseInfoList` | 数据库信息列表不能为空验证 | workflow_detail_node_error_empty |

### 4.2.9 Dataset 检索节点 (type: 6)

**描述**: 知识库检索

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-dataset-search-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-dataset-search-002` | `inputs.inputParameters.Query` | 知识库Query参数必填验证 |  |
| `FORM-dataset-search-003` | `inputs.datasetParameters.datasetParam` | 知识库数据集参数不能为空验证 | workflow_detail_knowledge_error_empty |

### 4.2.10 Dataset 写入节点 (type: 27)

**描述**: 知识库写入

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-dataset-write-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-dataset-write-002` | `inputs.inputParameters.knowledge` | 知识库写入knowledge参数必填验证 |  |
| `FORM-dataset-write-003` | `inputs.datasetParameters.datasetParam` | 知识库数据集参数不能为空验证 | workflow_detail_knowledge_error_empty |
| `FORM-dataset-write-004` | `inputs.datasetWriteParameters.chunkSt...` | 自定义分隔符在separatorType=custom时必填 | datasets_custom_segmentID_error |

### 4.2.11 ? (type: ?)

**描述**: ?

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-delete-conversation-001` | `inputParameters.*.input` | 删除会话输入参数验证（conversationName required） |  |

### 4.2.12 ? (type: ?)

**描述**: ?

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-delete-message-001` | `inputParameters.*.input` | 删除消息输入参数验证（conversationName/messageId required） |  |

### 4.2.13 结束节点 (type: 2)

**描述**: 工作流出口

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-end-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-end-002` | `inputs (spread from createInputsValid...` | 结束节点输入参数验证（required=true展开） |  |
| `FORM-end-003` | `inputs.content` | 回答内容验证（仅当终止方案为使用回答内容时） |  |

### 4.2.14 ? (type: ?)

**描述**: ?

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-http-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-http-002` | `inputs.apiInfo.url` | HTTP URL验证（长度限制10000, 非空, 变量合法） | node_http_url_length_limit / node_http_url_required / node_http_url_invalid_var |
| `FORM-http-003` | `inputs.headers.*.name` | HTTP请求头名称验证（正则: 不能是保留字） | node_http_name_rule |
| `FORM-http-004` | `inputs.headers.*.input` | HTTP请求头值验证（非必填） |  |
| `FORM-http-005` | `inputs.params.*.name` | HTTP查询参数名称验证（正则: 不能是保留字） | node_http_name_rule |
| `FORM-http-006` | `inputs.params.*.input` | HTTP查询参数值验证（非必填） |  |
| `FORM-http-007` | `inputs.body.bodyData.json` | HTTP JSON Body验证（JSON语法+变量合法性） | workflow_json_syntax_error / node_http_json_required / node_http_json_invalid_var |
| `FORM-http-008` | `inputs.body.bodyData.rawText` | HTTP RawText Body变量验证（非必填） | node_http_raw_text_invalid_var |
| `FORM-http-009` | `inputs.body.bodyData.formData.*.name` | HTTP FormData字段名验证（正则: 不能是保留字） | node_http_name_rule |
| `FORM-http-010` | `inputs.body.bodyData.formData.*.input` | HTTP FormData字段值验证（非必填） |  |
| `FORM-http-011` | `inputs.body.bodyData.formURLEncoded.*...` | HTTP FormURLEncoded字段名验证（正则: 不能是保留字） | node_http_name_rule |
| `FORM-http-012` | `inputs.body.bodyData.formURLEncoded.*...` | HTTP FormURLEncoded字段值验证（非必填） |  |
| `FORM-http-013` | `auth (spread from createAuthValidator)` | HTTP认证验证规则（通过createAuthValidator展开） |  |

**正确示例:**
```yaml
inputs:
  inputParameters:
    - name: url
      input:
        type: string
        value:
          type: literal
          content: 'https://api.example.com/data'
```

**错误示例:**
```yaml
# SEMANTIC-FE-001: url 为空
inputs:
  inputParameters:
    - name: url
      input:
        type: string
        value:
          type: literal
          content: ''
```

### 4.2.15 If 节点 (type: 8)

**描述**: 条件分支

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-if-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-if-002` | `condition` | 条件分支验证（验证所有分支的左值、运算符、右值） | validateAllBranches返回的left/operator/right错误信息拼接 |

**正确示例:**
```yaml
inputs:
  branches:
    - branchKey: 'true'
      condition:
        logic: and
        conditions:
          - left:
              type: ref
              content:
                source: block-output
                blockID: '100001'
                name: 'input_1'
            operator: '1'
            right:
              type: literal
              content: 'hello'
```

**错误示例:**
```yaml
# SEMANTIC-FE-001: 缺少 operator
conditions:
  - left:
      type: ref
      content:
        source: block-output
        blockID: '100001'
        name: 'input_1'
    right:
      type: literal
      content: 'hello'
```

### 4.2.16 ImageCanvas 节点 (type: 23)

**描述**: 图片画布

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-image-canvas-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-image-canvas-002` | `inputs.inputParameters.*.input` | 图片画布输入参数值必填验证 |  |

### 4.2.17 ImageGenerate 节点 (type: 16)

**描述**: 图片生成

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-image-generate-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-image-generate-002` | `inputs.modelSetting.model` | 模型与预处理器兼容性验证 | Imageflow_not_support |
| `FORM-image-generate-003` | `inputs.prompt.prompt` | 图片生成提示词不能为空 | workflow_detail_node_error_empty |

### 4.2.18 ? (type: ?)

**描述**: ?

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-input-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-input-002` | `outputs` | 输出变量验证（名称唯一性检查） |  |

### 4.2.19 Intent 节点 (type: 22)

**描述**: 意图识别

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-intent-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-intent-002` | `inputs.inputParameters.0.input` | 意图识别第一个输入参数必填 |  |
| `FORM-intent-003` | `intents.*` | 标准模式意图名称验证（去重+格式） |  |
| `FORM-intent-004` | `quickIntents.*` | 精简模式快速意图名称验证（去重+格式） |  |

### 4.2.20 JsonStringify 节点 (type: 50)

**描述**: JSON 序列化

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-json-stringify-001` | `inputs.inputParameters.0.input` | JSON序列化第一个输入参数必填 |  |

### 4.2.21 Loop 节点 (type: 21)

**描述**: 循环

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-loop-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-loop-002` | `inputs.inputParameters.*.name` | 循环数组输入名称验证 |  |
| `FORM-loop-003` | `inputs.inputParameters.*.input` | 循环数组输入值验证 |  |
| `FORM-loop-004` | `inputs.variableParameters.*.name` | 循环变量名称验证 |  |
| `FORM-loop-005` | `inputs.variableParameters.*.input` | 循环变量值验证 |  |
| `FORM-loop-006` | `outputs.*.name` | 循环输出名称验证 |  |
| `FORM-loop-007` | `outputs.*.input` | 循环输出值验证 |  |

### 4.2.22 LTM 节点 (type: 26)

**描述**: 长期记忆

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-ltm-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-ltm-002` | `inputs.inputParameters.0.input` | 长期记忆第一个输入参数必填 |  |

### 4.2.23 Output 节点 (type: 13)

**描述**: 输出节点

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-output-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-output-002` | `inputs (spread from createInputsValid...` | 输出节点输入参数验证（required=true展开） |  |

### 4.2.24 Plugin 节点 (type: 4)

**描述**: 外部插件调用

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-plugin-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-plugin-002` | `inputs.inputParameters.*` | 插件输入参数验证（required根据API定义动态决定） |  |
| `FORM-plugin-003` | `inputs.batch.inputLists.*.name` | 批量输入参数名称验证（batchMode=single时跳过） |  |
| `FORM-plugin-004` | `inputs.batch.inputLists.*.input` | 批量输入参数值验证（batchMode=single时跳过） |  |

### 4.2.25 ? (type: ?)

**描述**: ?

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-query-conversation-history-001` | `inputParameters.*.input` | 查询会话历史输入参数验证（conversationName/rounds required） |  |

### 4.2.26 ? (type: ?)

**描述**: ?

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-query-conversation-list-001` | `inputParameters.*.input` | 查询会话列表输入参数验证（无必填字段） |  |

### 4.2.27 ? (type: ?)

**描述**: ?

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-query-message-list-001` | `inputParameters.0.input` | 查询消息列表第一个输入参数必填 |  |

### 4.2.28 Question 节点 (type: 18)

**描述**: 用户提问

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-question-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-question-002` | `inputParameters.*.name` | 问题输入参数名称验证 |  |
| `FORM-question-003` | `inputParameters.*.input` | 问题输入参数值必填验证 |  |
| `FORM-question-004` | `questionParams.question` | 问题内容不能为空 | workflow_detail_node_error_empty |
| `FORM-question-005` | `questionParams.options.*.name` | 问题选项验证（静态选项模式下非空且不重复） | workflow_ques_option_notempty / workflow_ques_ans_testrun_dulpicate |
| `FORM-question-006` | `questionParams.dynamic_option` | 动态选项验证（仅当answer_type=option且optionType=Dynamic时） |  |
| `FORM-question-007` | `questionOutputs.extractOutput` | 问题输出提取验证 |  |

**正确示例:**
```yaml
inputs:
  inputParameters:
    - name: question
      input:
        type: string
        value:
          type: literal
          content: 'What is your name?'
    - name: answer_type
      input:
        type: string
        value:
          type: literal
          content: 'option'
    - name: options
      input:
        type: list
        value:
          type: literal
          content: '["Alice", "Bob"]'
```

**错误示例:**
```yaml
# SEMANTIC-FE-001: question 为空
inputs:
  inputParameters:
    - name: question
      input:
        type: string
        value:
          type: literal
          content: ''
```

### 4.2.29 SetVariable 节点 (type: 20)

**描述**: 变量赋值

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-set-variable-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-set-variable-002` | `inputs.inputParameters.*.left` | 变量赋值左侧变量验证 |  |
| `FORM-set-variable-003` | `inputs.inputParameters.*.right` | 变量赋值右侧值验证 |  |

### 4.2.30 开始节点 (type: 1)

**描述**: 工作流入口

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-start-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-start-002` | `outputs` | 输出变量验证（名称唯一性检查） |  |
| `FORM-start-003` | `trigger.dynamicInputs.*` | 触发器动态输入验证（根据触发器配置动态决定required） | workflow_detail_node_error_empty |
| `FORM-start-004` | `trigger.parameters.*` | 触发器参数验证（仅验证正在使用的输出参数） | workflow_detail_node_error_empty |

### 4.2.31 SubWorkflow 节点 (type: 9)

**描述**: 子工作流调用

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-sub-workflow-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-sub-workflow-002` | `inputs.inputParameters.*` | 子工作流输入参数验证（required根据子工作流定义动态决定） |  |
| `FORM-sub-workflow-003` | `inputs.batch.inputLists.*.name` | 批量输入参数名称验证（batchMode=single时跳过） |  |
| `FORM-sub-workflow-004` | `inputs.batch.inputLists.*.input` | 批量输入参数值验证（batchMode=single时跳过） |  |
| `FORM-sub-workflow-005` | `settingOnError` | 错误处理设置验证 |  |

### 4.2.32 TextProcess 节点 (type: 15)

**描述**: 文本处理

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-text-process-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-text-process-002` | `inputParameters.*.input` | 文本处理输入参数值必填验证 |  |
| `FORM-text-process-003` | `concatResult` | 拼接结果验证（仅拼接模式下不能为空） | workflow_testset_required_tip(Content) |
| `FORM-text-process-004` | `delimiter` | 分隔符验证（仅分割模式下不能为空） | workflow_testset_required_tip(workflow_stringprocess_delimiter_title) |

### 4.2.33 TriggerDelete 节点 (type: 35)

**描述**: 触发器删除

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-trigger-delete-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-trigger-delete-002` | `inputs.inputParameters.userId` | 触发器删除userId必填验证 |  |

### 4.2.34 TriggerRead 节点 (type: 36)

**描述**: 触发器读取

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-trigger-read-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-trigger-read-002` | `inputs.inputParameters.userId` | 触发器读取userId必填验证 |  |

### 4.2.35 TriggerUpsert 节点 (type: 34)

**描述**: 触发器写入

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-trigger-upsert-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-trigger-upsert-002` | `inputs.fixedInputs.userId` | 触发器upsert userId必填验证 |  |
| `FORM-trigger-upsert-003` | `inputs.fixedInputs.triggerName` | 触发器名称必填验证 |  |
| `FORM-trigger-upsert-004` | `inputs.bindWorkflowId` | 绑定工作流ID必填验证 |  |
| `FORM-trigger-upsert-005` | `inputs.dynamicInputs.timeZone` | 时区必填验证 |  |
| `FORM-trigger-upsert-006` | `inputs.dynamicInputs.crontab` | 定时任务表达式必填验证（特殊取值: value.content） |  |
| `FORM-trigger-upsert-007` | `inputs.payload.*` | 触发器载荷参数验证（根据绑定工作流定义动态required） |  |

### 4.2.36 ? (type: ?)

**描述**: ?

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-update-conversation-001` | `inputParameters.*.input` | 更新会话输入参数验证（conversationName/newConversationName... |  |

### 4.2.37 ? (type: ?)

**描述**: ?

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-update-message-001` | `inputParameters.*.input` | 更新消息输入参数验证（conversationName/messageId/newConten... |  |

### 4.2.38 Variable 节点 (type: 11)

**描述**: 变量声明

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-variable-001` | `inputParameters.*.name` | 变量名称非空验证 | bot_edit_variable_field_required_error |
| `FORM-variable-002` | `inputParameters.*.input` | 变量输入参数值必填验证 |  |

### 4.2.39 VariableAssign 节点 (type: 40)

**描述**: 变量赋值

**验证规则**:

| 规则 ID | 字段 | 检查逻辑 | 错误消息 |
|---------|------|----------|----------|
| `FORM-variable-assign-001` | `nodeMeta` | 节点元数据验证 |  |
| `FORM-variable-assign-002` | `$$input_decorator$$.inputParameters.*...` | 变量赋值左侧必填验证 | variable_assignment_node_select_empty |
| `FORM-variable-assign-003` | `$$input_decorator$$.inputParameters.*...` | 变量赋值右侧必填验证 |  |

---

## 4.3 条件分支语义规则 (Condition Branch Semantic Rules)

If 节点的条件分支验证规则。

### 4.3.1 条件三元组验证

每个条件由 `left`、`operator`、`right` 三部分组成。

| 部分 | 规则 | 错误消息 |
|------|------|----------|
| cond | 条件左值(left)必须非空且通过 valueExpressionValidator 验证。当 disabled=true 时跳过验证。 | `workflow_detail_condition_error_refer_empty` |
| cond | 条件操作符(operator)必须非 nil/null。当 disabled=true 时跳过验证。 | `workflow_detail_condition_condition_empty` |
| cond | 条件右值(right)必须非空且通过 valueExpressionValidator 验证。当操作符为一元运算符时(disabled=true)跳过验证。 | `workflow_detail_condition_error_enter_comparison` |

### 4.3.2 条件运算符 (ConditionType)

| ID | 运算符 | 类型 | right 要求 |
|----|--------|------|-----------|
| 1 | Equal | 二元 | 必填 |
| 2 | NotEqual | 二元 | 必填 |
| 3 | LengthGt | 二元 | 必填 |
| 4 | LengthGtEqual | 二元 | 必填 |
| 5 | LengthLt | 二元 | 必填 |
| 6 | LengthLtEqual | 二元 | 必填 |
| 7 | Contains | 二元 | 必填 |
| 8 | NotContains | 二元 | 必填 |
| 9 | Null | 一元 | 禁用 |
| 10 | NotNull | 一元 | 禁用 |
| 11 | True | 一元 | 禁用 |
| 12 | False | 一元 | 禁用 |
| 13 | Gt | 二元 | 必填 |
| 14 | GtEqual | 二元 | 必填 |
| 15 | Lt | 二元 | 必填 |
| 16 | LtEqual | 二元 | 必填 |

### 4.3.3 一元运算符规则

当 operator 为一元运算符 (9/10/11/12) 时，right 不需要填写。

**正确示例 (一元运算符):**
```yaml
conditions:
  - left:
      type: ref
      content:
        source: block-output
        blockID: '100001'
        name: 'input_1'
    operator: '9'  # Null (一元)
    # right 不需要
```

**错误示例 (二元运算符缺少 right):**
```yaml
# SEMANTIC-FE-001: 二元运算符缺少 right
conditions:
  - left:
      type: ref
      content:
        source: block-output
        blockID: '100001'
        name: 'input_1'
    operator: '1'  # Equal (二元)
    # right 缺失!
```

---

## 4.4 输出变量语义规则 (Output Variable Semantic Rules)

### 4.4.1 输出变量名验证 (SEMANTIC-FE-013)

**规则**: 输出变量名必须是合法标识符，不能是保留字。

**名称格式**: `^[a-zA-Z_][a-zA-Z_$0-9]*$`

**保留字** (12 个):
`true`, `false`, `and`, `AND`, `or`, `OR`, `not`, `NOT`, `null`, `nil`, `If`, `Switch`

**正确示例:**
```yaml
outputs:
  - name: result
    type: string
  - name: _output
    type: integer
  - name: data1
    type: object
```

**错误示例:**
```yaml
# SEMANTIC-FE-013: 保留字
outputs:
  - name: true
    type: boolean

# SEMANTIC-FE-013: 数字开头
outputs:
  - name: 1result
    type: string

# SEMANTIC-FE-013: 包含空格
outputs:
  - name: my output
    type: string
```

### 4.4.2 输出变量 type 必填

**规则**: 每个输出变量必须声明类型。

**错误示例:**
```yaml
# SEMANTIC-FE-013: 缺少 type
outputs:
  - name: result
    # type 缺失!
```

---

## 4.5 批量模式语义规则 (Batch Mode Semantic Rules)

### 4.5.1 批量输入验证

**规则**: 批量模式下，inputLists 的 name 和 input 必填。

**skipValidate 条件**: 当 `batchMode === 'single'` 时跳过验证。

**正确示例:**
```yaml
inputs:
  batch:
    batchMode: 'batch'
    inputLists:
      - name: param1
        input:
          type: string
          value:
            type: literal
            content: 'value1'
```

**错误示例:**
```yaml
# batchMode=batch 时 name 为空
inputs:
  batch:
    batchMode: 'batch'
    inputLists:
      - name: ''
        input:
          type: string
          value:
            type: literal
            content: 'value1'
```



---


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



---

