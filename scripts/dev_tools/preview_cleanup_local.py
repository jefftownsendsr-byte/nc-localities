#!/usr/bin/env python3
"""Local helper for testing PR preview cleanup behavior.

This script is intended for local testing. It can:
- create a sample PR preview directory with a metadata file
- delete a local preview directory
- optionally attempt to delete the PR comment using a GitHub token

Usage examples:
  python scripts/dev_tools/preview_cleanup_local.py --pr 123 --site-dir site --create-sample
  python scripts/dev_tools/preview_cleanup_local.py --pr 123 --site-dir site --delete --dry-run
  python scripts/dev_tools/preview_cleanup_local.py --pr 123 --site-dir site --delete --token $GHTOKEN
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import requests
except Exception:
    requests = None


@dataclass
class PreviewMetadata:
    pr: int
    comment_id: Optional[int]
    preview_url: Optional[str]
    created_at: Optional[str]


def create_sample(site_dir: Path, pr: int, comment_id: int = 12345):
    pr_dir = site_dir / f"pr-{pr}"
    meta_dir = pr_dir / ".preview-metadata"
    pr_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "pr": pr,
        "comment_id": comment_id,
        "preview_url": f"https://example.github.io/test-repo/pr-{pr}/",
        "created_at": datetime.utcnow().isoformat(),
    }
    with open(meta_dir / f"pr-{pr}.json", "w", encoding="utf8") as fh:
        json.dump(meta, fh)
    # create a dummy index.html so folder has content
    with open(pr_dir / "index.html", "w", encoding="utf8") as fh:
        fh.write(f"<html><body>PR {pr} preview</body></html>")
    print(f"Created sample preview at {pr_dir}")


def load_metadata(site_dir: Path, pr: int) -> Optional[PreviewMetadata]:
    md = site_dir / f"pr-{pr}" / ".preview-metadata" / f"pr-{pr}.json"
    if not md.exists():
        print(f"No metadata file found at {md}")
        return None
    with open(md, "r", encoding="utf8") as fh:
        j = json.load(fh)
    return PreviewMetadata(pr=j.get("pr"), comment_id=j.get("comment_id"), preview_url=j.get("preview_url"), created_at=j.get("created_at"))


def delete_preview_dir(site_dir: Path, pr: int, dry_run: bool = True):
    pr_dir = site_dir / f"pr-{pr}"
    if not pr_dir.exists():
        print(f"PR directory {pr_dir} not found; nothing to do.")
        return False
    if dry_run:
        print(f"DRY RUN: would remove {pr_dir}")
        return True
    shutil.rmtree(pr_dir)
    print(f"Removed {pr_dir}")
    return True


def delete_comment_by_id(owner: str, repo: str, comment_id: int, token: str, dry_run: bool = True):
    if requests is None:
        print("requests not available; cannot perform remote deletion")
        return False
    if dry_run:
        print(f"DRY RUN: would DELETE comment ID {comment_id}")
        return True
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{comment_id}"
    resp = requests.delete(url, headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json"})
    if resp.status_code == 204:
        print(f"Deleted comment {comment_id}")
        return True
    else:
        print(f"Failed to delete comment {comment_id}: {resp.status_code} {resp.text}")
        return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pr", type=int, required=True, help="PR number")
    p.add_argument("--site-dir", default="site", help="Site output dir (root) to operate on")
    p.add_argument("--create-sample", action="store_true", help="Create sample pr-<pr> directory with metadata")
    p.add_argument("--delete", action="store_true", help="Delete the pr-<pr> directory")
    p.add_argument("--dry-run", action="store_true", help="Don't actually delete, just print actions")
    p.add_argument("--owner", help="GitHub owner (for comment deletion)")
    p.add_argument("--repo", help="GitHub repo (for comment deletion)")
    p.add_argument("--token", help="GitHub token for comment deletion")
    args = p.parse_args()

    site_dir = Path(args.site_dir)

    if args.create_sample:
        create_sample(site_dir, args.pr)
        return 0

    meta = load_metadata(site_dir, args.pr)
    if meta:
        print("Metadata:", meta)
    else:
        print("No metadata: nothing to delete (maybe fallback to marker-based logic?)")

    if args.delete:
        deleted = delete_preview_dir(site_dir, args.pr, dry_run=args.dry_run)
        if meta and meta.comment_id and args.token and args.owner and args.repo:
            delete_comment_by_id(args.owner, args.repo, meta.comment_id, args.token, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
