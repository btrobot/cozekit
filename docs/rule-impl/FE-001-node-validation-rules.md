# FE-001: Node Validation Rules Reference

**Date**: 2026-06-17  
**Source**: coze-studio frontend/packages/workflow/playground/src  
**Total Form-Meta Files**: 46  
**Total Node Types**: 39  

---

## Common Rules (All Nodes)

All nodes with `nodeMeta: nodeMetaValidate` must pass:

| Rule | Description | Static? |
|------|-------------|---------|
| Title Required | `nodeMeta.title` cannot be empty | ✅ |
| Title Length | `nodeMeta.title` ≤ 63 characters | ✅ |
| Title Unique | Title must be unique in workflow | ✅ |

**Implementation Status**: ✅ Implemented as FE-009/010/011

---

## Node-Specific Rules

### LLM (type 3)

**File**: `nodes-v2/llm/llm-form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| modelType Required | `llmParam.modelType` | Must select a model | ✅ |
| temperature Range | `llmParam.temperature` | Must be in [0, 2] | ✅ |
| maxTokens Positive | `llmParam.maxTokens` | Must be > 0 | ✅ |
| Input Name Format | `inputParameters.*.name` | Must match identifier regex | ⚠️ |
| Input Value Required | `inputParameters.*.input` | Must have value | ⚠️ |
| Output Name Format | `outputs.*.name` | Must match identifier regex, not reserved word | ⚠️ |

**Implementation Status**: ✅ modelType, temperature, maxTokens implemented

---

### Question (type 18)

**File**: `node-registries/question/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Question Required | `questionParams.question` | Question content cannot be empty | ✅ |
| Option Name Required | `questionParams.options.*.name` | Option content required (when answer_type=option, option_type=static) | ✅ |
| Option Name Unique | `questionParams.options.*.name` | Options cannot be duplicated | ✅ |
| Dynamic Option Required | `questionParams.dynamic_option` | Required (when answer_type=dynamic) | ⚠️ |
| Input Name Format | `inputParameters.*.name` | Parameter name format | ⚠️ |
| Output Name Format | `questionOutputs.extractOutput` | Output variable name format | ⚠️ |

**Implementation Status**: ✅ Partially implemented (question required, options required when answer_type=option)

---

### Database (type 12/42/43/44/46)

**Files**: 
- `node-registries/database/database-base/form-meta.tsx`
- `node-registries/database/database-create/database-create-form-meta.tsx`
- `node-registries/database/database-delete/database-delete-form-meta.tsx`
- `node-registries/database/database-query/database-query-form-meta.tsx`
- `node-registries/database/database-update/database-update-form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| SQL Required | `sql` | SQL statement cannot be empty | ✅ |
| Database Info Required | `databaseInfoList` | Must select database, non-empty | ✅ |
| Query Limit Range | `queryLimit` | Must be in [1, 1000] (query only) | ✅ |
| Input Name Format | `inputParameters.*.name` | Parameter name format | ⚠️ |
| Input Value Required | `inputParameters.*.input` | Must have value | ⚠️ |
| Condition Required | `conditionList` | Condition fields required (delete/query/update) | ⚠️ |

**Implementation Status**: ✅ SQL required, databaseInfoList required, queryLimit range implemented

---

### Code (type 5)

**File**: `node-registries/code/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Code Required | `codeParam.code` | Code content cannot be empty | ✅ |
| Input Name Format | `inputParameters.*.name` | Parameter name format | ⚠️ |
| Output Name Format | `outputs` | Output variable name format | ⚠️ |

**Implementation Status**: ✅ code required implemented

---

### Loop (type 21)

**File**: `node-registries/loop/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Loop Array Name | `loopArray.*.name` | Array variable name format | ⚠️ |
| Loop Variable Name | `loopVariables.*.name` | Loop variable name format | ⚠️ |
| Loop Output Name | `loopOutputs.*.name` | Output variable name format | ⚠️ |

**Implementation Status**: ❌ Not implemented

---

### Batch (type 28)

**File**: `node-registries/batch/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Input List Name | `inputLists.*.name` | Input variable name format | ⚠️ |
| Input Value Required | `inputLists.*.input` | Must have value | ⚠️ |
| Output List Name | `outputLists.*.name` | Output variable name format | ⚠️ |

**Implementation Status**: ❌ Not implemented

---

### Plugin (type 4)

**File**: `node-registries/plugin/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Input Required | `inputs.inputParameters.*` | Required fields from API definition | ⚠️ |
| Batch Input Name | `inputs.batch.inputLists.*.name` | Parameter name format | ⚠️ |

**Implementation Status**: ❌ Not implemented

---

### SubWorkflow (type 9)

**File**: `node-registries/sub-workflow/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Input Required | `inputs.inputParameters.*` | Required fields from definition | ⚠️ |
| Batch Input Name | `inputs.batch.inputLists.*.name` | Parameter name format | ⚠️ |

**Implementation Status**: ❌ Not implemented

---

### Variable Assign (type 20/40)

**Files**: 
- `node-registries/set-variable/form-meta.tsx`
- `nodes-v2/variable-assign/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Left Required | `inputParameters.*.left` | Variable selection required | ✅ |
| Right Required | `inputParameters.*.right` / `inputParameters.*.input` | Value required | ✅ |

**Implementation Status**: ✅ left/right required implemented

---

### Intent (type 22)

**File**: `node-registries/intent/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Input Required | `inputs.inputParameters.0.input` | First input required | ✅ |
| Intent Name | `intents.*` / `quickIntents.*` | Intent name validation (unique, format) | ⚠️ |

**Implementation Status**: ✅ first input required implemented

---

### HTTP (type 45)

**File**: `node-registries/http/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| URL Required | `url` | URL cannot be empty | ✅ |
| Input Name Format | `inputParameters.*.name` | Parameter name format | ⚠️ |
| Input Value Required | `inputParameters.*.input` | Must have value | ⚠️ |

**Implementation Status**: ✅ URL required implemented

---

### Start (type 1)

**File**: `node-registries/start/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Output Name Format | `outputs` | Output variable name format, unique | ⚠️ |
| Trigger Input Required | `trigger.dynamicInputs.*` | Required when trigger enabled | ⚠️ |

**Implementation Status**: ❌ Not implemented

---

### Output (type 13)

**File**: `node-registries/output/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Input Required | `inputParameters.*` | All inputs required | ⚠️ |

**Implementation Status**: ❌ Not implemented

---

### Input (type 30)

**File**: `node-registries/input/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Output Name Format | `outputs` | Output variable name format, unique | ⚠️ |

**Implementation Status**: ❌ Not implemented

---

### Text Process (type 15)

**File**: `node-registries/text-process/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Input Required | `inputParameters.*.input` | Must have value | ⚠️ |
| Concat Result | `concatResult` | Concatenation format validation | ⚠️ |

**Implementation Status**: ❌ Not implemented

---

### LTM (type 26)

**File**: `node-registries/ltm/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Input Required | `inputs.inputParameters.0.input` | First input required | ✅ |

**Implementation Status**: ✅ first input required implemented

---

### Image Generate (type 16)

**File**: `node-registries/image-generate/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Model Required | `inputs.modelSetting.model` | Must select model | ✅ |

**Implementation Status**: ✅ model required implemented

---

### Image Canvas (type 23)

**File**: `node-registries/image-canvas/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Input Required | `inputs.inputParameters.*.input` | Must have value | ⚠️ |

**Implementation Status**: ❌ Not implemented

---

### Dataset Search/Write (type 6/27)

**Files**: 
- `node-registries/dataset/dataset-search/form-meta.tsx`
- `node-registries/dataset/dataset-write/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| Knowledge Required | `inputs.inputParameters.knowledge` | Must select knowledge base | ✅ |

**Implementation Status**: ✅ knowledge required implemented

---

### Chat Nodes (type 37-57)

**Files**: `nodes-v2/chat/*/form-meta.tsx`

| Node Type | Type ID | Key Rules |
|-----------|---------|-----------|
| QueryMessageList | 37 | input required |
| ClearContext | 38 | - |
| CreateConversation | 39 | input required |
| VariableAssign | 40 | left/right required |
| DatabaseUpdate | 42 | SQL, database required |
| DatabaseQuery | 43 | SQL, database, limit range |
| DatabaseDelete | 44 | SQL, database, condition |
| Http | 45 | URL required |
| DatabaseCreate | 46 | SQL, database required |
| UpdateConversation | 51 | input required |
| DeleteConversation | 52 | input required |
| QueryConversationList | 53 | input required |
| QueryConversationHistory | 54 | input required |
| CreateMessage | 55 | input required |
| UpdateMessage | 56 | input required |
| DeleteMessage | 57 | input required |
| JsonStringify | 58 | input required |
| JsonParser | 59 | input required |

**Implementation Status**: ❌ Not implemented

---

### Trigger Nodes (type 34/35/36)

**Files**: 
- `node-registries/trigger-upsert/form-meta.tsx`
- `node-registries/trigger-delete/form-meta.tsx`
- `node-registries/trigger-read/form-meta.tsx`

| Rule | Path | Description | Static? |
|------|------|-------------|---------|
| User ID Required | `inputs.inputParameters.userId` / `inputs.fixedInputs.userId` | User ID required | ✅ |

**Implementation Status**: ❌ Not implemented

---

### Break/Continue (type 19/29)

**Files**: 
- `node-registries/break/form-meta.tsx`
- `node-registries/continue/form-meta.tsx`

| Rule | Description | Static? |
|------|-------------|---------|
| nodeMeta only | No specific validation | ✅ |

**Implementation Status**: ✅ Implicit (no specific rules)

---

### End (type 2)

**File**: `node-registries/end/form-meta.tsx`

| Rule | Description | Static? |
|------|-------------|---------|
| nodeMeta only | No specific validation | ✅ |

**Implementation Status**: ✅ Implicit (no specific rules)

---

## Summary

### By Static Checkability

| Category | Count | Description |
|----------|-------|-------------|
| ✅ Fully Static | 15 | Can be checked without runtime |
| ⚠️ Partially Static | 24 | Requires some context but possible |
| ❌ Requires Runtime | 0 | All rules have some static component |

### Implementation Priority

| Priority | Node Types | Rules |
|----------|------------|-------|
| High | LLM, Question, Database, Code | Core validation rules |
| Medium | Variable Assign, HTTP, Intent, Image | Input/output validation |
| Low | Chat nodes, Trigger nodes | Specialized validation |

### Current Implementation Status

| Category | Implemented | Total | Coverage |
|----------|-------------|-------|----------|
| Common Rules | 3 | 3 | 100% |
| LLM Specific | 3 | 6 | 50% |
| Question Specific | 2 | 6 | 33% |
| Code Specific | 1 | 3 | 33% |
| Database Specific | 3 | 6 | 50% |
| HTTP Specific | 1 | 3 | 33% |
| Variable Assign Specific | 2 | 2 | 100% |
| Intent Specific | 1 | 2 | 50% |
| Image Generate Specific | 1 | 1 | 100% |
| LTM Specific | 1 | 1 | 100% |
| Dataset Specific | 1 | 1 | 100% |
| Other Node Specific | 0 | 30+ | 0% |

---

## Next Steps

1. **Implement Question node validation** (question required, options unique)
2. **Implement Database node validation** (SQL required, limit range)
3. **Implement Variable Assign validation** (left/right required)
4. **Implement Code node validation** (code required)
5. **Implement HTTP node validation** (URL required)

Each implementation requires:
- Extract node-specific params in AST builder
- Add validation logic in semantic pass
- Add test cases
