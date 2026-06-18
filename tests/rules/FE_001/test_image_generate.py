"""FE-001: Image Generate 节点 (type 16) 字段验证。

验证规则:
  - model 必填 (必须选择模型)

Tests cover:
  - Valid model
  - Missing model
  - Empty model
  - Model with special characters
  - Multiple model names
"""

from tests.conftest import compile_text


def _fe001_errors(yaml_text: str) -> list[str]:
    report = compile_text(yaml_text)
    return [
        d.message for d in report.diagnostics
        if d.rule_id == 'SEMANTIC-FE-001'
    ]


def _make_image_gen_yaml(model: str | None = 'dall-e-3') -> str:
    model_section = ""
    if model is not None:
        model_section = f"""
        modelSetting:
          model: '{model}'"""

    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'ig1'
    type: '16'
    data:
      nodeMeta:
        title: ImageGen
      inputs:
        inputParameters: []{model_section}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'ig1'
  - sourceNodeID: 'ig1'
    targetNodeID: '900001'
"""


# ── Positive ─────────────────────────────────────────────────────

class TestFE001_ImageGenerate_Positive:
    """Valid image generate configurations → no FE-001 errors."""

    def test_with_model(self):
        yaml = _make_image_gen_yaml(model='dall-e-3')
        errors = _fe001_errors(yaml)
        assert not any('model' in e.lower() for e in errors)

    def test_with_different_model(self):
        """Different model name → valid."""
        yaml = _make_image_gen_yaml(model='stable-diffusion-xl')
        errors = _fe001_errors(yaml)
        assert not any('model' in e.lower() for e in errors)

    def test_model_with_hyphens(self):
        """Model name with hyphens → valid."""
        yaml = _make_image_gen_yaml(model='midjourney-v6')
        errors = _fe001_errors(yaml)
        assert not any('model' in e.lower() for e in errors)


# ── Negative ─────────────────────────────────────────────────────

class TestFE001_ImageGenerate_Negative:
    """Invalid image generate configurations → FE-001 errors."""

    def test_missing_model(self):
        yaml = _make_image_gen_yaml(model=None)
        errors = _fe001_errors(yaml)
        assert any('model' in e.lower() for e in errors)

    def test_empty_model(self):
        yaml = _make_image_gen_yaml(model='')
        errors = _fe001_errors(yaml)
        assert any('model' in e.lower() for e in errors)

    def test_whitespace_model(self):
        """Whitespace-only model → error."""
        yaml = _make_image_gen_yaml(model='   ')
        errors = _fe001_errors(yaml)
        assert any('model' in e.lower() for e in errors)


# ── Edge cases ──────────────────────────────────────────────────

class TestFE001_ImageGenerate_EdgeCases:
    """Edge cases for image generate node validation."""

    def test_no_model_setting_section(self):
        """No modelSetting section at all → model missing error."""
        yaml = """
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'ig1'
    type: '16'
    data:
      nodeMeta:
        title: ImageGen
      inputs:
        inputParameters: []
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'ig1'
  - sourceNodeID: 'ig1'
    targetNodeID: '900001'
"""
        errors = _fe001_errors(yaml)
        assert any('model' in e.lower() for e in errors)
