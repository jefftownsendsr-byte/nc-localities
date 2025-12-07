import json
from pathlib import Path
from scripts.dev_tools.preview_cleanup_local import create_sample, load_metadata, delete_preview_dir


def test_create_and_delete(tmp_path: Path):
    site_dir = tmp_path / "site"
    site_dir.mkdir()
    create_sample(site_dir, 123, comment_id=2345)

    # metadata should load
    meta = load_metadata(site_dir, 123)
    assert meta is not None
    assert meta.pr == 123
    assert meta.comment_id == 2345

    # delete should succeed in dry-run mode
    assert delete_preview_dir(site_dir, 123, dry_run=True)
    # after actual delete, the folder should be gone
    assert delete_preview_dir(site_dir, 123, dry_run=False)
    assert not (site_dir / "pr-123").exists()
