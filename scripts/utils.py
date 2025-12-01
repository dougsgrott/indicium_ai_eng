import os
import sys


def set_path_to_imports():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    src_path = os.path.join(project_root, 'src')

    if src_path not in sys.path:
        sys.path.append(src_path)
    if project_root not in sys.path:
        sys.path.append(project_root)
    return project_root