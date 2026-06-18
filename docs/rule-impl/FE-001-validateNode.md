# FE-001: validateNode — 节点级静态字段验证

## 规则定义

**规则编号**: FE-001  
**规则名称**: 每个节点通过 validateNode  
**原始描述**: 每个节点必须通过前端聚合 `validateNode`  
**检查类型**: 语义检查 (SEMANTIC-FE)  
**检查时机**: 编译时静态分析  
**适用范围**: **所有节点类型**（不只是 LLM）

---

## Coze Studio 原始实现

### 检查入口

在 `frontend/packages/workflow/playground/src/services/workflow-validation-service.ts` 中：

```typescript
public async validateNode(node: WorkflowNodeEntity): Promise<ValidateResult> {
    const nodeErrorResult = this.validateNodeError(node);
    const formValidateResult = await this.validateForm(node);
    const subCanvasPortValidateResult = this.validateSubCanvasPort(node);
    const settingOnErrorResult = this.validateSettingOnErrorPort(node);
    // ... 合并结果
}
```

### 四项检查

| 检查项 | 方法 | 说明 |
|--------|------|------|
| 节点错误 | `validateNodeError(node)` | 检查节点是否已有错误标记 |
| **表单验证** | `validateForm(node)` | 验证节点表单字段（核心） |
| 子画布端口 | `validateSubCanvasPort(node)` | 验证 Loop/Batch 子画布端口连接 |
| 异常端口 | `validateSettingOnErrorPort(node)` | 验证异常处理端口连接 |

### 表单验证机制

表单验证通过 `FlowNodeFormData` 的 `getNodeError` 实现，依赖：
- **前端 UI 运行时** — 表单模型必须已初始化
- **表单 Schema** — 每个节点类型定义自己的表单结构和验证规则
- **Zod 验证器** — 使用 Zod schema 进行字段级验证

### 通用验证规则（所有节点）

在 `frontend/packages/workflow/playground/src/nodes-v2/materials/node-meta-validate.ts` 中：

```typescript
export const nodeMetaValidate: Validate = ({ value, context }) => {
  const res = nodeMetaValidator({
    value,
    context,
    options: {},
  });
  // ...
};
```

**所有节点都必须通过的验证：**
1. **标题必填** — `nodeMeta.title` 不能为空
2. **标题长度** — 不能超过 63 个字符
3. **标题唯一** — 同一 playground 上下文中标题必须唯一

### 节点特定验证规则

每个节点类型有自己的表单验证规则，定义在各自的 `form-meta.tsx` 中：

| 节点类型 | 文件路径 | 特定验证规则 |
|----------|----------|-------------|
| **LLM** | `nodes-v2/llm/llm-form-meta.tsx` | modelType 必填、输出变量名格式、输入参数名唯一 |
| **Question** | `node-registries/question/form-meta.tsx` | question 必填、选项内容非空/不重复、动态选项必填 |
| **Variable Assign** | `nodes-v2/variable-assign/form-meta.tsx` | 左值必填、右值必填 |
| **Variable Merge** | `nodes-v2/variable-merge/variable-merge-form-meta.tsx` | 合并变量配置验证 |
| **Plugin** | `node-registries/plugin/form-meta.tsx` | 插件选择验证 |
| **Input** | `node-registries/input/form-meta.tsx` | 输入参数验证 |
| **LTM** | `node-registries/ltm/form-meta.tsx` | LTM 配置验证 |
| **Trigger** | `node-registries/trigger-upsert/form-meta.tsx` | 触发器配置验证 |
| **Database** | `node-registries/database-*/form-meta.tsx` | 数据库操作验证 |
| **Chat** | `nodes-v2/chat/*/form-meta.tsx` | 聊天相关节点验证 |
| ... | ... | ... |

**共有 39 个节点类型有表单验证规则。**

### LLM 节点示例

在 `frontend/packages/workflow/playground/src/nodes-v2/llm/llm-form-meta.tsx` 中：

```typescript
validate: {
    nodeMeta: nodeMetaValidate,  // 通用标题验证
    outputs: llmOutputTreeMetaValidator,  // 输出变量名格式验证
    '$$input_decorator$$.inputParameters.*.name': llmInputNameValidator,  // 输入参数名验证
    '$$input_decorator$$.inputParameters.*.input': 
      createValueExpressionInputValidate({ required: true }),  // 输入值必填
    // ...
}
```

**LLM 节点特定验证：**
1. **modelType 必填** — 必须选择模型
2. **输出变量名格式** — 不能是保留字，必须匹配标识符规则
3. **输入参数名唯一** — 同一节点内参数名不能重复
4. **输入值必填** — 每个输入参数必须有值

### Question 节点示例

在 `frontend/packages/workflow/playground/src/node-registries/question/form-meta.tsx` 中：

```typescript
validate: {
    nodeMeta: nodeMetaValidate,
    'inputParameters.*.name': createNodeInputNameValidate({ ... }),
    'inputParameters.*.input': createValueExpressionInputValidate({ required: true }),
    'questionParams.question': ({ value }) => 
      value ? undefined : '参数值不可为空',
    'questionParams.options.*.name': ({ value, formValues }) => 
      // 选项内容非空、不重复
    'questionParams.dynamic_option': ({ value, formValues }) => 
      // 动态选项必填
    'questionOutputs.extractOutput': outputTreeMetaValidator,
}
```

---

## 我们的实现现状

### 已实现

| 节点类型 | 验证规则 | 状态 |
|----------|----------|------|
| **所有节点** | 标题必填、长度、唯一 | ✅ FE-009/010/011 |
| **LLM** (type 3) | modelType 必填 | ✅ FE-001 |
| **LLM** (type 3) | temperature 范围 [0, 2] | ✅ FE-001 |
| **LLM** (type 3) | maxTokens > 0 | ✅ FE-001 |
| **Question** (type 18) | question 必填 | ✅ FE-001 |
| **Question** (type 18) | 选项必填 (answer_type=option) | ✅ FE-001 |
| **Code** (type 5) | code 内容必填 | ✅ FE-001 |
| **Database** (types 12/42/43/44/46) | SQL 必填 | ✅ FE-001 |
| **Database** (types 12/42/43/44/46) | databaseInfoList 必填 | ✅ FE-001 |
| **Database Query** (type 43) | queryLimit 范围 [1, 1000] | ✅ FE-001 |
| **HTTP** (type 45) | URL 必填 | ✅ FE-001 |
| **Variable Assign** (types 20/40) | left 必填 | ✅ FE-001 |
| **Variable Assign** (types 20/40) | right 必填 | ✅ FE-001 |
| **Intent** (type 22) | 第一个输入必填 | ✅ FE-001 |
| **Image Generate** (type 16) | model 必填 | ✅ FE-001 |
| **LTM** (type 26) | 第一个输入必填 | ✅ FE-001 |
| **Dataset** (types 6/27) | knowledge 必填 | ✅ FE-001 |

### 未实现（需要扩展）

| 节点类型 | 验证规则 | 原因 |
|----------|----------|------|
| **Question** | 选项不重复 | 需要更复杂的逻辑 |
| **Question** | 动态选项必填 | 需要条件判断 |
| **Plugin** | 插件选择验证 | 需要提取 pluginParam |
| **LLM** | 输出变量名格式 | 需要类型系统 |
| **LLM** | 输入参数名唯一 | 需要作用域分析 |
| **Chat nodes** (types 37-59) | 各节点特定验证 | 需要逐个实现 |
| **Trigger nodes** (types 34-36) | userId 必填 | 需要提取 triggerParam |

---

## 设计理念

| 维度 | Coze Studio | 我们的编译器 |
|------|-------------|-------------|
| **检查方式** | 运行时表单验证 | 静态分析 |
| **依赖** | 前端 UI 运行时 | 无运行时依赖 |
| **检查时机** | 用户交互时 | 编译时 |
| **检查范围** | 所有表单字段 | 可静态推断的字段 |
| **节点覆盖** | 39 个节点类型 | 目前仅 LLM |

### 实现方案

#### 1. AST 扩展

在 `ast/workflow_ast.py` 中添加 `node_specific_params` 字段：

```python
@dataclass(frozen=True)
class NodeAST:
    # ... 其他字段 ...
    # Node-specific parameters (e.g., llmParam for LLM nodes)
    node_specific_params: tuple[ParameterAST, ...] = ()
```

#### 2. AST Builder 扩展

在 `ast/builder.py` 中添加节点特定参数提取：

```python
@staticmethod
def _extract_node_specific_params_raw(
    node_type: str,
    inputs_obj: dict,
    data: dict,
) -> list:
    """Extract node-specific parameters based on node type."""
    # LLM nodes (type 3): extract llmParam
    if node_type == '3':
        llm_params = inputs_obj.get('llmParam', [])
        return llm_params if isinstance(llm_params, list) else []
    
    # Code nodes (type 5): extract codeParam  
    if node_type == '5':
        code_params = inputs_obj.get('codeParam', [])
        return code_params if isinstance(code_params, list) else []
    
    # Question nodes (type 18): extract questionParam
    if node_type == '18':
        q_params = inputs_obj.get('questionParam', [])
        return q_params if isinstance(q_params, list) else []
    
    return []
```

#### 3. 语义验证实现

在 `passes/semantic_pass.py` 中添加验证逻辑：

```python
def _check_node_specific_fields(self, ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """FE-001: validate node-specific fields."""
    for canvas in ctx.sema.canvases():
        for node in canvas.nodes:
            if node.node_type == '3':  # LLM node
                self._check_llm_fields(node, diagnostics)
            elif node.node_type == '18':  # Question node
                self._check_question_fields(node, diagnostics)
            # ... 其他节点类型
```

---

## 测试用例

### 测试文件

`tests/test_semantic_fe.py::TestFE001NodeSpecificFields`

### 测试覆盖 (28 tests)

| 测试类 | 节点类型 | 测试数 |
|--------|----------|--------|
| `TestFE001NodeSpecificFields` | LLM (type 3) | 5 |
| `TestFE001QuestionNodeFields` | Question (type 18) | 3 |
| `TestFE001CodeNodeFields` | Code (type 5) | 3 |
| `TestFE001DatabaseNodeFields` | Database (types 12/43) | 6 |
| `TestFE001HTTPNodeFields` | HTTP (type 45) | 3 |
| `TestFE001VariableAssignFields` | Variable Assign (types 20/40) | 3 |
| `TestFE001IntentNodeFields` | Intent (type 22) | 2 |
| `TestFE001ImageGenerateFields` | Image Generate (type 16) | 2 |
| `TestFE001LTMNodeFields` | LTM (type 26) | 2 |
| `TestFE001DatasetNodeFields` | Dataset (types 6/27) | 3 |
| `TestFE001DatabaseVariants` | Database (types 42/43/44/46) | 4 (parametrized) |

---

## 后续扩展计划

### 短期（可静态分析）

1. ✅ **Question 节点**: question 必填、选项必填
2. ✅ **Code 节点**: code 内容必填
3. ✅ **Database 节点**: SQL 必填、databaseInfoList 必填、queryLimit 范围
4. ✅ **HTTP 节点**: URL 必填
5. ✅ **Variable Assign 节点**: 左值/右值必填
6. ✅ **Intent 节点**: 第一个输入必填
7. ✅ **Image Generate 节点**: model 必填
8. ✅ **LTM 节点**: 第一个输入必填
9. ✅ **Dataset 节点**: knowledge 必填
10. **Chat 节点** (types 37-59): 各节点特定验证
11. **Trigger 节点** (types 34-36): userId 必填

### 中期（需要类型系统）

1. **输出变量名格式**（所有节点）:
   - 不能是保留字
   - 必须匹配标识符规则

2. **输入参数名唯一**（所有节点）:
   - 同一节点内参数名不能重复

### 长期（需要运行时）

1. **模型存在性验证**（LLM）:
   - 需要查询模型 API

2. **插件存在性验证**（Plugin）:
   - 需要查询插件 API

---

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `ast/workflow_ast.py` | 修改 | 添加 `node_specific_params` 字段 |
| `ast/builder.py` | 修改 | 添加节点特定参数提取，修复字面值提取 |
| `passes/semantic_pass.py` | 修改 | 添加 FE-001 验证逻辑 |
| `passes/syntax/syntax_pass.py` | 修改 | 修复 SYNTAX-019 排除字面值 |
| `tests/test_semantic_fe.py` | 修改 | 添加 FE-001 测试用例 |
| `docs/v1-v2-rule-mapping-table.md` | 修改 | 更新规则状态 |
