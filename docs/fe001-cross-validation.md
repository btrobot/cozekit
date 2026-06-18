# FE-001 交叉验证报告：Compiler vs coze-studio

## 验证方法

对比 coze-studio 前端 `formMeta.validate` 中每个节点的验证规则与编译器 `semantic_pass.py` 中的 FE-001 实现。

---

## 1. 通用验证（所有节点）

| 规则 | coze-studio | 编译器 | 状态 |
|------|------------|--------|------|
| 标题非空 | `nodeMetaValidator` → z.string().min(1) | FE-009 | ✅ 一致 |
| 标题最大63字符 | `nodeMetaValidator` → regex `^.{0,63}$` | FE-010 (TITLE_MAX_LENGTH=63) | ✅ 一致 |
| 标题唯一 | `nodeMetaValidator` → refine isTitleRepeated | FE-011 | ✅ 一致 |

## 2. 输出变量验证（所有有outputs的节点）

| 规则 | coze-studio | 编译器 | 状态 |
|------|------------|--------|------|
| 名称非空 | OutputTreeNodeSchema → z.string().min(1) | FE-013 | ✅ 一致 |
| 名称格式 | regex `^(?!.*\b(reserved)\b)[a-zA-Z_][a-zA-Z_$0-9]*$` | FE-013 OUTPUT_NAME_PATTERN | ✅ 一致 |
| 保留字 | 12个: true,false,and,AND,or,OR,not,NOT,null,nil,If,Switch | FE-013 OUTPUT_RESERVED_NAMES | ✅ 一致 |
| 类型必填 | OutputTreeNodeSchema → `type: z.number()` | FE-013 (刚实现) | ✅ 一致 |
| 同级唯一 | OutputTreeUniqueNameSchema → findDuplicates | FE-013 (刚实现) | ✅ 一致 |
| defaultValue JSON校验 | checkObjectDefaultValue → jsonSchemaValidator | ❌ 未实现 | ⚠️ 缺口 |

## 3. 输入参数验证（通用 inputTreeValidator）

| 规则 | coze-studio | 编译器 | 状态 |
|------|------------|--------|------|
| 名称非空 | InputTreeValidator.validateName | ❌ 无通用输入名校验 | ⚠️ 缺口 |
| 名称格式 | VARIABLE_NAME_REGEX | ❌ 无通用输入名校验 | ⚠️ 缺口 |
| 值非空 | InputTreeValidator.validateInput → ValueExpression.isEmpty | 部分（各节点单独检查） | ⚠️ 部分 |
| 同级名称唯一 | InputTreeValidator.validateName → foundSames.length > 1 | ❌ 无通用输入名校验 | ⚠️ 缺口 |

## 4. LLM 节点 (type 3)

| 规则 | coze-studio | 编译器 | 状态 |
|------|------------|--------|------|
| modelType 必填 | formMeta implicit (model select required) | ✅ _check_llm_fields | ✅ 一致 |
| prompt 非空 | `createValueExpressionInputValidate({ required: true })` | ❌ 未检查 | ⚠️ 缺口 |
| temperature 0-2 | 无前端校验（后端校验） | ✅ _check_llm_fields | ✅ 编译器额外 |
| maxTokens > 0 | 无前端校验 | ✅ _check_llm_fields | ✅ 编译器额外 |
| 输出名称格式 | llmOutputTreeMetaValidator (同OutputTreeSchema) | ✅ FE-013 | ✅ 一致 |
| 输入名称格式 | llmInputNameValidator (nameValidationRule) | ❌ 未检查 | ⚠️ 缺口 |
| 输入名称唯一 | llmInputNameValidator (sameVisionInputs) | ❌ 未检查 | ⚠️ 缺口 |

## 5. Question 节点 (type 17)

| 规则 | coze-studio | 编译器 | 状态 |
|------|------------|--------|------|
| question 内容非空 | `value ? undefined : error` | ✅ _check_question_fields | ✅ 一致 |
| 选项内容非空 | `questionOptionValidator` → item.name.trim() === '' | ❌ 未检查 | ⚠️ 缺口 |
| 选项不重复 | `questionOptionValidator` → seenValues.has | ✅ _check_question_option_duplicates | ✅ 一致 |
| 动态选项值非空 | `createValueExpressionInputValidate({ required: true })` | ❌ 未检查 | ⚠️ 缺口 |
| 输入参数值非空 | `createValueExpressionInputValidate({ required: true })` | ❌ 未检查 | ⚠️ 缺口 |

## 6. Code 节点 (type 5)

| 规则 | coze-studio | 编译器 | 状态 |
|------|------------|--------|------|
| 代码内容非空 | `codeEmptyValidator` → value.code | ❌ 未检查 | ⚠️ 缺口 |
| 输入参数验证 | `createInputTreeValidator` (名称+值) | ❌ 未检查 | ⚠️ 缺口 |
| 输出验证 | `outputTreeMetaValidator` | ✅ FE-013 | ✅ 一致 |

## 7. HTTP 节点 (type 45)

| 规则 | coze-studio | 编译器 | 状态 |
|------|------------|--------|------|
| URL 非空 | form required | ✅ _check_http_fields | ✅ 一致 |
| URL 最大长度 | 无前端校验 | ✅ (10000) | ✅ 编译器额外 |

## 8. Database 节点 (type 30/31)

| 规则 | coze-studio | 编译器 | 状态 |
|------|------------|--------|------|
| SQL 非空 | form required | ✅ _check_database_fields | ✅ 一致 |
| 数据库选择 | form required | ✅ _check_database_fields | ✅ 一致 |
| queryLimit 范围 | form range | ✅ _check_database_fields | ✅ 一致 |

## 9. Variable Assign (type 20/40)

| 规则 | coze-studio | 编译器 | 状态 |
|------|------------|--------|------|
| left 必填 | `createValueExpressionInputValidate({ required: true })` | ✅ _check_variable_assign_fields | ✅ 一致 |
| right 必填 | `createValueExpressionInputValidate({ required: true })` | ✅ _check_variable_assign_fields | ✅ 一致 |

## 10. 其他节点

| 节点 | coze-studio 规则 | 编译器 | 状态 |
|------|-----------------|--------|------|
| Intent (24) | 输入值必填 | ✅ _check_intent_fields | ✅ 一致 |
| Image Generate (16) | model 必填 | ✅ _check_image_generate_fields | ✅ 一致 |
| LTM (26) | 输入值必填 | ✅ _check_ltm_fields | ✅ 一致 |
| Dataset (6/27) | knowledge 必填 | ✅ _check_dataset_fields | ✅ 一致 |
| VariableMerge | mergeGroups 必填 | ✅ _check_variable_merge_fields | ✅ 一致 |
| Plugin (4) | 输入格式校验 | ✅ _check_plugin_fields | ✅ 一致 |
| SubWorkflow (9) | 输入格式校验 | ✅ _check_subworkflow_fields | ✅ 一致 |
| Batch (21) | 输入/输出名称唯一性 | ❌ 未检查 | ⚠️ 缺口 |
| Loop (22) | 输入/输出名称唯一性 | ❌ 未检查 | ⚠️ 缺口 |
| TextProcess | concat 内容必填 | ✅ _check_text_process_fields | ✅ 一致 |
| Trigger | userId 必填 | ✅ _check_trigger_fields | ✅ 一致 |

## 11. 端口连接验证

| 规则 | coze-studio | 编译器 | 状态 |
|------|------------|--------|------|
| 子画布入口端口 | validateSubCanvasPort | FE-006 | ✅ 一致 |
| 子画布出口端口 | validateSubCanvasPort | FE-007 | ✅ 一致 |
| 异常处理端口 | validateSettingOnErrorPort | ❌ 未检查 | ⚠️ 缺口 |

---

## 汇总

### ✅ 已对齐（编译器 = coze-studio）：22 项
### ⚠️ 缺口（编译器缺失）：15 项
### ✅ 编译器额外（超出 coze-studio）：4 项

## 缺口优先级

| 优先级 | 缺口 | 影响范围 | 建议 |
|--------|------|---------|------|
| P0 | 输入参数名称格式+唯一性 | 所有有输入的节点 | 实现通用 inputTree 验证 |
| P0 | 输入参数值非空 | 所有有输入的节点 | 实现通用 inputTree 验证 |
| P1 | LLM prompt 非空 | LLM 节点 | 补充检查 |
| P1 | Code 代码内容非空 | Code 节点 | 补充检查 |
| P1 | Question 选项内容非空 | Question 节点 | 补充检查 |
| P2 | Batch/Loop 输入输出名称唯一性 | Batch/Loop 节点 | 补充检查 |
| P2 | 异常处理端口连接 | 有 settingOnError 的节点 | 补充检查 |
| P3 | 输出 defaultValue JSON 校验 | 输出变量 | 低优先级 |
| P3 | Question 动态选项值非空 | Question 节点 | 低优先级 |

---

## 更新记录

### 2026-06-17: FE-014 实现

补齐 P0 缺口：通用输入参数验证。

**新增规则 SEMANTIC-FE-014:**
- 输入参数名称非空
- 输入参数名称格式（与输出变量共用 OUTPUT_NAME_PATTERN，匹配 coze-studio VARIABLE_NAME_REGEX）
- 输入参数值非空（ref 类型检查 name 或 path，literal 类型检查 name）
- 同级输入参数名称唯一性

**测试:** 18 个测试用例（tests/rules/FE_014/test_input_tree.py）

**剩余缺口状态:**
| 优先级 | 缺口 | 状态 |
|--------|------|------|
| P0 | 输入参数名称格式+唯一性+值非空 | ✅ 已实现 (FE-014) |
| P1 | LLM prompt 非空 | 待实现 |
| P1 | Code 代码内容非空 | 待实现 |
| P1 | Question 选项内容非空 | 待实现 |

### 2026-06-17: P1 缺口补齐

**FE-014 通用输入参数验证:**
- 名称非空
- 名称格式（OUTPUT_NAME_PATTERN，匹配 coze-studio VARIABLE_NAME_REGEX）
- 值非空（ref 类型检查 name/path，literal 类型检查 name）
- 同级名称唯一性
- 测试: 18 个用例

**FE-001 LLM prompt 非空:**
- 检查 llmParam 中 prompt 参数是否存在且非空
- 测试: 更新 _make_llm_yaml helper

**FE-001 Question 选项内容非空:**
- 检查选项 name 字段是否为空
- 匹配 coze-studio questionOptionValidator
- 测试: 已有覆盖

**剩余缺口状态:**
| 优先级 | 缺口 | 状态 |
|--------|------|------|
| P0 | 输入参数名称格式+唯一性+值非空 | ✅ 已实现 (FE-014) |
| P1 | LLM prompt 非空 | ✅ 已实现 |
| P1 | Code 代码内容非空 | ✅ 已实现 (已有) |
| P1 | Question 选项内容非空 | ✅ 已实现 |
| P2 | Batch/Loop 输入输出名称唯一性 | 待实现 |
| P2 | 异常处理端口连接 | 待实现 |

### 2026-06-17: P2 缺口补齐

**Batch/Loop 输入输出名称唯一性:**
- FE-014 扩展支持 loop 节点的 variable_parameters
- 测试: 21 个用例 (test_batch.py + test_loop.py)

**异常处理端口连接:**
- FE-008 已实现 (exception port connectivity)
- 检查 exception branch 设置时端口是否有出边

**最终缺口状态:**
| 优先级 | 缺口 | 状态 |
|--------|------|------|
| P0 | 输入参数名称格式+唯一性+值非空 | ✅ 已实现 (FE-014) |
| P1 | LLM prompt 非空 | ✅ 已实现 |
| P1 | Code 代码内容非空 | ✅ 已实现 (已有) |
| P1 | Question 选项内容非空 | ✅ 已实现 |
| P2 | Batch/Loop 输入输出名称唯一性 | ✅ 已实现 |
| P2 | 异常处理端口连接 | ✅ 已实现 (FE-008) |
| P3 | 输出 defaultValue JSON 校验 | 低优先级，暂不实现 |
