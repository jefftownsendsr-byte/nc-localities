Manual deletion
- If you want to manually remove a specific PR preview, use the **Manual PR Preview Cleanup** workflow accessible in `Actions` and run it with the `pr_number` input (e.g., 123), setting `dry_run=false` to perform the deletion instead of a dry run.

# Developer Setup & Quick Guide

This project provides a small pipeline and site generator. These steps get you up and running quickly for development.

Prerequisites (recommended):

- Git (for pre-commit and version control)
- Python 3.11+ (if using venv/pip)
- Conda/Mamba (optional, recommended for full builds with geospatial packages)
- Docker (optional, for reproducible containerized builds)

Quick dev setup (recommended for beginners):

1. Create a virtual environment:

```powershell
python -m venv .\venv
. .\venv\Scripts\Activate
```
2. Install dev dependencies & pre-commit *and* hooks:

```powershell
# Install packages listed in requirements-dev.txt
python -m pip install -r requirements-dev.txt
# Hooks are installed by setup_dev.ps1
.\scripts\setup_dev.ps1
# Run ruff and black locally (optional):
ruff check .
black --check .
```

3. Run the fast demo (sample-mode, minimal dependencies):

```powershell
.\scripts\dev.ps1 -UseSample
# Serve the site and visit http://localhost:8000
```

On macOS/Linux, use the helper shell script:

```bash
./scripts/setup_dev.sh --full   # or without --full for venv dev only
```

Full build (requires conda for geopackages on Windows):

```powershell
conda env create -n nc-localities -f environment.yml
conda activate nc-localities
python .\scripts\build_nc_localities.py --output-dir .\output --year 2025 --non-interactive --pack-output
python .\scripts\build_site.py --output-dir .\output --site-dir .\site
```

Docker-based full run (recommended on Windows if you don't want to manage conda install):

```powershell
.\scripts\run_in_docker.ps1
```

Running tests:

```powershell
# (venv)
python -m pip install -r requirements-dev.txt
pytest -q
```

Pre-commit:

- `setup_dev.ps1` installs the hooks if this repo is a git repo and runs `pre-commit run --all-files` once.
- Fix issues shown by pre-commit and commit changes; hooks will prevent bad commits.

Windows note:
- If you're on Windows, installing geospatial dependencies via pip often fails because of GDAL/Fiona binary build requirements.
- For best results, install `conda`/`mamba` and run: `conda env create -n nc-localities -f environment.yml` to get a working environment.
- The helper `scripts/setup_dev.ps1 -Full` will prefer `mamba` if available and create/update the `nc-localities` environment.
 - Use `scripts/check_env.ps1` to validate your environment and see a short set of recommended commands.

Notes:
- Use `--use-sample` when iterating quickly.
- Use `conda` or Docker for reproducible builds when verifying full pipeline correctness.

## PR previews and cleanup

CI will deploy a preview of the generated site for every PR to `gh-pages/pr-<PR_NUMBER>` and will post a PR comment titled `NC Localities PR preview` with the preview URL. This is handled by `.github/workflows/pr_local_ci.yml` and provides quick live previews for reviewers.

Automatic cleanup:
- When a PR is closed (merged or closed), the `pr_preview_cleanup.yml` workflow removes the `pr-<PR_NUMBER>` directory from `gh-pages` and deletes the PR preview comment so links don't go stale.
- A scheduled workflow `pr_preview_age_cleanup.yml` runs daily and removes `pr-*` directories older than 7 days to keep `gh-pages` tidy. You can change the `STALE_DAYS` threshold in the workflow or set `DRY_RUN: 'true'` during testing.

How to disable or tweak behavior:
- To turn off automatic cleanup, remove or disable the file `.github/workflows/pr_preview_cleanup.yml`.
- To change the retention period for stale previews, edit `.github/workflows/pr_preview_age_cleanup.yml` and modify `STALE_DAYS`.
- To change how preview comments are shown or delete them manually, edit `.github/workflows/pr_local_ci.yml` where the comment is posted (it uses `peter-evans/create-or-update-comment` to keep a single comment per PR).

Using a deploy token for protected `gh-pages` branches
- If your repository protects `gh-pages` (or you want to use a dedicated token), create a personal access token with `repo` scope and add it as a repository secret called `DEPLOY_GH_PAGES_TOKEN`.
- To create a PAT for GH Pages deployment (recommended when `gh-pages` is protected):
	1. Go to https://github.com/settings/tokens (Personal access tokens), click "Generate new token".
	2. Set a note like "nc-localities gh-pages deploy".
	3. Select `repo` scope (full control of private repositories) and optionally `workflow` if needed.
	4. Generate token and copy it (you won’t see it again).
	5. In your repository: `Settings` → `Secrets` → `Actions` → `New repository secret` and create a secret `DEPLOY_GH_PAGES_TOKEN` with the PAT value.
- The workflows will automatically try to use `DEPLOY_GH_PAGES_TOKEN` if present; otherwise they fall back to the default `GITHUB_TOKEN`.
- You can create a token and add it in `Settings` > `Secrets and variables` > `Actions` > `New repository secret`.

PR comment metadata and cleanup
- The PR preview job stores metadata in `site/.preview-metadata/pr-<PR>.json` inside the deployed preview directory on `gh-pages` so cleanups can find and delete a specific comment by ID. The cleanup workflows prefer the stored `comment_id` for robust deletion, and fall back to the HTML marker if metadata is missing.

Retention check
- A scheduled workflow `pr_preview_retention_check.yml` runs daily to check the number of `pr-*` directories on `gh-pages`. If the number exceeds the configured threshold (default 100), it will open or update an issue on the repo so maintainers can take action.

Manual testing and dry-run:
- You can manually trigger the scheduled cleanup by using `Actions` > `PR Preview Age Cleanup` > Run workflow and set `dry_run=true` to test without committing changes.

Security note:
- These workflows use the built-in `GITHUB_TOKEN`. Ensure branch protections allow the token to push to `gh-pages` (or configure a deployment token in repository secrets if needed).

Example comment & removal templates
- Preview comment body: `✅ PR preview: https://<owner>.github.io/<repo>/pr-<number>/`
- Cleanup removal comment body (updated upon PR close): `⚠️ PR preview removed: https://<owner>.github.io/<repo>/pr-<number>/ is no longer available.`
- Comment title: `NC Localities PR preview` (used by the workflow to avoid duplicate preview comments in a single PR)
