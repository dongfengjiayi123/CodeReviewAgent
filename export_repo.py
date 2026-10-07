"""Export only reviewed project files, without local credentials or Git history."""

import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from dotenv import dotenv_values

PROJECT = Path(__file__).resolve().parent
FILES = (
    "README.md", "NOTICE.md", "LICENSE.txt", ".gitignore", ".env.example",
    "review.py", "export_repo.py", "main.ipynb", "requirements.txt",
    "requirements-notebook.txt", "tests/test_review.py",
    ".github/workflows/ci.yml", "data/sample_code.py",
    "examples/static_report.md", "outputs/.gitkeep",
)


def export():
    secrets = [value for key, value in dotenv_values(PROJECT / ".env").items()
               if value and len(value) >= 12 and ("KEY" in key or "TOKEN" in key)
               and not value.startswith("your_")]
    entries = {}
    for name in FILES:
        content = (PROJECT / name).read_text(encoding="utf-8")
        if name == "main.ipynb":
            notebook = json.loads(content)
            for cell in notebook["cells"]:
                if cell["cell_type"] == "code":
                    cell["outputs"] = []
                    cell["execution_count"] = None
            content = json.dumps(notebook, ensure_ascii=False, indent=1) + "\n"
        if any(secret in content for secret in secrets):
            raise ValueError(f"Export stopped: local credential found in {name}")
        if re.search(r"\b(?:sk-|ms-)[A-Za-z0-9_-]{20,}", content):
            raise ValueError(f"Export stopped: possible credential found in {name}")
        entries[name] = content
    target = PROJECT / "dist/CodeReviewAgent.zip"
    target.parent.mkdir(exist_ok=True)
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr("CodeReviewAgent/" + name, content)
    print(f"Exported {len(entries)} files: {target}")
    return target


if __name__ == "__main__":
    export()
