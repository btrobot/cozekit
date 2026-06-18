# 验证能力分层实现状态

## 当前状态

**总测试数**: 423 passed

## Layer 1: 语法验证 (Syntax) — ✅ 完成

| 规则 ID | 描述 | 状态 |
|---------|------|------|
| SYNTAX-001 | YAML/JSON 结构合法性 | ✅ |
| SYNTAX-003 | 必填字段存在性 | ✅ |
| SYNTAX-011 | 边的 source/target 存在性 | ✅ |
| SYNTAX-012 | 分支端口 sourcePortID | ✅ |
| SYNTAX-021 | 节点类型是否已知 | ✅ |
| SYNTAX-022 | 节点类型格式 | ✅ |

## Layer 2: 静态语义验证 (Static Sema) — ✅ 完成

| 规则 ID | 描述 | 状态 |
|---------|------|------|
| FE-001 | 节点特定字段验证 (25 种节点) | ✅ |
| FE-009 | 参数名格式 | ✅ |
| FE-010 | 节点标题长度 | ✅ |
| FE-011 | 节点标题格式 | ✅ |
| FE-013 | 输出变量名格式/保留字 | ✅ |
| FE-014 | 输出变量类型 | ✅ |

## Layer 3: 图结构验证 (Graph) — ✅ 完成

| 规则 ID | 描述 | coze-studio 对应 | 状态 |
|---------|------|------------------|------|
| BE-001 | Start 节点必须有出边 | ValidateConnections | ✅ |
| BE-002 | 非 End 节点必须有出边 | ValidateConnections | ✅ |
| BE-010 | 分支端口必须连接 | ValidateConnections | ✅ |
| BE-015 | 禁止环路 | DetectCycles | ✅ |
| BE-016 | 禁止嵌套 Loop/Batch | ValidateNestedFlows | ✅ (已修正) |

## Layer 4: 链接验证 (Link) — ⚠️ 部分完成

| 规则 ID | 描述 | 需要什么 | 状态 |
|---------|------|---------|------|
| BE-017 | 引用的 blockID 是否存在 | 无 (已实现) | ✅ |
| BE-018 | 引用的变量名是否存在 | 无 (已实现) | ✅ |
| BE-020 | 全局变量类型匹配 | API 调用 | ⚠️ 部分 |
| BE-022 | 子工作流终止计划 | 子工作流定义 | ❌ REQUIRES_LIVE |
| FE-001 | Plugin 输入 required | API 定义 | ❌ 无法静态 |
| FE-001 | SubWorkflow 输入 required | 子工作流定义 | ❌ 无法静态 |

## Layer 5: 运行时验证 (Runtime) — ❌ 不可做

| 描述 | 原因 |
|------|------|
| 变量实际值验证 | 需要执行环境 |
| API 调用结果验证 | 需要外部服务 |
| 循环边界检查 | 需要实际数据 |
| 表达式求值 | 需要值信息 |

## 本次更新

1. **创建验证分层标准文档**: `docs/validation-layers.md`
2. **修正 BE-016**: 从 `REQUIRES_LIVE_VALIDATION` 改为 `OFFLINE` (静态图检查)
3. **更新消息**: "nested composite nodes require live Coze validation" → "composite nodes such as batch/loop cannot be nested"

## 与 coze-studio 的对比

| 检查类别 | coze-studio | 我们的实现 | 差异 |
|---------|-------------|-----------|------|
| 前端表单验证 | ✅ 40+ form-meta | ✅ FE-001 (25 种节点) | 覆盖率相当 |
| 图结构验证 | ✅ 后端 API | ✅ BE-001/002/010/015/016 | 完全对齐 |
| 链接验证 | ✅ 后端 API | ⚠️ BE-017/018 | 部分对齐 |
| 运行时验证 | ✅ 运行时 | ❌ 不可做 | 设计差异 |

## 设计原则

我们的验证器 = 传统编译器的前端 (Lexer + Parser + Sema)

```
传统编译器:
  前端 (静态分析) → 后端 (优化 + 代码生成)

我们的验证器:
  Transport → AST → Sema → Passes → Report
  (纯静态分析，不生成代码)
```

**核心原则**: 只做不需要外部信息的静态检查，有外部定义时可以扩展 Layer 4。
