# Code Review: coze_yaml_compiler_v2

**Date:** 2026-06-17  
**Reviewer:** Compiler Expert  
**Status:** APPROVE with minor issues

## Executive Summary

The refactoring from rule-checker to textbook compiler front-end architecture is **excellent**. The pipeline is clean, layers are well-separated, and the code follows compiler design principles correctly.

## Architecture Review

### ✅ Strengths

1. **Clean Pipeline Architecture**
   ```
   Transport → AST → FlatGraph → Sema → Passes → Report
   ```
   - Each layer has clear responsibilities
   - No layer violations detected
   - Single-pass design is efficient

2. **Proper AST Design**
   - All types are frozen dataclasses
   - No raw_data passthrough
   - Complete extraction of YAML structure into typed fields

3. **Well-Designed Sema Layer**
   - SymbolTable provides O(1) lookups
   - ScopeTree correctly implements hierarchical visibility
   - ResolutionTable replaces mutation pattern cleanly

4. **Excellent Architecture Tests**
   - `test_architecture.py` enforces layer boundaries
   - Tests make violations physically impossible or immediately visible
   - Covers IR removal, no raw_data, no object.__setattr__

5. **Clean Type System**
   - TypeCategory enum is well-designed
   - CompatibilityState handles runtime-deferred cases
   - Canonical type mapping is correct

### ⚠️ Issues Found

#### MEDIUM Priority

1. **Stale TODO Comments (semantic_fe_pass.py:73-78)**
   ```python
   # TODO: Add when NodeIR exposes exception_port_connected / on_error_config
   # TODO: Add when NodeIR exposes on_error_return_json
   ```
   - References "NodeIR" which no longer exists
   - Should reference NodeAST or note that these require AST extension
   - **Fix:** Update comments to reflect current architecture

2. **Stale TODO Comment (portability_pass.py:33)**
   ```python
   # TODO: Add when pipeline provides space/product metadata.
   ```
   - Acceptable but should be documented as a future feature

3. **Missing Type Hints in Some Places**
   - `reference_resolution.py` uses `TYPE_CHECKING` for imports
   - Some methods could benefit from more explicit return types

#### LOW Priority

4. **Test Coverage Gaps**
   - No tests for edge cases in `canonicalize_type()`
   - No tests for `extract_item_type_from_param()` (returns None)
   - Limited tests for error recovery in transport layer

5. **Code Organization**
   - `query_authority.py` is 230+ lines - could be split into smaller modules
   - Some methods could be private (prefixed with `_`)

6. **Documentation**
   - Missing docstrings for some private methods
   - Could benefit from architecture decision records (ADRs)

## Detailed File Reviews

### pipeline.py ✅
- Clean, single-pass design
- Proper dependency injection
- No issues found

### ast/workflow_ast.py ✅
- All types frozen
- Complete extraction
- Good field naming

### ast/flat_graph.py ✅
- Clean replacement for IRBuilder
- Proper flattening logic
- Good separation of concerns

### sema/symbol_table.py ✅
- O(1) lookups via dictionaries
- Proper scope integration
- Clean build process

### sema/scope_tree.py ✅
- Correct hierarchical visibility
- Mutable-during-construction pattern is appropriate
- BFS traversal is efficient

### sema/reference_resolution.py ✅
- Clean ResolutionTable pattern
- No mutation of frozen objects
- Proper scope-aware resolution

### sema/query_authority.py ✅
- Comprehensive pass-facing API
- Clean delegation to SymbolTable
- Good separation of concerns

### passes/semantic_be/semantic_be_pass.py ✅
- Well-structured checks
- Proper use of sema queries
- Good diagnostic coverage

### tests/test_architecture.py ✅
- Excellent architectural boundary enforcement
- Makes violations physically impossible
- Good coverage of layer contracts

## Test Suite Status

```
255 passed, 0 skipped, 0 failed
```

## Recommendations

1. **Immediate (MEDIUM)**
   - Update stale TODO comments in semantic_fe_pass.py
   - Document the 3 TODOs as future features

2. **Short-term (LOW)**
   - Add tests for `canonicalize_type()` edge cases
   - Add tests for `extract_item_type_from_param()`
   - Split `query_authority.py` if it grows

3. **Long-term (LOW)**
   - Add architecture decision records (ADRs)
   - Consider adding more error recovery tests

## Conclusion

The compiler is well-architected and follows textbook design principles. The IR removal was executed cleanly, and the new pipeline is a significant improvement over the v1 rule-checker approach.

**Recommendation: APPROVE**

The code is production-ready with only minor documentation issues.
