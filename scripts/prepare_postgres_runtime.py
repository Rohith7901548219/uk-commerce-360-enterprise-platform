"""Extract only PostgreSQL server files, omitting pgAdmin/StackBuilder installers."""

from pathlib import Path
from zipfile import ZipFile

if __name__ == "__main__":
    root = Path(".tools/postgres-runtime").resolve()
    root.mkdir(parents=True, exist_ok=True)
    with ZipFile(".tools/postgresql.zip") as archive:
        for entry in archive.infolist():
            if not entry.filename.startswith(("pgsql/bin/", "pgsql/lib/", "pgsql/share/")):
                continue
            destination = (root / entry.filename).resolve()
            if not destination.is_relative_to(root):
                raise ValueError("Unsafe archive path")
            archive.extract(entry, root)
    print("Workspace PostgreSQL runtime extracted (bin/lib/share only)")
