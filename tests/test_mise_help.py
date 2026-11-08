"""`mise run help` (scripts/mise_help.py): it lists every task of mise.toml and prints runnable commands."""
import importlib.util

import tomllib

from roadanomaly import data_pipeline as dp

SPEC = importlib.util.spec_from_file_location("mise_help", dp.REPO_ROOT / "scripts" / "mise_help.py")
mise_help = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mise_help)
TEXT = mise_help.MISE_TOML.read_text()
TASKS = tomllib.loads(TEXT)["tasks"]


def test_every_task_sits_in_exactly_one_section():
    listed = [name for _, names in mise_help.sections(TEXT) for name in names]
    assert sorted(listed) == sorted(TASKS)
    assert len(listed) == len(set(listed))


def test_usage_shows_required_and_default_arguments():
    assert mise_help.usage("evaluate", TASKS["evaluate"]) == "evaluate <model> [split=val]"
    assert mise_help.usage("train", TASKS["train"]) == "train"


def test_printed_commands_are_plain_shell():
    command = mise_help.plain(TASKS["evaluate"]["run"])
    assert command == "python scripts/evaluate.py --model <model> --split val"
    assert "{{" not in mise_help.plain(" ".join(mise_help.commands(TASKS["landing:deploy"])))


def test_overview_and_details(capsys):
    assert mise_help.main([]) == 0
    overview = capsys.readouterr().out
    assert all(name in overview for name in TASKS)
    assert mise_help.main(["product"]) == 0
    assert "streamlit run app.py" in capsys.readouterr().out
    assert mise_help.main(["trainx"]) == 1
    assert "did you mean: train" in capsys.readouterr().err
