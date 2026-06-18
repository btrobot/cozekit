# Coze YAML Compiler V2 — 架构审查报告

> 审查日期: 2026-06-16
> 审查范围: `tools/coze_yaml_compiler_v2` 全部源码、测试、文档
> 审查目标: 评估 v2 是否实现了从"规则检查器"到"教科书级编译器架构"的扭转

---

## 总体判断

**V2 成功实现了从"规则检查器"到"教科书级编译器架构"的扭转。** 这不是 v1 的换皮——它是一个真正的编译器基础设施，拥有作用域树、符号表、类型系统、引用解析、查询协议等标准编译器组件。业务规则被正确地放置在 pass 层中，通过 IR 和 sema 基础设施来执行，而不是反过来由规则驱动架构。

---

## 一、架构总览

编译器流水线：

```
InputSource → TransportNormalizer → ParsedDocument
  → ASTBuilder → WorkflowAST          [语法层: 保语法]
  → IRBuilder  → WorkflowIR + Indices [IR层: 语义中间表示]
  → SymbolTable → ScopeTree → ReferenceResolver → QueryAuthority [语义分析]
  → SyntaxPass / SemanticPass / SemanticPass / PortabilityPass [验证pass]
  → CompilerV2Report                   [诊断报告]
```

| 教科书阶段 | V2 实现 | 评价 |
|---|---|---|
| 词法/传输层 | `TransportNormalizer` | ✅ 适配目标语言（YAML/JSON 有自己的 lexer，不需要自建） |
| 语法/AST | `ASTBuilder` → `WorkflowAST` | ✅ 保语法的 typed AST |
| IR/Lowering | `IRBuilder` → `WorkflowIR` + `WorkflowIndices` | ⚠️ 结构上与 AST 几乎同构（详见下文） |
| 语义分析 | `ScopeTree` + `SymbolTable` + `TypeSystem` + `ReferenceResolver` | ✅ 教科书级实现 |
| Pass 框架 | `PassProtocol` + `PassContext` + 4 passes | ✅ 真正的编译器 pass，非业务规则包装 |
| 诊断 | `Diagnostic` + `CompilerV2Report` | ✅ 结构化，有 rule_id/severity/checkability/horizon |

---

## 二、核心优势（V2 做对了什么）

### 1. 语义分析层是真正的编译器基础设施

| 组件 | 证据 |
|---|---|
| **作用域树** (`sema/scope_tree.py`) | 词法作用域、父子嵌套、祖先链可见性遍历——教科书实现 |
| **符号表** (`sema/symbol_table.py`) | "The symbol table is the single owner of 'what exists'"——单源真相原则 |
| **类型系统** (`sema/type_system.py`) | 类型规范化、类型推断、兼容性检查、RUNTIME_DEFERRED 处理 |
| **引用解析** (`sema/reference_resolution.py`) | 作用域感知的名字绑定，先同画布后全局 |
| **查询协议** (`sema/query_protocol.py`) | Pass 不能直接访问 IR——必须通过 SemaQueryAuthority 查询 |

> **这是扭转的核心证据：** v1 是"规则 → 检查函数"，v2 是"编译器基础设施 → pass 通过基础设施检查"。

### 2. Pass 是真正的编译器 Pass

4 个 pass 都操作 typed IR 字段，**无 `raw_data` 逃逸通道**——这是最重要的架构不变量：

| Pass | 验证 |
|---|---|
| `SyntaxPass` | 22 条规则，操作 IR 结构字段 |
| `SemanticPass` | 图分析（孤立节点、环检测、连通性）通过 sema 查询 |
| `SemanticPass` | 标题唯一性/长度、子画布端口 |
| `PortabilityPass` | 跨空间规则、作用域感知查询 |

### 3. 冻结 dataclass 贯穿全栈

`WorkflowAST`, `WorkflowIR`, `PassContext`, `InputSource`, `Diagnostic` 全部 `frozen=True`，防止 pass 意外修改 IR。

### 4. 测试架构纪律性强

- 87.9% 离线可检规则已覆盖
- 每个 pass 都有正/负样本对
- 7+ fixture 文件有 golden baseline
- `test_scope.py` 的 T1-T6 分层测试设计优秀
- 架构边界测试（A1-A6）强制执行层隔离

---

## 三、关键问题

### 🔴 高优先级

| # | 问题 | 位置 | 建议 |
|---|---|---|---|
| 1 | **AST 与 IR 结构同构** | `workflow_ast.py` vs `workflow_ir.py` | IR 应变成 graph-based（flat node table + adjacency list），而非树形 1:1 拷贝 |
| 2 | **SourceSpan 定义了但从未填充** | `diagnostics/core.py:17-22` | 诊断只能定位到文件级别，无法指向具体行/列。应利用 YAML mark 在 IR 构建时建立 span 映射 |
| 3 | **`lookup_node_by_id()` 声称 O(1) 实为 O(n)** | `symbol_table.py:123-133`, `query_authority.py:35-42` | 应维护 `node_id → NodeSymbol` 索引 |
| 4 | **Query Authority 打破封装** | `query_authority.py:229-264` | 直接访问 `_symtab._indices` 和 `_symtab._ir`，应改为 SymbolTable 的公开方法 |

### 🟡 中优先级

| # | 问题 | 位置 | 建议 |
|---|---|---|---|
| 5 | **frozen dataclass 被 `object.__setattr__` 篡改** | `workflow_ir.py:128-167`, `reference_resolution.py:108-125` | 有道理的权衡（保持 SymbolTable 引用有效），但需要 ADR 文档化 |
| 6 | **多分支条件被静默丢弃** | `ir/builder.py:158-167` | 只保留 `cond.branches[0]`，丢失 AND/OR 信息 |
| 7 | **跨 pass 规则重复** | `SyntaxPass` STRUCT-002/003 vs `SemanticPass` SEMANTIC-BE-012/023 | 边端点检查、全局变量类型检查重复 |
| 8 | **IR 残留语法诊断字段** | `NodeIR.has_data`, `has_blocks_key`, `_has_shape_issue` | 这些属于 AST 或诊断层，不属于语义 IR |
| 9 | **两种竞争的跨引用机制** | `link_canvas_references` (指针) vs `WorkflowIndices` (索引) | 应统一为一种 |
| 10 | **`ParameterSymbol` 引用在 `resolve_all_refs` 后变为过期** | `reference_resolution.py:149-165` | 新创建的 `ParameterIR` 不是 SymbolTable 持有的旧对象 |
| 11 | **边索引不区分画布** | `indices.py:49-53` | `edges_by_source` 按 node_id 而非 (canvas, node_id) 索引 |
| 12 | **CLI 不传播 exit_code** | `compiler_v2_api.py:68-80` | CI 无法通过 shell exit code 检测违规 |

### 🟢 低优先级

| # | 问题 | 建议 |
|---|---|---|
| 13 | `PortIR` 死代码 | 删除或实现 |
| 14 | `_diag` 辅助函数在每个 pass 中重复 | 提取到共享模块 |
| 15 | `STANDARD_NODE_TYPE_TABLE` 硬编码在 SyntaxPass 中 | 移到共享常量模块 |
| 16 | `api/__init__.py` 是空壳 | 删除或填充 re-exports |
| 17 | 复合类型映射 `'8':'if', '21':'loop', '28':'batch'` 散布多处 | 统一为 enum/常量 |
| 18 | mapping table 中 SYNTAX-016/017/020 标记为 ❌ 但实际已有测试 | 更新文档 |

---

## 四、AST vs IR 的核心矛盾

这是 v2 最需要思考的架构决策：

**现状：** AST 和 IR 是结构同构的树，IR 只是 AST 的字段重命名版本 + 少量语义标记。

**两个方向：**

| 方案 | 做法 | 代价 |
|---|---|---|
| **合并 AST+IR** | 用一个渐进式丰富的表示 | 失去语法/语义的清晰边界 |
| **IR 变为图结构** | flat node table + adjacency list，pass 用 O(1) 查找 | 需要重写 pass 的遍历逻辑 |

**建议：** 短期做 pruning（删除语法字段、死代码、统一跨引用机制），中期如果编译器继续成长，将 IR 改造为 graph-based 结构。

---

## 五、各层详细审查

### 5.1 Pipeline & API

**Pipeline** (`pipeline.py`): 单 pass 架构，SymbolTable 构建一次，引用解析一次，所有 pass 通过 WorkflowSemaQueryAuthority 查询。流水线顺序正确：Transport → AST → IR → link_canvas_references → SymbolTable → resolve_all_refs → PassRegistry.run_all → Report。

**API** (`compiler_v2_api.py`): 暴露 `compile_text()`, `compile_path()`, `compile_source()` + CLI `main()`。

**问题：**
- CLI 不传播 `exit_code` 到 shell（CI 无法检测违规）
- 全局可变单例（非线程安全，CLI 工具可接受）
- PassRegistry 无优先级/依赖声明
- `api/__init__.py` 是空命名空间

### 5.2 AST 层

**AST 类型** (`ast/workflow_ast.py`): 正确建模了节点、边、参数引用、条件分支、复合嵌套。SourceProvenance 线程化贯穿所有类型。

**AST Builder** (`ast/builder.py`): 从 raw dict 构建 typed AST，递归处理复合节点，支持 Coze full format 和 simple format 两种参数格式。

**问题：**
- 双格式参数解析应由 transport 层统一，不应耦合在 AST builder 中
- 复合类型映射 `'8':'if', '21':'loop', '28':'batch'` 应为共享常量
- AST 缺少：节点输出参数、节点配置（LLM 模型设置等）、工作流级元数据

### 5.3 IR 层

**IR 类型** (`ir/workflow_ir.py`): 与 AST 结构同构，添加了 `is_global_var_def`、`canvas_ref`/`parent_canvas`/`owner_node` 双向图链接、`resolved_ref` 插槽、版本/信封元数据。

**IR Builder** (`ir/builder.py`): 单 pass 机械字段拷贝 + 重命名。明确不解析引用（那是 sema 的职责）。

**IR Indices** (`ir/indices.py`): 提供 `nodes_by_id`, `edges_by_source/target`, `canvas_by_path` 等 O(1) 查找表。

**关键问题：**
- AST 与 IR 结构同构——IR 只是 AST 的字段重命名版本
- `PortIR` 死代码（从未构造）
- `link_canvas_references` 和 `WorkflowIndices` 两种跨引用机制竞争
- 多分支条件 `cond.branches[0]` 静默丢弃
- `NodeIR` 残留 `has_data`, `has_blocks_key`, `_has_shape_issue` 等语法诊断字段
- 边索引不区分画布

### 5.4 语义分析层 (Sema)

**作用域模型** (`sema/scope.py`): 教科书词法作用域，`ScopeKind` 分类（root/loop/batch/if/block），`frozen=True`。

**作用域树** (`sema/scope_tree.py`): 两遍 O(n) 构建，`visible_symbols()` 正确遍历祖先链并去重，`is_visible()` 是 O(depth) 可见性检查。

**符号表** (`sema/symbol_table.py`): 单源真相原则，三种符号类型（Node/Canvas/Parameter），O(1) 按路径查找，scope-aware 查询委托给 ScopeTree。

**类型系统** (`sema/type_system.py`): 类型规范化（str→string, int→integer）、类型推断、精确匹配兼容性检查、RUNTIME_DEFERRED 处理。

**引用解析** (`sema/reference_resolution.py`): 作用域感知的名字绑定，先同画布后全局，就地修改 frozen IR（通过 `object.__setattr__`）。

**查询协议** (`sema/query_protocol.py`): 定义 pass→sema 查询契约，等价于 clang::Sema 的公开 API。

**查询权威** (`sema/query_authority.py`): 具体实现，280 行，混合了符号查找、类型查询、图分析、边查询、画布遍历、工作流元数据。

**关键问题：**
- `lookup_node_by_id()` 声称 O(1) 实为 O(n)
- Query Authority 直接访问 `_symtab._indices` 和 `_symtab._ir`，打破封装
- `ParameterSymbol` 引用在 `resolve_all_refs` 后过期
- `CanvasView` 泄漏 `NodeIR`/`EdgeIR` 到协议边界
- `resolve_full_ref()` 未在 Protocol 中声明
- magic string 节点类型 ID (`'8'`, `'21'`, `'28'`) 未集中管理

### 5.5 Pass 层

**协议** (`passes/protocol.py`): 干净的 Protocol 契约——`run(ctx: PassContext) -> Tuple[Diagnostic, ...]`。

**注册表** (`passes/registry.py`): 简单 list-based，按注册顺序执行。

**上下文** (`passes/context.py`): 冻结 dataclass，提供 typed 访问到 IR、indices、sema、AST、source_text 等。

**4 个 Pass 全部是真正的编译器 Pass：**
- `SyntaxPass`: 22 条编号规则
- `SemanticPass`: 图分析，通过 sema 查询
- `SemanticPass`: 前端语义验证
- `PortabilityPass`: 跨空间规则，作用域感知

**关键问题：**
- 边端点检查跨 pass 重复（SyntaxPass STRUCT-002/003 vs SemanticPass SEMANTIC-BE-012/023）
- 全局变量类型检查重复（SYNTAX-020 vs SEMANTIC-BE-020）
- `_diag` 辅助函数每个 pass 重复
- `STANDARD_NODE_TYPE_TABLE` 硬编码在 SyntaxPass 中
- `SemanticPass._check_cycles` 只检查根画布，不检查嵌套画布
- `PortabilityPass` 重新解析 `source_text` 而非使用已解析的 `ParsedDocument`

### 5.6 诊断层

**核心类型** (`diagnostics/core.py`): 结构良好——`DiagnosticKind`（6 级严重度）、`Checkability`（5 级可检性）、`RuleHorizon`（4 阶段: COMPILE_TIME/LINK_TIME/RUN_PREFLIGHT/TRUE_RUNTIME）、`SourceSpan`、`CanvasPath`、`Diagnostic`。

**报告** (`diagnostics/report.py`): 干净的组装层——`CompilerV2Report` 聚合所有 pass 的诊断。

**关键问题：**
- `SourceSpan` 定义了但从未被任何 pass 填充——所有诊断只能定位到文件级别
- `CanvasPath` 定义了但从未被任何 pass 填充
- 无去重——同一规则可对同一节点多次触发

### 5.7 Transport 层

**InputSource** (`transport/input_source.py`): 冻结 dataclass，持有原始输入。

**ParsedDocument** (`transport/input_source.py`): 冻结 dataclass，标准化输出——raw parsed dict、源元数据、传输格式、版本、信封类型。

**TransportNormalizer** (`transport/normalizer.py`): 编排——resolve text → detect format → parse (YAML/JSON) → unwrap envelopes。

**评价：** 不是真正的 lexer/parser（没有 tokenization、没有语法），但这对目标语言（YAML/JSON）是合适的。正确地统一了输入格式、解包平台特定信封、保留源文本。

**问题：**
- 格式检测启发式可能误判
- 无畸形 YAML/JSON 错误处理
- `ParsedDocument.raw_document` 类型为 `Any`

---

## 六、测试审查

### 测试覆盖统计

| 维度 | 评级 | 说明 |
|---|---|---|
| 架构边界强制 | Strong | 源码文本边界测试捕获层违规 |
| 阶段覆盖 | Excellent | 5 个阶段都有专用测试文件 |
| 规则覆盖 | 87.9% 离线 | 51/58 离线可检规则已实现+测试 |
| 正/负样本对 | Excellent | 每个 batch 测试都用 clean→no rule / bad→fires rule 模式 |
| Oracle 基线 | Strong | 7+ fixture 文件有 golden counts 和 rule_ids |
| 测试隔离 | Good | `build_pipeline` 和 `build_sema` fixture 干净可复用 |
| Mapping table 准确性 | Stale | 3 规则 (SYNTAX-016/017/020) 标记 ❌ 但实际已测试 |

### 测试覆盖缺口（按优先级）

| 缺口 | 优先级 | 工作量 | 影响 |
|-----|--------|-------|------|
| SYNTAX-012 (branch edge sourcePortID) 无专用测试 | P1 | 低 | 结构规则仅有隐式覆盖 |
| SYNTAX-018 (variable schema nesting) 需 IR 扩展 | P2 | 中 | 需要新 IR 字段 + 测试 |
| BE-006 (canvas schema shape) 无专用测试 | P1 | 低 | 仅有 clean corpus 覆盖，无负测试 |
| BE-016 (composite nesting) 无专用负测试 | P1 | 低 | 仅有隐式覆盖 |
| 复杂类型兼容性 (object↔object, list↔list) | P2 | 低 | 类型系统仅测试标量类型 |
| 多画布 AST 字段验证（不仅检查计数） | P2 | 中 | IR 测试仅检查计数，不检查字段值 |
| Pass 排序和异常处理 | P3 | 中 | 无 pass 失败模式测试 |
| Mapping table 过期 (3 规则) | P1 | 极低 | 仅文档 |

---

## 七、总结

| 维度 | 评级 | 说明 |
|---|---|---|
| **教科书架构目标** | ✅ 达成 | 作用域/符号表/类型系统/引用解析/pass 框架全部是真正的编译器基础设施 |
| **v1 规则迁移到 v2** | ✅ 87.9% 离线覆盖 | mapping table 清晰，51/58 离线可检规则已实现+测试 |
| **AST/IR 分离** | ⚠️ 形式上分离，实质同构 | 需要让 IR 变得"真的不同"或合并 |
| **语义分析** | ✅ 教科书级 | 词法作用域、符号表、类型系统、引用解析、查询协议——完整 |
| **Pass 质量** | ✅ 真正的编译器 pass | 通过 typed IR + sema 查询，无 raw_data 逃逸 |
| **诊断质量** | ⚠️ 结构好但缺源码定位 | SourceSpan/CanvasPath 定义了但从未填充 |
| **测试** | ✅ 纪律性强 | 架构边界测试 + 阶段测试 + 正负样本对 + golden baseline |

**结论：V2 成功扭转了编译器的架构方向。** 从 v1 的"规则驱动检查器"变成了 v2 的"以编译器基础设施为中心、pass 通过基础设施执行验证"的教科书架构。当前的主要改进空间在于：让 IR 真正成为与 AST 不同的表示（而非 1:1 拷贝），以及接通 SourceSpan 使诊断能指向具体行号。

---

## 附录：建议行动路线

### 短期（Pruning，低迁移成本）

1. **更新 mapping table** — SYNTAX-016/017/020 标记为 ✅
2. **CLI 传播 exit_code** — `sys.exit(report.exit_code)`
3. **添加 `node_id → NodeSymbol` O(1) 索引** — 消除热路径 O(n) 查找
4. **Query Authority 封装修复** — 将 `_symtab._indices` 访问改为 SymbolTable 公开方法
5. **删除 `PortIR` 死代码**
6. **提取 `_diag` 到共享模块**
7. **提取 `STANDARD_NODE_TYPE_TABLE` 到共享常量模块**
8. **统一复合类型映射为 enum**
9. **Wire up SourceSpan** — 利用 YAML mark 在 IR 构建时建立 span 映射
10. **添加 BE-016、SYNTAX-012 专用负测试**
11. **为 frozen+`__setattr__` 模式写 ADR**

### 中期（IR 重构，如编译器继续成长）

1. **IR 变为 graph-based** — flat node table + adjacency list
2. **清理 IR 语法诊断字段** — `has_data`, `has_blocks_key`, `_has_shape_issue` 移到 AST/诊断层
3. **统一跨引用机制** — 选择指针或索引，删除另一种
4. **多分支条件完整保留**
5. **Transport 层统一参数格式** — AST builder 不应处理双格式
6. **PortabilityPass 不应重新解析 source_text**
7. **复杂类型兼容性测试**（object↔object, list↔list）
