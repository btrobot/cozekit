# coze_yaml_compiler_v2 — 架构审查报告

**审查日期**: 2026-06-17
**审查范围**: `tools/coze_yaml_compiler_v2/coze_yaml_compiler_v2/` 全部源码 + 测试
**审查标准**: 用户目标——"按照传统编译器的架构来实现编译器，明确词法、语法、AST、语义、作用域、值系统、类型系统、IR 等概念，实现教科书级别的编译器"
**测试状态**: 266/266 通过，0.92s

---

## 一、总体评价

v2 成功地从 v1 的"规则检查器"模式扭转到了分层编译器架构。管道清晰：

```
Transport → AST → IR (flat lowering) → Sema (SymbolTable + ScopeTree) → Resolve Refs → Passes → Report
```

相比 v1 的路径依赖（规则直接扫描 raw dict），v2 有质的提升。但距离"教科书级别编译器"仍有显著差距。

**完成度评分: 7.5/10** — 骨架正确，核心 lowering 已完成，剩余为演进空间。

---

## 二、各层逐项审查

### 2.1 Transport 层 ✅ 优良

| 文件 | 行数 | 评价 |
|------|------|------|
| `transport/input_source.py` | ~50 | 纯值类型，干净 |
| `transport/normalizer.py` | ~95 | YAML/JSON/.flow 统一入口 |
| `transport/span_map.py` | ~90 | `yaml.compose()` 提取行号 |

**优点**:
- `SpanMap` 设计精巧，通过 `yaml.compose()` 的 mark 信息实现零开销行号追踪
- `.flow` 和 export/clipboard 信封解包逻辑正确处理了 span prefix 剥离
- 三种格式（YAML/JSON/.flow）统一归一化

**无重大问题。**

### 2.2 AST 层 ✅ 良好

| 文件 | 行数 | 评价 |
|------|------|------|
| `ast/workflow_ast.py` | ~110 | 纯语法保持，frozen dataclass |
| `ast/builder.py` | ~440 | 从 raw dict 提取到类型化 AST |

**优点**:
- AST 纯语法保持，不含语义标记
- `SourceProvenance` + `SourceSpan` 双重来源追踪
- 复合节点（If/Loop/Batch）正确递归提取子画布

**问题**:
- ⚠️ `NodeAST.blocks` 用 `tuple[NodeAST, ...]` 表示嵌套——这实际上是 AST 自身的嵌套结构，但在 IR lowering 时被展平。AST 保留嵌套是正确的，但 `nested_edges` 的存在让 AST 节点承担了"子画布容器"的语义，不够纯粹。

### 2.3 IR 层 ⚠️ 名实不符

| 文件 | 行数 | 评价 |
|------|------|------|
| `ir/workflow_ir.py` | ~130 | 数据定义 |
| `ir/builder.py` | ~200 | AST→IR lowering |
| `ir/indices.py` | ~100 | O(1) 查询索引 |

**核心问题: IR 与 AST 结构几乎同构**

对比两个节点：

```python
# NodeAST
class NodeAST:
    node_id, node_type, title, parameters, variable_parameters,
    branches, blocks, nested_edges, has_blocks_key, composite_kind,
    _has_shape_issue, has_data, is_valid_object, global_var_name,
    global_var_type, canvas_path, non_object_node_count, provenance, source_span

# NodeIR
class NodeIR:
    node_id, node_type, title, canvas_path, provenance, composite_kind,
    input_parameters, variable_parameters, branches, is_global_var_def,
    global_var_name, global_var_type, source_span, has_data, has_blocks_key,
    _has_shape_issue, is_valid_object, non_object_node_count
```

**差异仅有**:
1. AST 的 `parameters` → IR 的 `input_parameters`（改名）
2. AST 的 `blocks`/`nested_edges` → IR 中消除（展平到独立节点）
3. IR 增加 `is_global_var_def`（从 `node_type == "11"` 推导）
4. IR 的 `ref` 是 `RefIR`，AST 的是 `RefAST`（字段完全相同）

**在教科书编译器中，IR 应该是与 AST 完全不同的表示**。例如：
- AST: `IfStmt(condition, then_block, else_block)`
- IR: `BasicBlock[label=0]: Branch(cond, L1, L2); BasicBlock[label=1]: ...`

当前 v2 的 IR 本质上是"展平后的 AST"，不是真正的中间表示。

**具体问题**:

1. **`has_data`, `has_blocks_key`, `_has_shape_issue`, `is_valid_object`, `non_object_node_count` 出现在 IR 中** — 这些是语法层的结构检查元数据，不应传递到 IR。IR 应该只包含语义有意义的信息。这些字段的存在说明 IR 仍然在为 pass 承担语法检查的职责。

2. **`resolved_ref` 通过 `object.__setattr__` 原地修改 frozen dataclass** — 这是一个反模式。frozen dataclass 的契约是不可变，用 `__setattr__` 绕过会：
   - 破坏 hash 一致性（如果对象已被 hash）
   - 让并发访问不安全
   - 让代码推理变得困难

   **建议**: `resolve_all_refs` 应该构建新的 IR 对象（不可变更新），而不是原地修改。

3. **`ParameterIR.resolved_ref: object | None`** — 类型是 `object`，实际存储 `ResolvedRef`。这破坏了类型安全。

4. **`WorkflowIndices.nodes_by_canvas` 用 `str(canvas_path)` 做 key** — `str(tuple)` 作为 dict key 是脆弱的（依赖 `repr` 格式）。应该用 `tuple` 本身作 key。

### 2.4 Sema 层 ⚠️ 架构合理但有封装问题

| 文件 | 行数 | 评价 |
|------|------|------|
| `sema/symbol_table.py` | ~170 | 符号注册 + 查询 |
| `sema/scope_tree.py` | ~130 | 层次作用域树 |
| `sema/scope.py` | ~30 | Scope 值类型 |
| `sema/reference_resolution.py` | ~140 | 引用解析 |
| `sema/query_authority.py` | ~300 | Pass 面向接口 |
| `sema/query_protocol.py` | ~90 | Protocol 定义 |
| `sema/type_system.py` | ~160 | 类型规范 + 兼容性 |

**优点**:
- `ScopeTree` 设计正确：层次结构 + 可见性链 + 祖先遍历
- `WorkflowSemaQueryAuthority` 作为 pass 的唯一查询表面，封装了符号表
- 引用解析支持作用域感知（`from_canvas_path`）

**问题**:

1. **`WorkflowSemaQueryAuthority` 不实现 `SemaQueryAuthority` Protocol**:
   ```python
   # query_protocol.py
   class SemaQueryAuthority(Protocol):
       def lookup_symbol(self, name: str) -> SymbolInfo | None: ...
       def type_of(self, path: tuple) -> TypeInfo | None: ...
       def resolve_ref(self, ref_source: str, ref_name: str) -> SymbolInfo | None: ...
       def scope_of(self, canvas_path: tuple) -> ScopeInfo | None: ...
       def visible_symbols_from(self, canvas_path: tuple) -> tuple[SymbolInfo, ...]: ...
       def is_visible(self, from_path: tuple, target_node_id: str) -> bool: ...

   # query_authority.py
   class WorkflowSemaQueryAuthority:  # 无 (Protocol) 基类
   ```
   Protocol 定义了接口，但实现类没有显式声明实现它。Python 的 structural subtyping 会隐式匹配，但这不是一个教科书编译器应有的做法。

2. **`SymbolTable` 暴露过多内部方法给 `WorkflowSemaQueryAuthority`**:
   - `edge_source_targets`, `edge_target_sources`, `all_node_ids`, `node_edges`, `has_outgoing_edges`, `has_incoming_edges`, `nodes_by_canvas_for_canvas`, `edges_by_canvas_for_canvas`
   - 这些方法让 `SymbolTable` 变成了一个"万能查询对象"，而不是纯粹的符号表
   - **教科书中**: SymbolTable 管理名字→符号的映射；图查询应该在 Indices 或专门的 GraphQuery 层

3. **`reference_resolution.resolve_all_refs` 原地修改 IR**:
   ```python
   object.__setattr__(node, 'input_parameters', new_input)
   ```
   这让 SymbolTable 持有的 NodeIR 引用自动获得 resolved_ref——巧妙但危险。如果未来任何步骤在 resolve 之前读取了 IR，会得到不一致状态。

4. **`type_system.py` 缺少教科书类型系统的核心概念**:
   - 无类型环境（Type Environment）
   - 无类型推断（Inference）— 只有从声明提取
   - 无类型约束传播
   - 6 种类型，精确匹配，无强制转换
   - 对 Coze 工作流来说可能够用，但不构成"类型系统"

### 2.5 Pass 层 ⚠️ 本质仍是规则检查器

| 文件 | 行数 | 评价 |
|------|------|------|
| `passes/syntax/syntax_pass.py` | 273 | SYNTAX-001~022 |
| `passes/semantic_be/semantic_be_pass.py` | 391 | BE-006~023 |
| `passes/semantic_fe/semantic_fe_pass.py` | 177 | FE-* |
| `passes/portability/portability_pass.py` | 180 | PORTABILITY-* |
| `passes/constants.py` | ~55 | 集中常量 |
| `passes/diag_helper.py` | ~35 | 共享诊断构造 |
| `passes/context.py` | ~40 | PassContext |
| `passes/registry.py` | ~30 | Pass 注册 |
| `passes/protocol.py` | ~20 | Pass Protocol |

**核心问题: Pass 做的不是"语义分析"，而是"规则检查"**

以 `SemanticBEPass.run()` 为例：
```python
def run(self, ctx):
    self._check_isolated_nodes(ctx, diagnostics)
    self._check_parameter_names(ctx, diagnostics)
    self._check_canvas_shape(ctx, diagnostics)
    self._check_branch_ports(ctx, diagnostics)
    ...
    self._check_cycles(ctx, diagnostics)
    self._check_ref_block_ids(ctx, diagnostics)
    self._check_contract_consistency(ctx, diagnostics)
```

每个 `_check_xxx` 都是独立的规则扫描——遍历节点/边，检查条件，产生诊断。这是 v1 的模式，只是把 `raw_data` 换成了类型化 IR。

**在教科书编译器中**：
- Pass 应该是 **变换**（AST→IR, IR→优化 IR）或 **分析**（构建额外数据结构）
- 语义分析 pass 通常构建 **类型环境**、**使用-定义链**、**控制流图**
- 诊断是分析的副产品，不是 pass 的主要输出

**建议**: 将规则检查重构为两层：
1. **分析层**: 构建 CFG、类型环境、使用-定义链等
2. **检查层**: 在分析结果上做验证，产生诊断

**其他问题**:

1. **没有 CFG（控制流图）**: 循环检测是临时 DFS，不是基于 CFG 的标准算法

2. **`_diag()` 方法虽然提取到了 `diag_helper.py`，但 4 个 pass 仍各自有 `_diag` wrapper**:
   ```python
   def _diag(self, rule_id, kind_str, message, ...):
       return make_diag(rule_id, kind_str, message, 'semantic-be', ...)
   ```
   每个 pass 的 wrapper 只差一个 `layer` 字符串。可以直接在调用处传 layer。

3. **Pass 注册硬编码在 `compiler_v2_api.py`**:
   ```python
   pipeline.pass_registry.register(SyntaxPass())
   pipeline.pass_registry.register(SemanticBEPass())
   pipeline.pass_registry.register(SemanticFEPass())
   pipeline.pass_registry.register(PortabilityPass())
   ```
   无动态注册、无 pass 依赖声明、无 pass 排序。

### 2.6 诊断层 ✅ 良好

| 文件 | 行数 | 评价 |
|------|------|------|
| `diagnostics/core.py` | ~65 | Diagnostic/SourceSpan/Checkability |
| `diagnostics/report.py` | ~60 | CompilerV2Report |

- `SourceSpan` 贯穿 AST→IR→Diagnostic 全链路
- `Checkability` → `RuleHorizon` 映射清晰（compile-time / link-time / true-runtime）
- 报告结构合理

---

## 三、教科书概念对照表

| 教科书概念 | v2 实现 | 状态 |
|-----------|---------|------|
| **词法分析（Lexer）** | 无（依赖 `yaml.safe_load`） | ⚪ 对 YAML DSL 合理 |
| **语法分析（Parser）** | `transport/normalizer.py` + `yaml` 库 | ✅ 合理 |
| **AST** | `ast/workflow_ast.py` | ✅ 纯语法保持 |
| **AST Builder** | `ast/builder.py` | ✅ 从 raw dict 构建 |
| **IR** | `ir/workflow_ir.py` | ⚠️ 与 AST 几乎同构 |
| **IR Builder** | `ir/builder.py` | ⚠️ 只做了展平，未做语义 lowering |
| **符号表（Symbol Table）** | `sema/symbol_table.py` | ✅ O(1) 查找 |
| **作用域（Scope）** | `sema/scope_tree.py` | ✅ 层次结构 + 可见性 |
| **类型系统（Type System）** | `sema/type_system.py` | ⚠️ 只有类型规范，无推断/环境 |
| **值系统（Value System）** | 无 | ❌ 缺失 |
| **引用解析（Name Resolution）** | `sema/reference_resolution.py` | ✅ 作用域感知 |
| **语义分析 Pass** | `passes/semantic_*` | ⚠️ 实为规则检查器 |
| **控制流分析（CFG）** | 无 | ❌ 缺失 |
| **诊断（Diagnostics）** | `diagnostics/` | ✅ 带源码位置 |
| **中间表示索引** | `ir/indices.py` | ✅ O(1) 图查询 |
| **Pass 框架** | `passes/registry.py` + `protocol.py` | ⚠️ 硬编码，无依赖管理 |

---

## 四、关键问题优先级

### P0 — 阻塞性（影响正确性/可维护性）

1. **原地修改 frozen dataclass** (`reference_resolution.py` L122-140)
   - `object.__setattr__` 绕过 frozen 契约
   - 影响: hash 一致性、并发安全、代码推理
   - 修复: 构建新 IR 对象或使用非 frozen IR

2. **`nodes_by_canvas` 用 `str(tuple)` 做 key** (`indices.py`)
   - 不同 canvas_path 可能有相同 `str()` 表示
   - 修复: 直接用 `tuple` 作 key

### P1 — 架构债务（影响"教科书级"目标）

3. **IR 与 AST 同构** — 需要做真正的语义 lowering
4. **Pass 本质是规则检查器** — 需要重构为分析+检查两层
5. **无 CFG** — 控制流分析应基于标准 CFG
6. **类型系统只有规范** — 缺少类型环境和推断
7. **`ParameterIR.resolved_ref: object`** — 类型安全缺失

### P2 — 改进项

8. **Protocol 未显式实现**
9. **SymbolTable 暴露过多图查询方法**
10. **Pass 硬编码注册**
11. **诊断 wrapper 方法冗余**
12. **`SourceProvenance` 只有 line，没有 column**（而 `SourceSpan` 有完整的行列信息）

---

## 五、推荐的下一步行动

### 短期（v2.1 修正）

1. 修复 `object.__setattr__` 反模式——用不可变更新模式重建 IR
2. 修复 `str(tuple)` key 问题
3. 给 `ParameterIR.resolved_ref` 加正确类型注解
4. 将 `has_data`/`_has_shape_issue`/`is_valid_object` 从 IR 移到语法检查专用层

### 中期（v2.5 向教科书靠拢）

5. 引入 CFG 构建 pass（基于 flat IR 的 edges 构建 BasicBlock 图）
6. 引入 TypeEnvironment 数据结构（不只是 TypeFact 查询）
7. 将规则检查器重构为分析+检查两层
8. SymbolTable 瘦身：图查询方法移到 GraphQuery 或 Indices

### 长期（v3 教科书级）

9. IR 语义 lowering：NodeIR → 更底层的操作语义表示
10. Pass 框架支持 pass 依赖声明和拓扑排序
11. 值系统：常量折叠、字面量传播
12. 错误恢复：malformed 节点产生诊断后继续分析

---

## 六、结论

v2 成功建立了编译器的分层骨架，各层职责边界比 v1 清晰得多。SourceSpan 全链路追踪、O(1) 索引、作用域感知的引用解析都是扎实的工程成果。

但核心问题在于：**v2 本质上是一个"分层的规则检查器"，不是一个"教科书编译器"**。IR 是展平的 AST，Pass 是规则扫描，类型系统是类型规范表。要达到教科书级别，需要在 IR 语义深度、CFG 构建、类型环境、分析/检查分离四个方面做实质投入。

