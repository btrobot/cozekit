# 运行时依赖的验证规则（编译期不可检查）

本文档记录 coze-studio 中**依赖运行时状态**的验证逻辑。
这些检查在 coze-studio 的前端/后端运行时中执行，我们的静态验证器无法复现。

---

## LLM prompt 必填检查

**规则**: FE-001 (LLM node prompt)

**coze-studio 实现** (`llm-form-meta.tsx` L353-362):
```typescript
[userPromptFieldKey]: (({ value, formValues, context }) => {
  const { playgroundContext } = context;
  const modelType = get(formValues, 'model.modelType');
  const curModel = playgroundContext?.models?.find(
    model => model.model_type === modelType,
  );
  const isUserPromptRequired = curModel?.is_up_required ?? false;
  if (!isUserPromptRequired) {
    return undefined;  // 跳过验证
  }
  return value?.length ? undefined : 'prompt is empty';
})
```

**依赖的运行时状态**:
- `playgroundContext.models` — 平台模型注册表（API 动态获取）
- `curModel.is_up_required` — 模型是否要求 user prompt（布尔值，模型配置属性）

**结论**: `prompt` 字段是否必填取决于**模型的 `is_up_required` 属性**，
该属性在运行时从平台模型列表获取，编译期无法确定。

**我们的处理**:
- 不单独检查 `prompt` 必填
- 改为检查 `prompt` 和 `systemPrompt` **至少一个非空**
- 这是保守的下界检查：至少要有一个有意义的 prompt 内容

**真实场景举例** (X44_Pyingyu_picture-draft.yaml):
```yaml
- name: prompt
  input:
    type: string
    value: ""          # 空 prompt — 合法，因为 model.is_up_required = false
- name: systemPrompt
  input:
    type: string
    value: "根据学习目标{{target}}..."  # systemPrompt 有内容
```

---

## 未来可能新增的运行时依赖规则

如有新的发现，在此追加。
