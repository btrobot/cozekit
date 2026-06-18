"""Backward compatibility shim — use cozekit.api instead."""
from .api import compile_text, compile_path, compile_source, _get_pipeline

# Legacy alias
_default = None
def _default_pipeline():
    return _get_pipeline()

def main() -> None:
    from .cli import main as cli_main
    cli_main()
