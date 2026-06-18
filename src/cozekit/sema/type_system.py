"""Type system — type categories, compatibility checking, and inference.

Provides type facts for parameters based on declared types and ref analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TypeCategory(StrEnum):
    SCALAR = 'scalar'
    OBJECT = 'object'
    LIST = 'list'
    ENUM_LIKE = 'enum-like'
    UNKNOWN = 'unknown'
    RUNTIME_DEFERRED = 'runtime-deferred'


class CompatibilityState(StrEnum):
    COMPATIBLE = 'compatible'
    INCOMPATIBLE = 'incompatible'
    UNKNOWN = 'unknown'
    RUNTIME_DEFERRED = 'runtime-deferred'


# Canonical type mapping
_TYPE_CANONICAL: dict[str, str] = {
    'string': 'string', 'str': 'string',
    'integer': 'integer', 'int': 'integer',
    'float': 'float', 'number': 'float',
    'boolean': 'boolean', 'bool': 'boolean',
    'object': 'object', 'map': 'object',
    'list': 'list', 'array': 'list',
}


@dataclass(frozen=True)
class TypeFact:
    """Type inference result for a parameter or value."""
    category: TypeCategory
    canonical_type: str | None = None
    item_type: str | None = None
    declared_type: str | None = None


def canonicalize_type(raw_type: str | None) -> str | None:
    """Normalize a raw type string to canonical form."""
    if raw_type is None:
        return None
    return _TYPE_CANONICAL.get(raw_type.lower().strip(), raw_type.lower().strip())


def infer_type(declared_type: str | None, *, ref_source: str | None = None) -> TypeFact:
    """Infer type fact from declared type and optional ref source."""
    if ref_source and ref_source.startswith('global_variable'):
        return TypeFact(category=TypeCategory.RUNTIME_DEFERRED, declared_type=declared_type)
    canonical = canonicalize_type(declared_type)
    if canonical is None:
        return TypeFact(category=TypeCategory.UNKNOWN)
    if canonical in ('string', 'integer', 'float', 'boolean'):
        return TypeFact(category=TypeCategory.SCALAR, canonical_type=canonical, declared_type=declared_type)
    if canonical == 'object':
        return TypeFact(category=TypeCategory.OBJECT, canonical_type=canonical, declared_type=declared_type)
    if canonical == 'list':
        return TypeFact(category=TypeCategory.LIST, canonical_type=canonical, declared_type=declared_type)
    return TypeFact(category=TypeCategory.UNKNOWN, declared_type=declared_type)


def check_compatibility(source_type: TypeFact, target_type: TypeFact) -> CompatibilityState:
    """Check if source type is compatible with target type.

    Uses exact type matching for deterministic offline checks.
    Scalar coercion (e.g. int->float) is NOT automatic — only identical
    canonical types are COMPATIBLE.
    """
    if source_type.category == TypeCategory.UNKNOWN or target_type.category == TypeCategory.UNKNOWN:
        return CompatibilityState.UNKNOWN
    if source_type.category == TypeCategory.RUNTIME_DEFERRED or target_type.category == TypeCategory.RUNTIME_DEFERRED:
        return CompatibilityState.RUNTIME_DEFERRED
    if source_type.canonical_type == target_type.canonical_type:
        return CompatibilityState.COMPATIBLE
    return CompatibilityState.INCOMPATIBLE


# ── P3: Parameter-level type facts ─────────────────────────


@dataclass(frozen=True)
class ParameterTypeFact:
    """Type inference result for a specific parameter with ref analysis."""
    parameter_name: str | None
    declared_type: str | None          # canonicalized declared type (from left.type)
    declared_item_type: str | None     # for lists: item type
    ref_target_type: str | None = None # resolved ref target's declared type
    compatibility: CompatibilityState = CompatibilityState.UNKNOWN


def extract_declared_type_from_param(param) -> str | None:
    """Extract declared type from a ParameterAST.

    Returns the canonicalized left_type, or None if not a scalar/compound type.
    Filters out meta-types like 'ref', 'object_ref', 'literal'.
    """
    if param.left_type:
        vt = param.left_type
        if vt not in ('ref', 'object_ref', 'literal'):
            return canonicalize_type(vt)
    return None


def extract_item_type_from_param(param) -> str | None:
    """Extract list item type from a ParameterAST's left.schema.type."""
    # Item type is not yet exposed as a dedicated AST field.
    return None


def resolve_ref_type(ref, *, symbol_table) -> str | None:
    """Resolve a RefAST to the target parameter's declared type.

    Resolution chain:
    1. ref.block_id -> symbol_table O(1) lookup -> target NodeSymbol
    2. Target node's parameters -> match ref.name or ref.path[0]
    3. Extract declared type from matched parameter
    4. Return canonicalized type or None
    """
    block_id = ref.block_id
    if not block_id:
        return None

    target_node_sym = symbol_table.lookup_node_by_id(block_id)
    if target_node_sym is None:
        return None

    # Match ref name to target parameter
    ref_name = None
    if ref.path:
        ref_name = ref.path[0]
    if ref_name is None and ref.name:
        ref_name = ref.name

    target_node = target_node_sym.node
    for param in target_node.parameters:
        if param.name == ref_name:
            declared = extract_declared_type_from_param(param)
            if declared:
                return declared

    return None


def build_parameter_type_facts(param, *, symbol_table) -> ParameterTypeFact:
    """Build a ParameterTypeFact for a single parameter."""
    declared = extract_declared_type_from_param(param)
    item_type = extract_item_type_from_param(param)
    ref_target_type = None
    compat = CompatibilityState.UNKNOWN

    if param.input_ref is not None:
        # Check if ref target is a global variable
        ref_source = param.input_ref.source
        if ref_source and isinstance(ref_source, str) and ref_source.startswith('global_variable'):
            compat = CompatibilityState.RUNTIME_DEFERRED
        else:
            ref_target_type = resolve_ref_type(param.input_ref, symbol_table=symbol_table)
            if declared and ref_target_type:
                source_fact = infer_type(declared)
                target_fact = infer_type(ref_target_type)
                compat = check_compatibility(source_fact, target_fact)

    return ParameterTypeFact(
        parameter_name=param.name,
        declared_type=declared,
        declared_item_type=item_type,
        ref_target_type=ref_target_type,
        compatibility=compat,
    )
