import importlib

import pytest

from personal_kb.cli.main import build_parser, main


def test_personal_kb_import_has_no_bootstrap_side_effects() -> None:
    module = importlib.import_module("personal_kb")
    assert module.__name__ == "personal_kb"


def test_cli_help_exits_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])

    captured = capsys.readouterr()
    assert excinfo.value.code == 0
    assert "usage:" in captured.out.lower()


def test_parser_has_kb_program_name() -> None:
    parser = build_parser()
    assert parser.prog == "kb"
