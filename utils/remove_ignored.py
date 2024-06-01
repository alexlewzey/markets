import shutil
from pathlib import Path

import pathspec
from tqdm.auto import tqdm


def to_relative(root: Path, p: Path) -> str:
    posix = p.relative_to(root).as_posix()
    if p.is_dir():
        posix += "/"
    return posix


root = Path(__file__).parent.parent.resolve()
with (root / ".gitignore").open() as f:
    patterns = [
        s for s in f.read().splitlines() if (s != "") and (not s.startswith("#"))
    ]
spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)


paths = [to_relative(root, p) for p in root.rglob("*")]
to_ignore = [root / Path(p) for p in spec.match_files(paths)]
for path in tqdm(to_ignore):
    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    except Exception:  # noqa
        pass
