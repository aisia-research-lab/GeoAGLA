import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from experiments.audit_ledger import audit

REPO = Path(__file__).resolve().parent.parent


def test_audit_passes_clean_ledger_and_catches_tampering():
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "calls.jsonl"
        env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(REPO / "src"), str(REPO)]))
        subprocess.run(
            [sys.executable, "-m", "experiments.matched_budget_benchmark", "--synthetic", "--mode", "calls", "--device", "cpu", "--out", str(raw)],
            cwd=str(REPO), env=env, check=True, capture_output=True,
        )
        assert audit([str(raw)], "calls")["status"] == "PASS"

        lines = raw.read_text(encoding="utf-8").splitlines()
        row = json.loads(lines[0])
        row["success"] = not row["success"]
        raw.write_text("\n".join([json.dumps(row)] + lines[1:]) + "\n", encoding="utf-8")
        try:
            audit([str(raw)], "calls")
        except AssertionError as err:
            assert "success arithmetic" in str(err)
        else:
            raise AssertionError("tampered ledger passed the audit")
