#!/usr/bin/env python3
"""Safely extract a pinned GitHub source archive into its workload directory."""

import argparse
import tarfile
import tempfile
from pathlib import Path


def safe_member(member: tarfile.TarInfo, destination: str) -> tarfile.TarInfo | None:
    member = tarfile.data_filter(member, destination)
    if member is None:
        return None
    if member.isdir():
        mode = 0o755
    elif member.isfile():
        mode = 0o755 if member.mode & 0o111 else 0o644
    else:
        mode = None
    return member.replace(uid=None, gid=None, uname=None, gname=None,
                          mtime=None, mode=mode)


def extract(archive: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{target.name}-extract-",
                                     dir=target.parent) as temporary:
        temporary_path = Path(temporary)
        with tarfile.open(archive, "r:gz") as source:
            roots = {member.name.split("/", 1)[0] for member in source
                     if member.name and member.name != "."}
            if len(roots) != 1:
                raise ValueError(f"Expected one top-level directory in {archive}")
            root_name = roots.pop()
            source.extractall(temporary_path, filter=safe_member)
        extracted = temporary_path / root_name
        if not extracted.is_dir():
            raise ValueError(f"Missing source directory in {archive}")
        (extracted / ".benchmark-extracted").write_text(f"{archive.name}\n")
        if target.exists():
            target.rmdir()
        extracted.rename(target)
    print(f"압축 해제: {archive} → {target}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("target", type=Path)
    arguments = parser.parse_args()
    extract(arguments.archive, arguments.target)
