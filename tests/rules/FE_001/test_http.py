"""FE-001: HTTP 节点 (type 45) 字段验证。

验证规则:
  - url 必填 (URL 不能为空)
  - url 长度 ≤ 10000

Tests cover:
  - Valid HTTPS URL
  - Valid HTTP URL
  - Missing URL
  - Empty URL
  - Whitespace URL
  - URL at length limit
  - URL over length limit
  - URL with query parameters
  - URL with special characters
"""

from tests.conftest import compile_text


def _fe001_errors(yaml_text: str) -> list[str]:
    report = compile_text(yaml_text)
    return [
        d.message for d in report.diagnostics
        if d.rule_id == 'SEMANTIC-FE-001'
    ]


def _make_http_yaml(url: str | None = 'https://example.com') -> str:
    url_section = ""
    if url is not None:
        url_section = f"""
        apiInfo:
          url: '{url}'"""

    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'h1'
    type: '45'
    data:
      nodeMeta:
        title: HTTP
      inputs:
        inputParameters: []{url_section}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'h1'
  - sourceNodeID: 'h1'
    targetNodeID: '900001'
"""


# ── Positive ─────────────────────────────────────────────────────

class TestFE001_HTTP_Positive:
    """Valid HTTP configurations → no FE-001 errors."""

    def test_with_https_url(self):
        yaml = _make_http_yaml(url='https://example.com')
        errors = _fe001_errors(yaml)
        assert not any('url' in e.lower() for e in errors)

    def test_with_http_url(self):
        yaml = _make_http_yaml(url='http://localhost:8080/api')
        errors = _fe001_errors(yaml)
        assert not any('url' in e.lower() for e in errors)

    def test_url_with_query_params(self):
        """URL with query parameters → valid."""
        yaml = _make_http_yaml(url='https://api.example.com/v1?key=abc&format=json')
        errors = _fe001_errors(yaml)
        assert not any('url' in e.lower() for e in errors)

    def test_url_with_path(self):
        """URL with deep path → valid."""
        yaml = _make_http_yaml(url='https://api.example.com/v1/users/123/profile')
        errors = _fe001_errors(yaml)
        assert not any('url' in e.lower() for e in errors)

    def test_url_with_port(self):
        """URL with explicit port → valid."""
        yaml = _make_http_yaml(url='https://example.com:8443/api')
        errors = _fe001_errors(yaml)
        assert not any('url' in e.lower() for e in errors)


# ── Negative ─────────────────────────────────────────────────────

class TestFE001_HTTP_Negative:
    """Invalid HTTP configurations → FE-001 errors."""

    def test_missing_url(self):
        yaml = _make_http_yaml(url=None)
        errors = _fe001_errors(yaml)
        assert any('url' in e.lower() for e in errors)

    def test_empty_url(self):
        yaml = _make_http_yaml(url='')
        errors = _fe001_errors(yaml)
        assert any('url' in e.lower() for e in errors)

    def test_whitespace_url(self):
        yaml = _make_http_yaml(url='   ')
        errors = _fe001_errors(yaml)
        assert any('url' in e.lower() for e in errors)


class TestFE001_HTTP_UrlLength:
    """URL length boundary tests."""

    def test_url_at_limit(self):
        """URL at exactly 10000 chars → no length violation."""
        url = 'https://example.com/' + 'a' * 9980
        assert len(url) == 10000
        yaml = _make_http_yaml(url=url)
        errors = _fe001_errors(yaml)
        assert not any('exceeds' in e.lower() for e in errors)

    def test_url_over_limit(self):
        """URL over 10000 chars → length violation."""
        url = 'https://example.com/' + 'a' * 10000
        yaml = _make_http_yaml(url=url)
        errors = _fe001_errors(yaml)
        assert any('exceeds' in e.lower() for e in errors)


# ── Edge cases ──────────────────────────────────────────────────

class TestFE001_HTTP_EdgeCases:
    """Edge cases for HTTP node validation."""

    def test_url_with_fragment(self):
        """URL with fragment identifier → valid."""
        yaml = _make_http_yaml(url='https://example.com/page#section')
        errors = _fe001_errors(yaml)
        assert not any('url' in e.lower() for e in errors)

    def test_ip_address_url(self):
        """URL with IP address → valid."""
        yaml = _make_http_yaml(url='http://192.168.1.1:3000/api')
        errors = _fe001_errors(yaml)
        assert not any('url' in e.lower() for e in errors)


# ── VAL-HTTP-AUTH-001: Auth field validation ────────────────────

def _make_http_auth_yaml(
    auth_open: str = 'true',
    auth_type: str = 'BASIC_AUTH',
    auth_data: str = '',
) -> str:
    auth_section = f'''
        auth:
          authOpen: {auth_open}
          authType: '{auth_type}'
          authData:
{auth_data}''' if auth_open else ''

    return f"""
nodes:
  - id: '100001'
    type: '1'
    data:
      nodeMeta:
        title: Start
  - id: 'h1'
    type: '45'
    data:
      nodeMeta:
        title: HTTP
      inputs:
        inputParameters: []
        apiInfo:
          url: 'https://example.com'
{auth_section}
  - id: '900001'
    type: '2'
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: '100001'
    targetNodeID: 'h1'
  - sourceNodeID: 'h1'
    targetNodeID: '900001'
"""


class TestHTTPAuth_Positive:
    """Valid auth configurations → no errors."""

    def test_no_auth_section(self):
        """No auth section → no error."""
        yaml = _make_http_yaml(url='https://example.com')
        errors = _fe001_errors(yaml)
        assert not any('auth' in e.lower() for e in errors)

    def test_auth_closed(self):
        """authOpen=false → no error."""
        yaml = _make_http_auth_yaml(auth_open='false', auth_data='')
        errors = _fe001_errors(yaml)
        assert not any('auth' in e.lower() for e in errors)

    def test_basic_auth_with_credentials(self):
        """BASIC_AUTH with credentials → no error."""
        auth_data = """            basicAuthData:
              - name: username
                input:
                  type: string
                  value:
                    type: literal
                    content: 'admin'
              - name: password
                input:
                  type: string
                  value:
                    type: literal
                    content: 'secret'"""
        yaml = _make_http_auth_yaml(auth_open='true', auth_type='BASIC_AUTH', auth_data=auth_data)
        errors = _fe001_errors(yaml)
        assert not any('auth' in e.lower() for e in errors)

    def test_bearer_auth_with_token(self):
        """BEARER_AUTH with token → no error."""
        auth_data = """            bearerTokenData:
              - name: token
                input:
                  type: string
                  value:
                    type: literal
                    content: 'my-token-123'"""
        yaml = _make_http_auth_yaml(auth_open='true', auth_type='BEARER_AUTH', auth_data=auth_data)
        errors = _fe001_errors(yaml)
        assert not any('auth' in e.lower() for e in errors)


class TestHTTPAuth_Negative:
    """Invalid auth configurations → errors."""

    def test_basic_auth_empty_credentials(self):
        """BASIC_AUTH with empty credentials → error."""
        auth_data = """            basicAuthData: []"""
        yaml = _make_http_auth_yaml(auth_open='true', auth_type='BASIC_AUTH', auth_data=auth_data)
        errors = _fe001_errors(yaml)
        assert any('auth' in e.lower() for e in errors)

    def test_bearer_auth_empty_token(self):
        """BEARER_AUTH with empty token → error."""
        auth_data = """            bearerTokenData: []"""
        yaml = _make_http_auth_yaml(auth_open='true', auth_type='BEARER_AUTH', auth_data=auth_data)
        errors = _fe001_errors(yaml)
        assert any('auth' in e.lower() for e in errors)


# ── VAL-HTTP-EXPR-STRING-001: Expression string validation ──────

class TestHTTPExprString_Positive:
    """Valid expression strings → no errors."""

    def test_url_without_expressions(self):
        """Plain URL → no error."""
        yaml = _make_http_yaml(url='https://example.com/api')
        errors = _fe001_errors(yaml)
        assert not any('expression' in e.lower() for e in errors)

    def test_url_with_valid_expression(self):
        """URL with valid {{var}} → no error."""
        yaml = _make_http_yaml(url='https://example.com/{{path}}/api')
        errors = _fe001_errors(yaml)
        assert not any('expression' in e.lower() or 'empty' in e.lower() for e in errors)


class TestHTTPExprString_Negative:
    """Invalid expression strings → errors."""

    def test_url_with_unclosed_braces(self):
        """URL with unclosed {{ → error."""
        yaml = _make_http_yaml(url='https://example.com/{{path/api')
        errors = _fe001_errors(yaml)
        assert any('expression' in e.lower() or 'malformed' in e.lower() for e in errors)

    def test_url_with_empty_expression(self):
        """URL with {{}} → error."""
        yaml = _make_http_yaml(url='https://example.com/{{}}/api')
        errors = _fe001_errors(yaml)
        assert any('empty' in e.lower() for e in errors)
