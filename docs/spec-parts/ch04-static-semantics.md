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
