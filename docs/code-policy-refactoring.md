# 代码策略重构分析

## 问题分类

### 1. 魔法字符串 (Magic Strings)

**问题**: 代码中直接使用字符串字面量表示节点类型、端口类型等。

**示例**:
```python
# 差
if node.node_type == '8':  # If node
if node.node_type == '21':  # Loop node

# 好
if node.node_type == IF_NODE_TYPE_ID:
if node.node_type == LOOP_NODE_TYPE_ID:
```

**影响**:
- 可读性差：需要注释说明含义
- 维护性差：修改需要全局搜索
- 容易出错：拼写错误不会被编译器捕获

### 2. 魔法数字 (Magic Numbers)

**问题**: 代码中直接使用数字字面量表示常量。

**示例**:
```python
# 差
if len(title) > 63:
if temperature < 0 or temperature > 2:

# 好
if len(title) > TITLE_MAX_LENGTH:
if temperature < TEMPERATURE_MIN or temperature > TEMPERATURE_MAX:
```

### 3. 硬编码集合 (Hardcoded Sets)

**问题**: 在多处定义相同的集合常量。

**示例**:
```python
# 在多个文件中重复定义
COMPOSITE_TYPES = {'21', '28', '8'}
LOOP_CONTROL_TYPES = {'19', '29', '20'}
```

### 4. 局部常量 (Local Constants)

**问题**: 在函数或类内部定义应该全局共享的常量。

**示例**:
```python
# 差 - 在文件顶部定义，但只在局部使用
_VARIABLE_NODE_TYPE = '11'

# 好 - 从 constants.py 导入
from ..passes.constants import VARIABLE_NODE_TYPE_ID
```

## 重构策略

### 阶段 1: 常量集中管理

**目标**: 所有常量定义在 `constants.py` 中。

**原则**:
1. 单一职责：每个常量文件只负责一类常量
2. 命名规范：使用 `UPPER_SNAKE_CASE`
3. 类型明确：使用 `frozenset` 代替 `set` 用于不可变集合
4. 文档完整：每个常量都有注释说明

**实现**:
```python
# constants.py

# ── 节点类型 ID ──────────────────────────────────────────────
START_NODE_TYPE_ID = '1'
END_NODE_TYPE_ID = '2'
LLM_NODE_TYPE_ID = '3'
CODE_NODE_TYPE_ID = '5'
IF_NODE_TYPE_ID = '8'
SUBWORKFLOW_NODE_TYPE_ID = '9'
VARIABLE_NODE_TYPE_ID = '11'
QUESTION_NODE_TYPE_ID = '18'
INTENT_NODE_TYPE_ID = '21'
LOOP_NODE_TYPE_ID = '21'
BATCH_NODE_TYPE_ID = '28'

# ── 节点类型集合 ──────────────────────────────────────────────
COMPOSITE_NODE_TYPE_IDS = frozenset({
    IF_NODE_TYPE_ID,
    LOOP_NODE_TYPE_ID,
    BATCH_NODE_TYPE_ID,
    CONTINUE_NODE_TYPE_ID,
    BREAK_NODE_TYPE_ID,
})

# ── 验证规则常量 ──────────────────────────────────────────────
TITLE_MAX_LENGTH = 63
TEMPERATURE_MIN = 0.0
TEMPERATURE_MAX = 2.0
MAX_TOKENS_MIN = 1
QUERY_LIMIT_MIN = 1
QUERY_LIMIT_MAX = 1000

# ── 参数名模式 ──────────────────────────────────────────────
PARAM_NAME_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
```

### 阶段 2: 消除重复定义

**目标**: 删除所有重复的常量定义。

**检查清单**:
- [ ] `semantic_pass.py` 中的 `IF_NODE_TYPE`, `SUBWORKFLOW_TYPE`, `COMPOSITE_TYPES`
- [ ] `portability_pass.py` 中的 `LOOP_CONTROL_TYPES`, `COMPOSITE_TYPES`, `SUBWORKFLOW_NODE_TYPE`
- [ ] `builder.py` 中的 `_COMPOSITE_TYPES`
- [ ] `analysis_graph.py` 中的 `_VARIABLE_NODE_TYPE`

### 阶段 3: 统一导入方式

**目标**: 所有文件从 `constants.py` 导入常量。

**原则**:
1. 明确导入：使用 `from ... import ...` 而不是 `import ...`
2. 按需导入：只导入需要的常量
3. 避免通配符：不要使用 `from ... import *`

### 阶段 4: 更新测试

**目标**: 测试代码也使用常量。

**原则**:
1. 测试数据可以使用字符串字面量（因为是输入数据）
2. 断言中应该使用常量（如果引用实现代码的常量）

## 重构优先级

### 高优先级 (立即修复)

1. **节点类型 ID**: 已经完成
2. **验证规则常量**: 标题长度、温度范围等
3. **重复集合定义**: `COMPOSITE_TYPES` 等

### 中优先级 (下一步)

1. **端口类型常量**: `sourcePortID`, `targetPortID` 等
2. **错误消息常量**: 统一错误消息格式
3. **配置常量**: 文件路径、API 端点等

### 低优先级 (长期改进)

1. **类型别名**: 使用 `TypeAlias` 定义类型
2. **枚举类型**: 对于有限集合使用 `Enum`
3. **配置文件**: 外部化可配置常量

## 验证方法

### 静态检查

```bash
# 检查是否有未使用的常量
grep -r "^[A-Z_]* = " constants.py | while read line; do
  name=$(echo "$line" | cut -d' ' -f1)
  if ! grep -r "$name" . --include="*.py" | grep -v constants.py | grep -q .; then
    echo "Unused: $name"
  fi
done

# 检查是否有硬编码的节点类型 ID
grep -r "'[0-9]'" . --include="*.py" | grep -v constants.py | grep -v test_
```

### 测试验证

```bash
# 运行所有测试
python -m pytest tests/ -q

# 运行架构测试
python -m pytest tests/test_architecture.py -v
```

## 预期收益

1. **可维护性**: 修改常量只需改一处
2. **可读性**: 代码自文档化
3. **安全性**: 编译器捕获拼写错误
4. **一致性**: 统一的命名和使用方式
5. **可测试性**: 常量可以被 mock 或覆盖
