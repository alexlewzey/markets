from pathlib import Path

dir_root = Path(__file__).parent.parent

dir_data = Path('data')
dir_data.mkdir(exist_ok=True)

dir_tmp = Path('tmp')
dir_tmp.mkdir(exist_ok=True)