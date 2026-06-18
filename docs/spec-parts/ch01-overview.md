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
