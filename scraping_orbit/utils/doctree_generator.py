from pathlib import Path

import seedir as sd


def create_doctree():
    """
    Creates a visual doctree

    :return:
    """
    sd.seedir(str(Path(__file__).resolve().parent.parent), style='emoji',
              exclude_folders=['.git', 'venv', '__pycache__', '.gitignore', 'downloads',
                               '.idea', '.wdm', '.egg'],
              exclude_files=['.xml', '.xlsx', '.xls', '.sh', '.bat', '.gitignore', 'log', '__init__.py'])
