# Coze 工作流验证器 — 验证能力分层标准

## 概述

本文档定义了 Coze 工作流静态验证器的验证能力分层标准，明确哪些检查可以静态完成，哪些需要外部定义或运行时环境。

## 验证能力分层

```
┌─────────────────────────────────────────────────────────────────┐
│                    验证能力分层                                   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: 语法 (Syntax)           → 纯静态，100% 可做           │
│  Layer 2: 静态语义 (Static Sema)  → 纯静态，大部分可做           │
│  Layer 3: 图结构 (Graph)          → 纯静态，可做                 │
│  Layer 4: 链接 (Link)             → 需要外部定义，部分可做        │
│  Layer 5: 运行时 (Runtime)        → 需要执行环境，不可做          │
└─────────────────────────────────────────────────────────────────┘
```

## 各层详细说明

### Layer 1: 语法验证 (Syntax)

**特征**: 只需要源文件，不需要任何外部信息

| 验证点 | 规则 ID | 示例 |
|--------|---------|------|
| YAML/JSON 结构合法性 | SYNTAX-001 | 格式错误 |
| 节点 ID 格式 | SYNTAX-001 | ID 为空或格式错误 |
| 节点类型是否已知 | SYNTAX-021 | type: "99" 不存在 |
| 边的 source/target 存在性 | SYNTAX-011 | 引用不存在的节点 ID |
| 必填字段存在性 | SYNTAX-003 | 缺少 nodeMeta.title |

**Checkability**: `OFFLINE`

> **注意**: LLM `prompt` 字段是否必填取决于运行时模型配置 (`model.is_up_required`)，
> 编译期无法确定。因此我们只检查 `prompt` 和 `systemPrompt` 至少一个非空。
> 详见 `docs/runtime-dependent-validations.md`。

---

### Layer 2: 静态语义验证 (Static Sema)

**特征**: 只需要 AST + 符号表，不需要外部定义

| 验证点 | 规则 ID | 示例 |
|--------|---------|------|
| 节点标题长度/格式 | FE-009/010/011 | title 超过 63 字符 |
| 参数名格式 (标识符) | FE-009 | name: "123abc" 不合法 |
| 值表达式格式 (type+content) | FE-001 | type: "invalid" 不在允许列表 |
| 节点特定字段验证 | FE-001 | LLM temperature 超出 [0,2] |
| prompt/systemPrompt 至少一个非空 | FE-001 | LLM 两个 prompt 都为空 → 错误 |
| 条件分支结构 (left/op/right) | FE-001 | If 节点缺少 operator |
| 输出变量名格式 | FE-013 | 输出名为保留字 |
| 保留字检查 | FE-013 | name: "true" 是保留字 |

**Checkability**: `OFFLINE`

---

### Layer 3: 图结构验证 (Graph)

**特征**: 只需要图的拓扑结构 (nodes + edges)，纯图算法

| 验证点 | 规则 ID | coze-studio 对应 | 示例 |
|--------|---------|------------------|------|
| Start 节点必须有出边 | BE-001 | ValidateConnections | Start → (无出边) |
| 分支端口必须连接 | BE-010 | ValidateConnections | If 只连了 true，false 没连 |
| 非 End 节点必须有出边 | BE-002 | ValidateConnections | LLM → (无出边) = 死节点 |
| 禁止嵌套 Loop/Batch | BE-016 | ValidateNestedFlows | Loop 内再放 Loop |
| 禁止环路 | BE-015 | DetectCycles | A→B→C→A |

**Checkability**: `OFFLINE`

**实现状态**:
- ✅ BE-001: 已实现
- ✅ BE-002: 已实现
- ✅ BE-010: 已实现
- ✅ BE-015: 已实现
- ✅ BE-016: 已实现 (需修正 checkability)

---

### Layer 4: 链接验证 (Link)

**特征**: 需要外部定义 (API 定义、子工作流定义、全局变量定义)

| 验证点 | 规则 ID | 需要什么外部信息 |
|--------|---------|-----------------|
| 全局变量类型匹配 | BE-020 | 需要调用 API 获取变量定义 |
| 子工作流终止计划类型 | BE-022 | 需要子工作流定义 |
| Plugin 输入是否 required | FE-001 | 需要 API 定义 |
| SubWorkflow 输入是否 required | FE-001 | 需要子工作流定义 |

**Checkability**: `PARTIAL` 或 `REQUIRES_LIVE_VALIDATION`

**说明**: 如果有外部定义文件，可以部分实现；否则标记为无法静态检查

---

### Layer 5: 运行时验证 (Runtime)

**特征**: 需要执行环境，无法静态检查

| 验证点 | 示例 |
|--------|------|
| 变量实际值 | temperature = "abc" 运行时才报错 |
| API 调用结果 | Plugin 返回格式错误 |
| 循环边界 | loopCount = -1 运行时才检查 |
| 表达式求值 | 变量实际值验证 |

**Checkability**: `REQUIRES_LIVE_VALIDATION`

---

## coze-studio 验证架构对比

```
coze-studio 前端:
  ├── feValidate (前端表单验证)
  │   ├── validateNode (每个节点的 form-meta.tsx)
  │   └── validateWorkflow (遍历所有节点)
  └── beValidate (后端 schema 验证)
      └── validateSchemaV2 → 调用后端 API

coze-studio 后端:
  └── ValidateTree
      ├── ValidateConnections    → Layer 3 (图结构)
      ├── DetectCycles           → Layer 3 (图结构)
      ├── ValidateNestedFlows    → Layer 3 (图结构)
      ├── CheckRefVariable       → Layer 4 (链接)
      ├── CheckGlobalVariables   → Layer 4 (链接，需 API)
      └── CheckSubWorkFlow...    → Layer 4 (链接，需定义)

我们的编译器:
  └── compile_text / compile_path
      ├── SyntaxPass             → Layer 1 (语法)
      ├── SemanticPass           → Layer 2 (语义) + Layer 3 (图结构)
      └── PortabilityPass        → Layer 4 (部分链接)
```

## 设计原则

1. **纯静态优先**: 只做不需要外部信息的检查
2. **明确标记**: 无法静态检查的规则标记为 `REQUIRES_LIVE_VALIDATION`
3. **渐进增强**: 有外部定义时可以扩展 Layer 4 检查
4. **测试驱动**: 每个规则都有对应的测试用例

## 与传统编译器的对应关系

```
传统编译器前端:
  Lexer → Parser → AST → Sema → IR

我们的验证器:
  Transport → AST → Sema → Passes → Report

对应关系:
  - Lexer/Parser  = Transport + AST Builder
  - Sema          = SymbolTable + ScopeTree
  - Passes        = SyntaxPass + SemanticPass + PortabilityPass
  - Report        = CompilerV2Report (diagnostics)

我们没有 IR 和后端，因为我们不生成代码，只做验证。
```
