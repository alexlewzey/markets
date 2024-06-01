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
