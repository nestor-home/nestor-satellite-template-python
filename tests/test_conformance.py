"""The satellite against the Nestor server's black-box conformance suite.

The published server's `nestor satellites conformance`, run through uvx at the version in
`.nestor-version`, launches `my-satellite run` once per scenario, without a sound card: pairing
with a device code and an enrollment code, refused codes, rate limits, identify, acks, text, audio
both ways and reconnection. Raise `.nestor-version` to check against a newer server.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SERVER = f"nestor-home[voice]=={(ROOT / '.nestor-version').read_text().strip()}"
SATELLITE = [sys.executable, "-m", "my_satellite", "run", "--core", "{url}", "--room", "salon"]
SATELLITE += ["--token-file", "{state}/token.json", "--null-audio"]


@pytest.mark.conformance
def test_the_satellite_passes_the_servers_conformance_suite() -> None:
    suite = ["uvx", "--from", SERVER, "nestor", "satellites", "conformance", "--deadline", "20", "--"]
    run = subprocess.run(
        [*suite, *SATELLITE], capture_output=True, text=True, env={**os.environ, "LC_ALL": "en_US.UTF-8"}
    )
    report = run.stdout + run.stderr

    assert run.returncode == 0, report
    assert not [line for line in report.splitlines() if line.startswith("FAIL")], report
    for check in [
        "PASS  receives the core's audio (A1, A2)",
        "PASS  sends its microphone audio (A1, A2)",
        "PASS  acknowledges intent.text within 1 s",
        "PASS  reconnects with the same token after the core closes its link (L5)",
        "PASS  pairs with the enrollment code of NESTOR_PAIRING_URI, no code typed (P3, P4)",
        "PASS  presents a refused enrollment code (used) only once (P5)",
        "PASS  keeps polling after a pending identify (I1)",
        "PASS  acknowledges intent.identify within 1 s",
    ]:
        assert check in report.splitlines(), f"{check}: not run\n{report}"
