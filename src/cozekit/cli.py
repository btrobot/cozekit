"""cozekit — Coze Workflow Static Validator.

Command-line interface for validating Coze workflow YAML/JSON files.

Usage:
    cozekit check <file>                  Validate a single file
    cozekit check <dir>                   Validate all .yaml/.json files in directory
    cozekit check <file> --format json    Output diagnostics as JSON
    cozekit check <file> --quiet          Only output if violations found
    cozekit info                          Show compiler version and capabilities
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

from .api import compile_path, compile_text
from .diagnostics.core import DiagnosticKind
from .diagnostics.report import CompilerV2Report

# ── Version ──────────────────────────────────────────────────────

__version__ = "0.1.0"

# ── ANSI colors ──────────────────────────────────────────────────

_NO_COLOR = not sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if _NO_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def red(t: str) -> str: return _c("31", t)
def green(t: str) -> str: return _c("32", t)
def yellow(t: str) -> str: return _c("33", t)
def cyan(t: str) -> str: return _c("36", t)
def dim(t: str) -> str: return _c("2", t)
def bold(t: str) -> str: return _c("1", t)


# ── Exit codes ───────────────────────────────────────────────────

EXIT_CLEAN = 0
EXIT_VIOLATIONS = 1
EXIT_ERROR = 2

# ── Supported extensions ─────────────────────────────────────────

_EXTENSIONS = {".yaml", ".yml", ".json", ".flow"}


# ── Output formatters ────────────────────────────────────────────

def _format_text(report: CompilerV2Report, path: Path, *, show_ok: bool = True) -> str:
    """Human-readable single-line output."""
    s = report.summary
    fname = str(path)

    if s.total == 0:
        if show_ok:
            return f"  {green('✓')} {fname}"
        return ""

    lines = []
    icon = red("✗") if s.violations > 0 else yellow("⚠")
    lines.append(f"  {icon} {fname}  {dim(f'({s.total} diagnostics)')}")

    for d in report.diagnostics:
        loc = ""
        if d.source_span and d.source_span.start_line is not None:
            loc = dim(f" :{d.source_span.start_line + 1}")
        kind_icon = red("●") if d.kind == DiagnosticKind.VIOLATION else yellow("○")
        lines.append(f"    {kind_icon} {d.rule_id}{loc}  {d.message}")

    return "\n".join(lines)


def _format_compact(report: CompilerV2Report, path: Path) -> str:
    """Machine-readable: one line per file."""
    s = report.summary
    rules = Counter(d.rule_id for d in report.diagnostics)
    rules_str = ",".join(f"{k}:{v}" for k, v in rules.most_common()) if rules else "clean"
    status = "FAIL" if s.violations > 0 else ("WARN" if s.warnings > 0 else "OK")
    return f"{status}\t{path}\t{s.total}\t{rules_str}"


def _format_json_single(report: CompilerV2Report, path: Path) -> dict:
    """JSON output for a single file."""
    d = report.to_dict()
    d["file"] = str(path)
    return d


# ── Batch result ─────────────────────────────────────────────────

def _print_batch_summary(
    results: list[tuple[Path, CompilerV2Report]],
    elapsed: float,
) -> str:
    """Print summary after batch processing."""
    total_files = len(results)
    clean = sum(1 for _, r in results if r.exit_code == 0)
    failed = total_files - clean
    total_diags = sum(len(r.diagnostics) for _, r in results)
    total_violations = sum(r.summary.violations for _, r in results)

    # Rule breakdown
    all_rules: Counter = Counter()
    for _, r in results:
        for d in r.diagnostics:
            all_rules[d.rule_id] += 1

    lines = []
    lines.append("")
    lines.append(bold("── Summary ──────────────────────────────────────"))
    lines.append(f"  Files:       {total_files} total, {green(str(clean))} clean, {red(str(failed))} failed")
    lines.append(f"  Diagnostics: {total_diags} total, {red(str(total_violations))} violations")
    lines.append(f"  Time:        {elapsed:.2f}s")

    if all_rules:
        lines.append("")
        lines.append(bold("  Rule breakdown:"))
        for rule, count in all_rules.most_common():
            lines.append(f"    {rule:30s} {count}")

    return "\n".join(lines)


# ── Commands ─────────────────────────────────────────────────────

def cmd_check(args: argparse.Namespace) -> int:
    """Validate one or more workflow files."""
    target = Path(args.target)
    fmt = args.format
    quiet = args.quiet
    show_ok = not quiet

    # Collect files
    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(
            f for f in target.rglob("*")
            if f.suffix.lower() in _EXTENSIONS
            and not f.name.startswith(".")
        )
        if not files:
            print(f"Error: no workflow files found in {target}", file=sys.stderr)
            return EXIT_ERROR
    else:
        print(f"Error: {target} not found", file=sys.stderr)
        return EXIT_ERROR

    # Batch mode
    if len(files) > 1:
        return _check_batch(files, fmt, show_ok)

    # Single file mode
    return _check_single(files[0], fmt, show_ok)


def _check_single(path: Path, fmt: str, show_ok: bool) -> int:
    """Validate a single file."""
    try:
        report = compile_path(path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_ERROR

    if fmt == "json":
        print(json.dumps(_format_json_single(report, path), ensure_ascii=False, indent=2))
    elif fmt == "compact":
        print(_format_compact(report, path))
    else:
        line = _format_text(report, path, show_ok=show_ok)
        if line:
            print(line)

    return EXIT_VIOLATIONS if report.exit_code != 0 else EXIT_CLEAN


def _check_batch(files: list[Path], fmt: str, show_ok: bool) -> int:
    """Validate multiple files."""
    results: list[tuple[Path, CompilerV2Report]] = []
    has_violations = False
    json_results = []

    t0 = time.monotonic()

    for f in files:
        try:
            report = compile_path(f)
        except Exception as e:
            print(f"  {red('✗')} {f}  {red(str(e))}", file=sys.stderr)
            has_violations = True
            continue

        results.append((f, report))

        if report.exit_code != 0:
            has_violations = True

        if fmt == "json":
            json_results.append(_format_json_single(report, f))
        elif fmt == "compact":
            print(_format_compact(report, f))
        else:
            line = _format_text(report, f, show_ok=show_ok)
            if line:
                print(line)

    elapsed = time.monotonic() - t0

    if fmt == "json":
        summary_data = {
            "files": len(results),
            "clean": sum(1 for _, r in results if r.exit_code == 0),
            "violations": sum(r.summary.violations for _, r in results),
            "elapsed_seconds": round(elapsed, 2),
            "results": json_results,
        }
        print(json.dumps(summary_data, ensure_ascii=False, indent=2))
    elif fmt == "text":
        print(_print_batch_summary(results, elapsed))

    return EXIT_VIOLATIONS if has_violations else EXIT_CLEAN


def cmd_info(args: argparse.Namespace) -> int:
    """Show compiler info."""
    print(bold(f"cozekit v{__version__}"))
    print()
    print("  Coze Workflow Static Validator")
    print("  Textbook compiler architecture: transport → AST → semantic → passes")
    print()
    print(bold("  Supported formats:"))
    print("    .yaml / .yml   Coze workflow source format")
    print("    .json          Coze workflow export format")
    print("    .flow          Coze workflow flow format")
    print()
    print(bold("  Validation layers:"))
    print("    Layer 1  Syntax       Structural correctness (nodes, edges, required fields)")
    print("    Layer 2  Semantic     Field-level validation (types, ranges, references)")
    print("    Layer 3  Graph        Connectivity, cycles, isolated nodes")
    print("    Layer 4  Portability  Cross-format portability checks")
    print()
    print(bold("  Exit codes:"))
    print(f"    {green('0')}  Clean — no violations")
    print(f"    {red('1')}  Violations found")
    print(f"    {red('2')}  Compiler error")
    print()
    print(bold("  Examples:"))
    print("    cozekit check workflow.yaml")
    print("    cozekit check ./workflows/ --format json")
    print("    cozekit check workflow.yaml --format compact")
    print("    cozekit check workflow.yaml --quiet")
    return EXIT_CLEAN


# ── Main ─────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cozekit",
        description="Coze Workflow Static Validator — validate workflow files without a runtime",
    )
    parser.add_argument("--version", action="version", version=f"cozekit {__version__}")

    sub = parser.add_subparsers(dest="command", help="command")

    # check
    p_check = sub.add_parser(
        "check",
        help="Validate workflow file(s)",
        description="Validate one or more Coze workflow files for syntax, semantic, and graph errors.",
    )
    p_check.add_argument("target", help="Workflow file or directory to validate")
    p_check.add_argument(
        "--format", "-f",
        choices=["text", "json", "compact"],
        default="text",
        help="Output format (default: text)",
    )
    p_check.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output files with violations (text mode)",
    )

    # info
    sub.add_parser("info", help="Show compiler version and capabilities")

    return parser


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "check":
        code = cmd_check(args)
    elif args.command == "info":
        code = cmd_info(args)
    else:
        parser.print_help()
        code = EXIT_CLEAN

    sys.exit(code)
