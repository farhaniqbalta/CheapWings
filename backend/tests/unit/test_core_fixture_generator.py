"""The fixture generator's money answers must come from pure Python, never the Rust core.

money.py delegates to Rust since P5.1, so a generator that imported it would gate Rust
against itself. The generator carries its own Decimal reference instead.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_generator_money_reference_runs_without_rust_core():
    code = (
        "import sys; sys.modules['cheapwings_core'] = None\n"
        f"sys.path.insert(0, {str(ROOT / 'scripts')!r})\n"
        "import gen_core_fixtures as g\n"
        "assert g.reference_fx_convert('0.125', '1', 'USD') == '0.12'\n"
        "assert g.reference_fx_convert('-0.004', '1', 'USD') == '-0.00'\n"
        "assert g.reference_from_minor_units(100, 'USD') == '1.00'\n"
        "assert g.reference_as_minor_units('1.50', 'USD') == 150\n"
        "assert len(g.money_cases(3)) == 3 * 3 + 6\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
