# FE-001 交叉验证：coze-studio 前端验证 vs 我们的实现

## 数据来源
- coze-studio 前端: `frontend/packages/workflow/playground/src/node-registries/*/form-meta.tsx`
- 共享验证器: `frontend/packages/workflow/nodes/src/validators/`
- 我们的实现: `coze_yaml_compiler_v2/passes/semantic_pass.py` 中的 `_check_node_form_fields`

## 逐节点对比

### 1. LLM 节点 (type=3)

| 验证项 | coze-studio | 我们 | 差异 |
|--------|------------|------|------|
| title 非空 | ✅ nodeMetaValidate (Zod: min(1)) | ✅ title 非空 | ✅ 一致 |
| title ≤63 字符 | ✅ nodeMetaValidate (regex /^.{0,63}$/) | ✅ TITLE_MAX_LENGTH=63 | ✅ 一致 |
| title 不重复 | ✅ nodeMetaValidator.refine(isTitleRepeated) | ❌ 未实现 | **差距** |
| modelType 必填 | ✅ `inputs.modelSetting.model` (required) | ✅ modelType 非空 | ✅ 一致 |
| temperature 0-2 | ❌ 未找到显式验证 | ✅ [0,2] 范围检查 | **我们更严格** |
| maxTokens >0 | ❌ 未找到显式验证 | ✅ >0 检查 | **我们更严格** |
| inputParameters 非空 | ✅ createValueExpressionInputValidate(required) | ❌ 未检查 | **差距** |
| outputs 树验证 | ✅ llmOutputTreeMetaValidator | ❌ 未检查 | **差距** |
| input name 验证 | ✅ llmInputNameValidator | ❌ 未检查 | **差距** |
| userPrompt 条件必填 | ✅ is_up_required 时检查 | ❌ 未检查 | **差距** |

### 2. Code 节点 (type=5)

| 验证项 | coze-studio | 我们 | 差异 |
|--------|------------|------|------|
| code 非空 | ✅ codeEmptyValidator (value?.code) | ✅ code content 必填 | ✅ 一致 |
| title 非空+长度 | ✅ nodeMetaValidate | ✅ | ✅ 一致 |
| code inputs 验证 | ✅ createCodeInputsValidator | ❌ | **差距** |
| outputs 树验证 | ✅ outputTreeMetaValidator | ❌ | **差距** |

### 3. Database 节点 (type=12/42/43/44/46)

| 验证项 | coze-studio | 我们 | 差异 |
|--------|------------|------|------|
| sql 非空 | ✅ `!value → error` | ✅ sql 必填 | ✅ 一致 |
| databaseInfoList 非空 | ✅ `length===0 → error` | ✅ databaseInfoList 必填 | ✅ 一致 |
| queryLimit [1,1000] | ❌ 未找到 | ✅ [1,1000] | **我们更严格** |
| inputParameters 验证 | ✅ createValueExpressionInputValidate | ❌ | **差距** |
| title 非空+长度 | ✅ nodeMetaValidate | ✅ | ✅ 一致 |

### 4. Question 节点 (type=18)

| 验证项 | coze-studio | 我们 | 差异 |
|--------|------------|------|------|
| question 非空 | ✅ `!value → error` | ✅ question 必填 | ✅ 一致 |
| options (answer_type=option, static) | ✅ 非空+不重复 | ✅ options 必填 | ✅ 基本一致 |
| options 不重复 | ✅ duplicate check | ❌ 未检查重复 | **差距** |
| dynamic_option 验证 | ✅ valueExpressionValidator(required) | ❌ | **差距**（需要运行时） |
| outputs 树验证 | ✅ outputTreeMetaValidator | ❌ | **差距** |
| title 非空+长度 | ✅ nodeMetaValidate | ✅ | ✅ 一致 |

### 5. HTTP 节点 (type=45)

| 验证项 | coze-studio | 我们 | 差异 |
|--------|------------|------|------|
| url 非空 | ✅ expressionStringValidator(emptyMessage) | ✅ url 必填 | ✅ 一致 |
| url ≤10000 字符 | ✅ `length > 10000` | ❌ 未限制长度 | **差距** |
| url 变量格式 | ✅ invalidVar check | ❌ | **差距**（需要运行时） |
| headers name 验证 | ✅ httpNameValidationRule | ❌ | **差距** |
| title 非空+长度 | ✅ nodeMetaValidate | ✅ | ✅ 一致 |

### 6. Variable Assign 节点 (type=20/40)

| 验证项 | coze-studio | 我们 | 差异 |
|--------|------------|------|------|
| left 必填 | ✅ VariableAssignLeftValidator | ✅ left 必填 | ✅ 一致 |
| right 必填 | ✅ VariableAssignRightValidator | ✅ right 必填 | ✅ 一致 |
| title 非空+长度 | ✅ nodeMetaValidate | ✅ | ✅ 一致 |

### 7. Intent 节点 (type=22)

| 验证项 | coze-studio | 我们 | 差异 |
|--------|------------|------|------|
| first input 必填 | ✅ `inputParameters.0.input` required | ✅ first input 必填 | ✅ 一致 |
| intents 名称验证 | ✅ validateIntentsName | ❌ | **差距** |
| title 非空+长度 | ✅ nodeMetaValidate | ✅ | ✅ 一致 |

### 8. Image Generate 节点 (type=16)

| 验证项 | coze-studio | 我们 | 差异 |
|--------|------------|------|------|
| model 必填 | ✅ `inputs.modelSetting.model` | ✅ model 必填 | ✅ 一致 |
| preprocessor 兼容性 | ✅ invalidPreprocessors check | ❌ | **差距**（需要运行时） |
| title 非空+长度 | ✅ nodeMetaValidate | ✅ | ✅ 一致 |

### 9. LTM 节点 (type=26)

| 验证项 | coze-studio | 我们 | 差异 |
|--------|------------|------|------|
| first input 必填 | ✅ `inputParameters.0.input` required | ✅ first input 必填 | ✅ 一致 |
| title 非空+长度 | ✅ nodeMetaValidate | ✅ | ✅ 一致 |

### 10. Dataset 节点 (type=6/27)

| 验证项 | coze-studio | 我们 | 差异 |
|--------|------------|------|------|
| knowledge 必填 | ✅ `datasetParamFieldName` non-empty | ✅ knowledge 必填 | ✅ 一致 |
| Query 必填 (search) | ✅ `inputParameters.Query` required | ❌ | **差距** |
| knowledge input 必填 (write) | ✅ `inputParameters.knowledge` required | ❌ | **差距** |
| separator 验证 (write) | ✅ custom separator 非空 | ❌ | **差距** |
| title 非空+长度 | ✅ nodeMetaValidate | ✅ | ✅ 一致 |

## 通用验证器对比

| 验证器 | coze-studio | 我们 | 可静态化 |
|--------|------------|------|----------|
| nodeMetaValidate (title) | ✅ 所有节点通用 | ✅ 所有节点通用 | ✅ |
| title 不重复 | ✅ isTitleRepeated | ❌ | ✅ 可实现 |
| inputParameters 非空 | ✅ createValueExpressionInputValidate | ❌ 部分 | ✅ 可实现 |
| outputs 树验证 | ✅ outputTreeMetaValidator | ❌ | ✅ 可实现 |
| settingOnError | ✅ settingOnErrorValidator | ❌ | 部分（JSON合法性可检查） |

## 汇总

### 我们覆盖了的核心验证（12 项）
1. ✅ title 非空 (所有节点)
2. ✅ title ≤63 字符 (所有节点)
3. ✅ LLM modelType 必填
4. ✅ LLM temperature [0,2]
5. ✅ LLM maxTokens >0
6. ✅ Code code 非空
7. ✅ Database sql 非空
8. ✅ Database databaseInfoList 非空
9. ✅ Database queryLimit [1,1000]
10. ✅ Question question 非空
11. ✅ Question options 必填 (answer_type=option)
12. ✅ HTTP url 必填
13. ✅ Variable Assign left/right 必填
14. ✅ Intent first input 必填
15. ✅ Image Generate model 必填
16. ✅ LTM first input 必填
17. ✅ Dataset knowledge 必填

### 可静态化但我们未实现的（6 项，按优先级排序）
1. **P1-1**: title 不重复 — 需要跨节点检查，可静态实现
2. **P1-2**: Question options 不重复 — 可静态实现
3. **P1-3**: HTTP url ≤10000 字符 — 可静态实现
4. **P1-4**: inputParameters 必填检查 — 需要理解各节点的 required 字段配置
5. **P1-5**: outputs 树验证 — 需要理解输出变量类型系统
6. **P1-6**: Dataset Query/knowledge input 必填 — 可静态实现

### 不可静态化（需要运行时/UI 上下文）
1. title 不重复（需要遍历所有节点 — 可以做）
2. inputParameters 值表达式验证（需要变量解析上下文）
3. url 变量格式验证（需要变量系统）
4. Image preprocessor 兼容性（需要模型配置）
5. dynamic_option 验证（需要变量系统）
6. settingOnError JSON 合法性（部分可做）
