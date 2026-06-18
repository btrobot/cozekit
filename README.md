# cozekit

Static validator for [Coze](https://www.coze.com/) workflow files.

Validates YAML/JSON workflow files for syntax, semantic, and graph errors **without a runtime** — catch problems before deploying to the Coze platform.

```
$ cozekit check workflow.yaml
  ✗ workflow.yaml  (1 diagnostics)
    ● SEMANTIC-BE-017 :22  reference blockID "" does not point to an existing node
```

## Install

```bash
pip install cozekit
```

Or from source:

```bash
git clone https://github.com/your-org/cozekit.git
cd cozekit
pip install -e ".[dev]"
```

## Usage

```bash
# Validate a single file
cozekit check workflow.yaml

# Validate all workflow files in a directory
cozekit check ./workflows/

# JSON output (for CI pipelines)
cozekit check workflow.yaml -f json

# Machine-readable single-line output
cozekit check workflow.yaml -f compact

# Quiet mode — only show files with errors
cozekit check ./workflows/ -q

# Show version and capabilities
cozekit info
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0`  | Clean — no violations found |
| `1`  | Violations found |
| `2`  | Compiler internal error |

## What it checks

cozekit validates Coze workflow files across four layers:

| Layer | Category | Examples |
|-------|----------|---------|
| 1 | **Syntax** | Required fields, valid types, node/edge structure |
| 2 | **Semantic** | Field values, type consistency, reference integrity |
| 3 | **Graph** | Connectivity, cycles, isolated nodes, branch completeness |
| 4 | **Portability** | Cross-format compatibility, self-references |

### Supported formats

- `.yaml` / `.yml` — Coze workflow source format (commercial export)
- `.json` — Coze workflow JSON export format
- `.flow` — Coze workflow flow format

## Architecture

cozekit uses a textbook compiler architecture:

```
Input → Transport → AST → Semantic Model → Passes → Diagnostics
         (parse)   (build)  (symbol table)  (rules)   (report)
```

- **Transport**: normalizes YAML/JSON/flow input into a common representation
- **AST**: structured node/edge/canvas representation
- **Semantic Model**: symbol table, scope tree, type system
- **Passes**: independent rule validators (syntax, semantic-be, semantic-fe, portability)
- **Diagnostics**: structured error/warning output with source locations

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=cozekit

# Lint a single file programmatically
python -c "from cozekit import compile_path; r = compile_path('workflow.yaml'); print(r.summary)"
```

## License

MIT
