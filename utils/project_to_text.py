"""Write a text file summary of the project to project tmp directory."""
import re
from pathlib import Path

import pathspec

root = Path(__file__).parent.parent.resolve()
tmp = root / "tmp"
tmp.mkdir(exist_ok=True)
paths = [p for p in root.rglob("*") if p.is_file()]
with (root / ".gitignore").open() as f:
    patterns = [
        s for s in f.read().splitlines() if (s != "") and (not s.startswith("#"))
    ]
spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
relative_paths = [p.relative_to(root).as_posix() for p in paths]
to_ignore = set(spec.match_files(relative_paths))
result = [
    p
    for p in relative_paths
    if (p not in to_ignore) and not re.search(r"^(\.git/|data|poetry.lock)", p)
]
project_structure = "\n".join(result)
output = f"""Project name
------------
{root.name}

Project structure
-----------------
{project_structure}

Files
-----
"""

for path in result:
    with Path(root / path).open() as f:
        content = f.read()
    output += f"{path}:\n"
    output += f"{content}\n\n"

with (tmp / "project.txt").open("w") as f:
    f.write(output)
