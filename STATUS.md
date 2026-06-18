# cozekit — Coze Workflow Static Validator

## 产品定位

**静态验证器**，用于校验 Coze 工作流 YAML/JSON 文件的语法和语义正确性。

采用教科书级编译器架构：Transport → AST → Semantic Model → Passes → Diagnostics。

**目标**：编写 Coze 工作流脚本后，用 cozekit 检查通过，可直接加载到 Coze 平台，无语法/语义错误。

## 架构

```
Transport → AST → AnalysisGraph → Sema → Passes → Diagnostics
   │         │         │            │        │          │
 YAML/JSON  frozen   flat graph   symbol   FE/BE/    rule_id
  解析     dataclass  构建       table    SYNTAX    + severity
            AST      + indices   + scope   + PORT
                               + refs    检查
```

### 核心模块

| 模块 | 职责 | 文件 |
|------|------|------|
| `transport/` | YAML/JSON 解析、格式转换、错误恢复 | `normalizer.py`, `yaml_source_converter.py` |
| `ast/` | 冻结 dataclass AST、Builder、Visitor | `workflow_ast.py`, `builder.py`, `visitor.py` |
| `sema/` | 符号表、作用域树、引用解析、类型系统 | `symbol_table.py`, `scope_tree.py`, `type_system.py` |
| `passes/` | 语法/语义/可移植性检查 Pass | `syntax_pass.py`, `frontend_pass.py`, `backend_pass.py` |
| `diagnostics/` | 诊断输出、报告 | `core.py`, `report.py` |
| `types.py` | 节点类型枚举（51 种）、分组常量 | 叶子模块，无外部依赖 |

### Pass 架构

| Pass | 规则前缀 | 职责 |
|------|----------|------|
| `SyntaxPass` | SYNTAX-* | 22 条语法规则 |
| `FrontendPass` | SEMANTIC-FE-* | 14 条前端语义规则 |
| `BackendPass` | SEMANTIC-BE-* | 23 条后端语义规则 |
| `PortabilityPass` | PORTABILITY-* | 14 条可移植性规则 |
| `SemanticPass` | (facade) | 向后兼容，委托 FrontendPass + BackendPass |

## 测试覆盖

**889 测试，0 失败**（2026-06-18）

| 分类 | 测试数 | 覆盖范围 |
|------|--------|----------|
| SYNTAX | 71 | 22 条语法规则 |
| SEMANTIC-BE | 85 | 23 条后端语义规则 |
| SEMANTIC-FE | 327 | 14 条前端语义规则（含 20+ 节点类型） |
| PORTABILITY | 18 | 14 条可移植性规则 |
| CONDITION | 41 | 条件表达式验证 |
| OUTPUT | 29 | 输出变量验证 |
| COMMON | 18 | 通用验证器 |
| Oracle | 58 | 33 YAML fixture + 25 JSON fixture 回归 |
| AST | 16 | Visitor 模式遍历 |
| Passes | 14 | Pass 拆分 diff 测试 |
| Transport | 47 | YAML/JSON 解析、格式转换 |
| Infra | 165 | 基础设施（sema、scope、analysis graph） |

### 硬检查

- **33 YAML fixture oracle diff**：每个 YAML fixture 的诊断 rule_id 列表与 baseline 完全一致
- **10 YAML fixture pass-split diff**：FrontendPass + BackendPass 输出与 SemanticPass facade 完全一致
- **边界注入**：Unicode 标题、最大长度 63/64、环检测（自环/2 环/钻石）、isolated 节点豁免
- **错误恢复**：malformed JSON/YAML 不抛异常，返回 Diagnostic

## 代码规模

- **源码**：54 个 Python 文件，6603 行
- **测试**：96 个测试文件
- **CLI**：`python -m cozekit check <file>` 验证工作流文件

## 演进历史

| 阶段 | 目标 | 测试数 |
|------|------|--------|
| P0 | 教科书编译器基础修复（依赖方向、类型系统、错误恢复） | 797 |
| P2 | ASTVisitor、SemanticPass 拆分、类型流分析、错误恢复增强 | 832 |
| P3 | 边界用例注入、缺失规则测试、YAML oracle 全量回归 | 889 |

## 验证策略分层

| 层级 | 状态 | 说明 |
|------|------|------|
| Layer 1: 语法检查 | ✅ 完整 | 22 条 SYNTAX 规则 |
| Layer 2: 静态语义检查 | ✅ 完整 | FE-001~014, BE-001~023 |
| Layer 3: 类型流分析 | ✅ 基本 | 单参数类型比较，全局变量跳过 |
| Layer 4: 可移植性检查 | ✅ 完整 | 14 条 PORTABILITY 规则 |
| Layer 5: 运行时检查 | ❌ 不可做 | 需要 Coze 运行时 |

## 使用

```bash
# 安装
cd tools/cozekit && pip install -e .

# 验证工作流文件
python -m cozekit check workflow.yaml

# 运行测试
python -m pytest tests/ -q
```
