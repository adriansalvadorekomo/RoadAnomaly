"""`mise run help`: every project command, grouped by purpose, read from mise.toml (the single source).

    mise run help            all commands, grouped by the `# ---- <section>` headers of mise.toml
    mise run help <task>     one command in full: description, arguments, dependencies and what it runs

Standard library only, so it works on a fresh clone before `mise run setup`. Colours are used on a terminal only
(set NO_COLOR to turn them off).
"""
import difflib
import os
import re
import shutil
import sys
import textwrap
from pathlib import Path

import tomllib

MISE_TOML = Path(__file__).resolve().parents[1] / "mise.toml"
SECTION = re.compile(r"^# -{10,} (?P<title>.+)$")
TASK = re.compile(r'^\[tasks\.(?:"(?P<quoted>[^"]+)"|(?P<plain>[\w-]+))\]')
ARG = re.compile(r"arg\(name='(?P<name>\w+)'(?:, default='(?P<default>[^']*)')?\)")
COMMON = [
    ("first time", "mise run setup && mise run setup:deploy"),
    ("get the models", "mise run train   (or copy models/ from a teammate)"),
    ("before a PR", "mise run check && mise run test:fast"),
    ("try the apps", "mise run api · mise run app · mise run product"),
]

LABEL_MAX = 28                         # widest command label kept on the description's line

USE_COLOUR = sys.stdout.isatty() and "NO_COLOR" not in os.environ


def style(text, code):
    return f"\033[{code}m{text}\033[0m" if USE_COLOUR else text


def bold(text):
    return style(text, "1")


def dim(text):
    return style(text, "2")


def accent(text):
    return style(text, "38;5;208")      # RoadAnomaly orange


def sections(text):
    """Task names in file order, grouped under their section header."""
    groups, current = [], None
    for line in text.splitlines():
        if m := SECTION.match(line):
            current = (m["title"], [])
            groups.append(current)
        elif (m := TASK.match(line)) and current is not None:
            current[1].append(m["quoted"] or m["plain"])
    return groups


def commands(task):
    run = task.get("run", [])
    return [run] if isinstance(run, str) else list(run)


def usage(name, task):
    """`train`, `evaluate <model> [split=val]`, ... from the {{arg(...)}} templates of the task."""
    parts = []
    for m in ARG.finditer(" ".join(commands(task))):
        parts.append(f"[{m['name']}={m['default']}]" if m["default"] is not None else f"<{m['name']}>")
    return " ".join([name, *parts])


def wrap(text, indent, width):
    """Wrap a description into the column that starts at `indent` on a terminal `width` wide."""
    lines = textwrap.wrap(text, width=max(width - indent, 40))
    return ("\n" + " " * indent).join(lines)


def plain(command):
    """The command as you would type it: {{arg(name='split', default='val')}} -> val, required args -> <name>."""
    command = command.replace("{{config_root}}", ".")
    return ARG.sub(lambda m: m["default"] if m["default"] is not None else f"<{m['name']}>",
                   command).replace("{{", "").replace("}}", "")


def overview(tasks, groups):
    width = min(shutil.get_terminal_size((110, 24)).columns, 120)
    labels = [usage(n, tasks[n]) for _, names in groups for n in names]
    column = min(max(len(label) for label in labels), LABEL_MAX) + 4    # longer labels get their own line
    header = f"{bold(accent('RoadAnomaly'))} {bold('· project commands')}"
    out = [f"{header}   {dim('run one with: mise run <task> [args]')}", ""]
    for title, names in groups:
        out.append(bold(title.upper()))
        for name in names:
            label = usage(name, tasks[name])
            text = wrap(tasks[name].get("description", ""), column + 2, width)
            if len(label) <= column - 2:
                out.append(f"  {accent(label)}{' ' * (column - len(label))}{text}")
            else:
                out.append(f"  {accent(label)}\n{' ' * (column + 2)}{text}")
        out.append("")
    out.append(bold("COMMON FLOWS"))
    out += [f"  {flow:<16}{dim(cmd)}" for flow, cmd in COMMON]
    out.append("")
    out.append(dim("Details of one command: mise run help <task>   ·   without mise, every command is a plain "
                   "shell command (mise run help <task> prints it)."))
    return "\n".join(out)


def detail(name, task):
    out = [f"{bold(accent(usage(name, task)))}", "", task.get("description", "")]
    if args := list(ARG.finditer(" ".join(commands(task)))):
        out += ["", bold("arguments")]
        out += [f"  {m['name']}" + (f"  (default: {m['default']})" if m["default"] is not None else "  (required)")
                for m in args]
    if depends := task.get("depends"):
        out += ["", bold("runs first"), "  " + ", ".join(depends)]
    if folder := task.get("dir"):
        out += ["", bold("runs in"), "  " + folder.replace("{{config_root}}", ".")]
    out += ["", bold("command" if len(commands(task)) == 1 else "commands")]
    for command in commands(task):
        out.append(textwrap.indent(plain(command).strip("\n"), "  "))
    return "\n".join(out)


def main(argv):
    text = MISE_TOML.read_text()
    tasks = tomllib.loads(text)["tasks"]
    groups = sections(text)
    listed = {n for _, names in groups for n in names}
    if missing := sorted(set(tasks) - listed):          # a task added without a section header still shows up
        groups.append(("other", missing))
    if not argv:
        print(overview(tasks, groups))
        return 0
    name = argv[0]
    if name not in tasks:
        close = difflib.get_close_matches(name, tasks, n=3, cutoff=0.6) or [t for t in tasks if name in t]
        print(f"unknown task {name!r}" + (f"; did you mean: {', '.join(close)}" if close else ""), file=sys.stderr)
        return 1
    print(detail(name, tasks[name]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
