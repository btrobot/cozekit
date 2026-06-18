# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-06-18

### Added
- Initial release
- Textbook compiler architecture: Transport → AST → Semantic → Passes → Diagnostics
- YAML source format support (commercial Coze export)
- JSON export format support
- CLI tool with `check` and `info` commands
- Three output formats: text (human), json, compact (machine)
- Batch directory validation
- 787 unit tests covering syntax, semantic, graph, and portability rules
- Validation of 33 real-world Coze workflow files

### Validation Rules
- **SYNTAX**: 22 rules (canvas structure, node/edge shape, version, types)
- **SEMANTIC-BE**: 23 rules (connectivity, cycles, references, composites)
- **SEMANTIC-FE**: 14 rules (node-specific fields, prompts, outputs, titles)
- **PORTABILITY**: 14 rules (cross-format, cross-space, self-references)
