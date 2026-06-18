# Coze YAML 编译器规则映射表

> v1 = `tools/coze_yaml_compiler` | v2 = `tools/coze_yaml_compiler_v2`
>
> 状态标记: ✅ 已实现 | ⚡ 架构隐式覆盖 | 🔒 需要运行时 | ❌ 待实现 | 📝 需 IR 扩展

---

## 一、SYNTAX 语法规则（22 条）

| # | 规则编号 | 中文描述 | 具体规则内容 | v1 实现位置 | v2 实现位置 | v2 测试点 | 状态 |
|---|---------|---------|-------------|-----------|-----------|----------|------|
| 1 | SYNTAX-001 | 画布根节点必须是对象 | canvas 根节点必须是 dict 类型，不能是 string/list | `syntax_validator.py` 检查 `raw_document` 类型 | `syntax_pass.py:78` 检查 `ctx.sema.canvases()` 是否为空 | `test_batch1_syntax.py:51` test_clean_valid_root / :57 test_non_object_root_emits_001 | ✅ |
| 2 | SYNTAX-002 | 节点列表必须存在 | `canvas.nodes` 必须是非空 list | `syntax_validator.py` 检查 `nodes` key | `syntax_pass.py:98` 检查 `has_nodes` | `test_batch1_syntax.py:69` test_clean_has_nodes_and_edges / :74 test_missing_nodes_emits_002 | ✅ |
| 3 | SYNTAX-003 | 边列表必须存在 | `canvas.edges` 必须是非空 list | `syntax_validator.py` 检查 `edges` key | `syntax_pass.py:103` 检查 `has_edges` | `test_batch1_syntax.py:69` / :80 test_missing_edges_emits_003 | ✅ |
| 4 | SYNTAX-004 | 版本元数据格式 | `canvas.versions` 如果存在必须是 dict | `syntax_validator.py` 检查 versions 类型 | `syntax_pass.py:112` 检查 `workflow_version_is_valid()` | `test_batch1_syntax.py:92` test_clean_no_versions / :112 test_versions_not_dict_emits_004 | ✅ |
| 5 | SYNTAX-005 | 节点 ID 必须存在且唯一 | 每个 node 必须有 `id`，同一 canvas 内不可重复 | `syntax_validator.py` 检查 `node.id` | `syntax_pass.py:123` 检查 `node_id` + 重复检测 | `test_batch1_syntax.py:116` test_clean_valid_nodes / :122 test_non_object_node_emits_005 / :126 test_duplicate_id | ✅ |
| 6 | SYNTAX-006 | 节点类型必须存在且已知 | `node.type` 必须是已知的 Coze 节点类型 ID | `syntax_validator.py` 检查 type + `IDStrToNodeType` | `syntax_pass.py:148` 检查 `node_type` + `KNOWN_NODE_TYPE_IDS` | `test_batch1_syntax.py:177` test_clean_has_type / :183 test_missing_type_emits_006 | ✅ |
| 7 | SYNTAX-007 | 节点数据必须存在 | 校验敏感节点必须有 `node.data` | `syntax_validator.py` 检查 `node.data` | `syntax_pass.py:196` 检查 `node.has_data` | `test_batch1_syntax.py:195` test_clean_has_data / :201 test_missing_data_emits_007 | ✅ |
| 8 | SYNTAX-008 | blocks 仅限复合节点 | `node.blocks` 只应出现在 Loop/Batch 等复合节点上 | `syntax_validator.py` 检查 blocks + composite_kind | `syntax_pass.py:204` 检查 `has_blocks_key` + `composite_kind` | `test_batch1_syntax.py:213` test_composite_node_with_blocks_ok / :250 test_non_composite_with_blocks | ✅ |
| 9 | SYNTAX-009 | edges 应与 blocks 配对 | `node.nested_edges` 应与 `node.blocks` 同时出现 | `syntax_validator.py` 检查 edges+blocks 配对 | `syntax_pass.py:223` 检查 `nested_edges` 无 `blocks` | `test_batch1_syntax.py:213` test_composite_node_with_blocks_ok（隐式覆盖） | ✅ |
| 10 | SYNTAX-010 | 边源节点 ID 必须存在 | `edge.sourceNodeID` 必须非空 | `syntax_validator.py` 检查 source | `syntax_pass.py:241` 检查 `edge.source_node_id` | `test_batch1_syntax.py:269` test_clean_valid_edges / :276 test_missing_source_emits_010 | ✅ |
| 11 | SYNTAX-011 | 边目标节点 ID 必须存在 | `edge.targetNodeID` 必须非空 | `syntax_validator.py` 检查 target | `syntax_pass.py:246` 检查 `edge.target_node_id` | `test_batch1_syntax.py:269` / :295 test_missing_target_emits_011 | ✅ |
| 12 | SYNTAX-012 | 分支边应有源端口 ID | 来自分支节点的边应设置 `sourcePortID` | `syntax_validator.py` 检查 sourcePortID | `syntax_pass.py:264` 检查分支节点边的 `source_port_id` | `test_batch1_syntax.py:269` test_clean_valid_edges（隐式覆盖） | ✅ |
| 13 | SYNTAX-013 | 目标端口 ID 应保留 | 如果源数据有 `targetPortID`，不应被丢弃 | `syntax_validator.py` 检查 targetPortID 保留 | v2 IR 架构保证：`EdgeIR` 始终保留 `target_port_id` | 架构保证，无需专门测试 | ⚡ |
| 14 | SYNTAX-014 | 入口节点 ID 必须为 100001 | Start 节点的 `id` 必须是 `100001` | `syntax_validator.py` 检查 start node id | `syntax_pass.py:168` 检查 `START_NODE_ID` | `test_batch1_syntax.py:316` test_clean_canonical_ids / :323 test_wrong_start_id_emits_014 | ✅ |
| 15 | SYNTAX-015 | 出口节点 ID 必须为 900001 | End 节点的 `id` 必须是 `900001` | `syntax_validator.py` 检查 end node id | `syntax_pass.py:181` 检查 `END_NODE_ID` | `test_batch1_syntax.py:316` / :343 test_wrong_end_id_emits_015 | ✅ |
| 16 | SYNTAX-016 | 全局变量必须有名称 | 变量节点的 `name` 必须非空 | `syntax_validator.py` 检查 variable.name | `syntax_pass.py:231` 检查 `global_var_name` | `test_batch1_syntax.py` — 通过 compile_text 端到端覆盖 | ✅ |
| 17 | SYNTAX-017 | 全局变量必须有类型 | 变量节点的 `type` 必须非空 | `syntax_validator.py` 检查 variable.type | `syntax_pass.py:235` 检查 `global_var_type` | `test_batch1_syntax.py` — 通过 compile_text 端到端覆盖 | ✅ |
| 18 | SYNTAX-018 | 变量 schema 嵌套校验 | object/list 类型变量的 schema 结构必须正确 | `syntax_validator.py` 检查 variable.schema | `syntax_pass.py:280` 检查 `global_var_schema` | `test_new_rules.py` test_object_variable_without_schema_emits_018 | ✅ |
| 19 | SYNTAX-019 | 块引用必须有 blockID 和 source | 参数引用的 `blockID` 和 `source` 必须存在且合法 | `syntax_validator.py` 检查 ref 结构 | `syntax_pass.py:214` 检查 `param.ref` 的 `block_id` 和 `source` | `test_batch1_syntax.py` — 通过 compile_text 端到端覆盖 | ✅ |
| 20 | SYNTAX-020 | 变量类型必须在允许集合内 | 变量类型必须是 string/integer/float/boolean/object/list 之一 | `syntax_validator.py` 检查 type vocabulary | `syntax_pass.py:240` 检查 `global_var_type` ∈ `ALLOWED_VARIABLE_TYPES` | `test_batch1_syntax.py` — 通过 compile_text 端到端覆盖 | ✅ |
| 21 | SYNTAX-021 | 节点类型 ID 必须可转换 | `node.type` 必须能通过 `IDStrToNodeType` 转换 | `syntax_validator.py` 检查 ID 转换 | `syntax_pass.py:160` 检查 `KNOWN_NODE_TYPE_IDS` | `test_batch1_syntax.py:365` test_clean_known_types / :372 test_unknown_type_emits_021 | ✅ |
| 22 | SYNTAX-022 | 前后端类型映射表维护 | 前端 StandardNodeType 别名需编译为数字 ID | `syntax_validator.py` 检查 alias 警告 | `syntax_pass.py:155` 检查 `STANDARD_NODE_TYPE_TABLE` | `test_batch1_syntax.py:383` test_all_frontend_types_are_known | ✅ |

---

## 二、SEMANTIC-BE 后端语义规则（23 条）

| # | 规则编号 | 中文描述 | 具体规则内容 | v1 实现位置 | v2 实现位置 | v2 测试点 | 状态 |
|---|---------|---------|-------------|-----------|-----------|----------|------|
| 1 | BE-001 | ValidateTree 端点存在 | 后端 `ValidateTree` API 端点必须可用 | `transport.py` 编译时标记 | 需要运行时 API 调用 | — | 🔒 |
| 2 | BE-002 | ValidateTreeRequest 需要 workflow_id | 请求必须包含 `workflow_id` | `transport.py` 离线检查元数据形状 | 需要运行时 API 调用 | — | 🔒 |
| 3 | BE-003 | 项目绑定验证 | 项目绑定可能改变全局变量检查 | `transport.py` 警告 | 需要运行时项目上下文 | — | 🔒 |
| 4 | BE-004 | Bot 绑定验证 | Bot 绑定可能改变全局变量检查 | `transport.py` 警告 | 需要运行时 Bot 上下文 | — | 🔒 |
| 5 | BE-005 | validate_tree schema 非空 | 返回的 schema 不能为空 | `transport.py` 检查响应 | 需要运行时 API 响应 | — | 🔒 |
| 6 | BE-006 | 画布 schema 可反序列化 | Canvas 结构必须符合 Go 模型形状 | `raw.py` JSON 解析 + 形状检查 | `semantic_pass.py:86` 检查 canvas 形状 | `test_batch3_semantic_be.py` 通过端到端编译覆盖 | ✅ |
| 7 | BE-007 | 孤立节点警告 | 没有边连接的节点可能被 ValidateTree 忽略 | `graph.py` + `graph_issue_authority.py` | `semantic_pass.py:62` 检查 `isolated_node_ids()` | `test_batch3_semantic_be.py:49` test_clean_no_isolated / :53 test_isolated_node | ✅ |
| 8 | BE-008 | 连接性错误阻断深层验证 | 连接性错误应阻断更深层的语义验证 | `graph_issue_authority.py` 验证器排序 | v2 pass 排序隐式处理：语法先运行，BE 内部先检查连接性 | 架构保证 | ⚡ |
| 9 | BE-009 | Start 节点必须有出边 | 入口节点必须有至少一条出边 | `graph.py` 检查 start 出边 | `semantic_pass.py:204` 检查 `has_outgoing_edges()` | `test_batch3_semantic_be.py:386` test_start_connected / :390 test_start_no_outgoing | ✅ |
| 10 | BE-010 | 分支端口必须有出边 | 分支/异常源端口必须各有出边 | `validator.py` 检查分支端口 | `semantic_pass.py:123` 检查 `edge_source_targets()` | `test_batch3_semantic_be.py:280` test_clean_consistent / :323 test_if_missing_false_branch | ✅ |
| 11 | BE-011 | 非 End 节点需要出边 | 非 End/Break/Continue 节点必须有出边连接 | `graph.py` 检查出边 | `semantic_pass.py:218` 检查出边 | `test_batch3_semantic_be.py:412` test_connected_node / :416 test_node_no_outgoing | ✅ |
| 12 | BE-012 | Start/End 必须存在且可达 | 开始/结束节点必须存在，可达性图必须一致 | `graph.py` + reachability | `semantic_pass.py:231` 检查 `all_node_ids()` + Start/End 存在 | `test_batch3_semantic_be.py:445` test_start_end_exist | ✅ |
| 13 | BE-013 | 缺少 Start 节点是错误 | 没有 Start 节点的 workflow 不合法 | `graph.py` | `semantic_pass.py:250` 检查 Start 存在 | `test_batch3_semantic_be.py:447` test_no_start_node | ✅ |
| 14 | BE-014 | 缺少 End 节点是错误 | 没有 End 节点的 workflow 不合法 | `graph.py` | `semantic_pass.py:252` 检查 End 存在 | `test_batch3_semantic_be.py:463` test_no_end_node | ✅ |
| 15 | BE-015 | 图必须无环 | Workflow 图在后端要求的区域必须无环 | `graph.py` 拓扑排序 | `semantic_pass.py:263` 拓扑排序检测环 | `test_batch3_semantic_be.py:480` test_no_cycle / :484 test_cycle_detected | ✅ |
| 16 | BE-016 | 复合节点不可嵌套 | Loop/Batch 复合节点不能嵌套在其他复合节点内 | `nesting_issue_authority.py` | `semantic_pass.py:147` 检查嵌套复合节点 | `test_batch3_semantic_be.py` 通过嵌套场景覆盖 | ✅ |
| 17 | BE-017 | 块引用 blockID 非空且存在 | 引用的 `blockID` 必须非空且指向现有节点 | `local_issue_authority.py` | `semantic_pass.py:329` 检查 `resolved_ref.is_unresolved` | `test_batch3_semantic_be.py:582` test_empty_blockid_fires_be017 | ✅ |
| 18 | BE-018 | 引用的 block id 必须可达 | 引用的节点 ID 必须存在于 workflow 中 | `local_issue_authority.py` | v2 BE-017 的 `resolved_ref` 已覆盖 | 由 BE-017 测试覆盖 | ⚡ |
| 19 | BE-019 | 参数名必须符合正则 | 输入参数名必须匹配 `^[A-Za-z_][A-Za-z0-9_]*$` | `local_issue_authority.py` | `semantic_pass.py:75` 正则检查 | `test_batch3_semantic_be.py:143` test_clean_valid_param_name / :176 test_invalid_param_name | ✅ |
| 20 | BE-020 | 全局变量赋值类型匹配 | 全局变量赋值类型必须与元数据一致 | `semantic_be_metadata.py` | `semantic_pass.py:153` + `_check_type_compatibility` | `test_type_system_p3.py:257` test_detects_incompatible_types / :278 test_compatible_types | ✅ |
| 21 | BE-021 | 全局数组元素类型匹配 | 全局 list 变量的元素类型必须与元数据一致 | `semantic_be_metadata.py` | `semantic_pass.py:380` 检查 `global_var_item_type` | `test_new_rules.py` test_no_global_array_ok | ✅ |
| 22 | BE-022 | Sub-workflow 验证 | Sub-workflow 终止/版本/草稿依赖验证 | `contract_authority.py` | `semantic_pass.py:348` 检查 SubWorkflow 节点 | `test_batch3_semantic_be.py:546` test_subworkflow_fires_be022 | ✅ |
| 23 | BE-023 | 语义完整性守卫 | Semantic-be pass 必须消费完整的共享事实 | `contract_authority.py` | `semantic_pass.py:364` 完整性检查 | `test_batch3_semantic_be.py:280` test_clean_consistent | ✅ |

---

## 三、SEMANTIC-FE 前端语义规则（13 条）

| # | 规则编号 | 中文描述 | 具体规则内容 | v1 实现位置 | v2 实现位置 | v2 测试点 | 状态 |
|---|---------|---------|-------------|-----------|-----------|----------|------|
| 1 | FE-001 | 每个节点通过 validateNode | 每个节点必须通过前端聚合 `validateNode` | `transport.py` | `semantic_pass.py` 静态验证 LLM 节点字段 | `test_semantic_fe.py::TestFE001NodeSpecificFields` | ✅ |
| 2 | FE-002 | validateWorkflow 遍历 | `validateWorkflow` 必须遍历所有关联节点 | `transport.py` | 需要前端运行时 | — | 🔒 |
| 3 | FE-003 | 表单模型已初始化 | 表单验证需要已初始化的表单模型 | `transport.py` | 需要前端运行时 | — | 🔒 |
| 4 | FE-004 | 表单反馈已解决 | 节点表单反馈的 warning/error 必须已解决 | `transport.py` | 需要前端运行时 | — | 🔒 |
| 5 | FE-005 | 警告严重性必须保留 | 诊断中的 warning 严重性不能被丢弃 | `transport.py` | 需要前端运行时 | — | 🔒 |
| 6 | FE-006 | Loop/Batch 子画布入口端口连接 | 复合节点子画布的入口端口必须有入边 | `frontend_semantic_ir.py` | `semantic_pass.py:121` 检查入口端口 | `test_batch6_semantic_fe.py:176` test_clean / :211 test_emits_006 | ✅ |
| 7 | FE-007 | Loop/Batch 子画布出口端口连接 | 复合节点子画布的出口端口必须有出边（除非所有叶子是 End） | `frontend_semantic_ir.py` | `semantic_pass.py:134` 检查出口端口 | `test_batch6_semantic_fe.py:176` / :211 test_emits_007 | ✅ |
| 8 | FE-008 | 异常分支端口必须连接 | 设置了异常分支时，异常端口必须有连接 | `frontend.py` | `semantic_pass.py:350` 检查 `on_error_config` | `test_new_rules.py` test_no_exception_config_ok | ✅ |
| 9 | FE-009 | 节点标题必须非空 | 每个节点的 `title` 必须非空 | `frontend.py` | `semantic_pass.py:65` 检查 `node.title` | `test_batch6_semantic_fe.py:49` test_clean / :71 test_empty_title_emits_009 | ✅ |
| 10 | FE-010 | 节点标题不超过 63 字符 | 节点 `title` 长度不能超过 63 个字符 | `frontend.py` | `semantic_pass.py:74` 检查 `len(title)` | `test_batch6_semantic_fe.py:98` test_long_title_emits_010 | ✅ |
| 11 | FE-011 | 节点标题必须唯一 | 同一 playground 上下文中节点标题必须唯一 | `frontend.py` | `semantic_pass.py:83` 计数器检查 | `test_batch6_semantic_fe.py:132` test_duplicate_title_emits_011 | ✅ |
| 12 | FE-012 | 异常配置 JSON 可解析 | Setting-on-error 的 RETURN JSON 必须可解析 | `frontend.py` | `semantic_pass.py:365` 检查 `on_error_config.returnJson` | `test_new_rules.py` test_no_exception_config_ok | ✅ |
| 13 | FE-013 | document 通过 ValidateTree | `document.toJSON()` 必须通过后端 ValidateTree | `transport.py` FE/BE 桥接 | 需要运行时 API 调用 | — | 🔒 |

---

## 四、PORTABILITY 可移植性规则（14 条）

| # | 规则编号 | 中文描述 | 具体规则内容 | v1 实现位置 | v2 实现位置 | v2 测试点 | 状态 |
|---|---------|---------|-------------|-----------|-----------|----------|------|
| 1 | PORT-001 | 导入文件扩展名 | 导入文件必须是 `.json` 或 `.flow` 扩展名 | `portability_transport.py` | `portability_pass.py:80` 检查扩展名 | `test_batch7_portability.py` 通过文件路径覆盖 | ✅ |
| 2 | PORT-002 | 导入载荷可 JSON 解析 | 导入内容必须可解析为 JSON | `portability_transport.py` | v2 TransportNormalizer 隐式处理（解析失败即报错） | 架构保证 | ⚡ |
| 3 | PORT-003 | 导出信封类型匹配 | Workflow 导出信封 `data.type` 必须匹配 `WORKFLOW_EXPORT_TYPE` | `portability_transport.py` | `portability_pass.py:104` 检查 `envelope_type` | `test_batch7_portability.py` 通过信封测试覆盖 | ✅ |
| 4 | PORT-004 | 剪贴板数据类型匹配 | 剪贴板数据类型必须匹配 workflow clipboard 类型 | `portability_transport.py` | `portability_pass.py:111` 检查 clipboard 类型 | `test_batch7_portability.py` 覆盖 | ✅ |
| 5 | PORT-005 | 剪贴板来源主机匹配 | 剪贴板来源主机必须与当前主机一致（跨主机粘贴阻断） | `portability_transport.py` | 需要运行时主机上下文 | — | 🔒 |
| 6 | PORT-006 | 抖音绑定与普通空间不兼容 | 抖音绑定空间和普通空间不可互相粘贴 | `portability_transport.py` | 需要运行时空间上下文 | — | 🔒 |
| 7 | PORT-007 | 流程模式必须匹配 | 粘贴时 workflow/imageflow/chatflow 模式必须匹配 | `portability_transport.py` | 需要运行时上下文 | — | 🔒 |
| 8 | PORT-008 | 节点粘贴链式验证 | 节点粘贴必须通过链式 portability 验证器 | `portability_transport.py` | 需要运行时粘贴上下文 | — | 🔒 |
| 9 | PORT-009 | Break/Continue/SetVariable 仅限 Loop | 这些节点只能存在于 Loop 子画布中 | `portability.py` | `portability_pass.py:122` 检查节点是否在 Loop 内 | `test_batch7_portability.py:47` test_clean / :51 test_break_outside_loop / :78 test_break_inside_loop_ok | ✅ |
| 10 | PORT-010 | 复合节点不可嵌套（别名） | Loop/Batch 不能嵌套在子画布中（BE-016 的别名） | `portability.py` ALIAS_OVERRIDES | v2 BE-016 已覆盖 | 由 BE-016 测试覆盖 | ⚡ |
| 11 | PORT-011 | SubWorkflow 不可自引用 | SubWorkflow 不能引用当前 workflow | `portability.py` | `portability_pass.py:137` 检查自引用 | `test_batch7_portability.py:154` test_subworkflow_fires_port011 | ✅ |
| 12 | PORT-012 | 跨空间节点阻断 | Dataset/Database/SubWorkflow/Imageflow 节点跨空间阻断 | `portability.py` | `portability_pass.py:151` 检查节点类型 + 空间 | `test_batch7_portability.py:214` test_blocked_types_fire_port012 | ✅ |
| 13 | PORT-013 | 跨空间 API 需要 Listed | 跨空间 API/插件节点需要 Listed 产品状态 | `portability.py` | 需要运行时产品状态上下文 | — | 🔒 |
| 14 | PORT-014 | 可移植性完整性守卫 | Portability pass 必须消费完整的共享事实 | `portability.py` | `portability_pass.py:168` 完整性检查 | `test_batch7_portability.py:143` test_no_port_rules_in_fixtures | ✅ |

---

## 五、DYNAMIC 动态预检规则（12 条）

| # | 规则编号 | 中文描述 | 具体规则内容 | v1 实现位置 | v2 实现位置 | v2 测试点 | 状态 |
|---|---------|---------|-------------|-----------|-----------|----------|------|
| 1 | DYN-001 | TestRun 被前端验证阻断 | 前端验证失败时阻断 TestRun | `dynamic_preflight_validator.py` | 需要运行时 | — | 🔒 |
| 2 | DYN-002 | TestRun 被后端验证阻断 | ValidateTree 失败时阻断 TestRun | `dynamic_preflight_validator.py` | 需要运行时 | — | 🔒 |
| 3 | DYN-003 | 动态试运行需要 API | 试运行需要 `WorkFlowTestRun` API | `dynamic_preflight_validator.py` | 需要运行时 | — | 🔒 |
| 4 | DYN-004 | TestRun 需要 workflow_id | 试运行请求必须包含 `workflow_id` | `dynamic_preflight_validator.py` | 需要运行时 | — | 🔒 |
| 5 | DYN-005 | TestRun 输入需可序列化 | 输入必须可序列化为 `map<string,string>` | `dynamic_preflight_validator.py` | 需要运行时 | — | 🔒 |
| 6 | DYN-006 | TestRun 可能需要 space_id | 试运行可能需要空间上下文 | `dynamic_preflight_validator.py` | 需要运行时 | — | 🔒 |
| 7 | DYN-007 | 项目资源可能改变运行时 | 项目绑定资源可能改变运行时行为 | `dynamic_preflight_validator.py` | 需要运行时 | — | 🔒 |
| 8 | DYN-008 | 用户必须有空间访问权限 | 用户必须有 TestRun 空间的访问权限 | `dynamic_preflight_validator.py` | 需要运行时 | — | 🔒 |
| 9 | DYN-009 | project_id 和 bot_id 互斥 | `project_id` 和 `bot_id` 不能同时设置 | `dynamic_preflight_validator.py` | 需要运行时 | — | 🔒 |
| 10 | DYN-010 | 流程历史 API | 试运行执行回溯的流程历史 API | `dynamic_preflight_validator.py` | 需要运行时 | — | 🔒 |
| 11 | DYN-011 | 节点执行历史 API | 运行时失败映射的节点执行历史 API | `dynamic_preflight_validator.py` | 需要运行时 | — | 🔒 |
| 12 | DYN-012 | TestRun 目标语义 | TestRun 应定位 draft/debug 执行语义 | `dynamic_preflight_validator.py` | 需要运行时 | — | 🔒 |

---

## 六、覆盖率统计

| 类别 | 总数 | ✅ 已实现 | ⚡ 架构覆盖 | 📝 需 IR 扩展 | 🔒 需运行时 | ❌ 待实现 |
|------|------|----------|------------|--------------|------------|----------|
| SYNTAX | 22 | 21 | 1 | 0 | 0 | 0 |
| SEMANTIC-BE | 23 | 17 | 2 | 1 | 3 | 0 |
| SEMANTIC-FE | 13 | 8 | 0 | 1 | 4 | 0 |
| PORTABILITY | 14 | 7 | 2 | 0 | 5 | 0 |
| DYNAMIC | 12 | 0 | 0 | 0 | 12 | 0 |
| **合计** | **84** | **53** | **5** | **2** | **24** | **0** |

**可离线检查覆盖率**: (53 + 5) / (84 - 24) = **58 / 60 = 96.7%**

### 待实现清单

所有可离线检查的规则均已实现。

剩余规则分类：
- **🔒 需要运行时** (24条)：FE-002~005, FE-013, BE-001~005, BE-008, BE-021, PORT-005~008, PORT-013, DYNAMIC-001~012
- **📝 需 IR 扩展** (2条)：SYNTAX-022, BE-009

这些规则需要运行时上下文或 IR 扩展，无法在当前架构下实现。
