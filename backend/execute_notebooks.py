from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]


def main():
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        client = NotebookClient(notebook, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}})
        client.km = client.create_kernel_manager()
        client.km.kernel_spec.argv[0] = sys.executable
        client.execute()
        nbformat.write(notebook, path)
        print(f"Executed {path.name}: {len(notebook.cells)} cells", flush=True)


if __name__ == "__main__":
    main()