# Publish Steps (Beginner-friendly)

This guide shows the minimal steps to publish the project to GitHub and automatically build & deploy the site.

1) Install prerequisites (if you plan to automate everything):
   - Docker: https://docs.docker.com/get-docker
   - Git for Windows: https://git-scm.com/download/win
   - GitHub CLI (optional, for automatic publishing): https://cli.github.com/

2) Use GitHub Desktop (if you prefer GUI) to publish the repo:
   - Open GitHub Desktop → File → Add Local Repository → choose `C:\Users\Registered User\nc-localities` → Add
   - Commit and then press **Publish Repository** and choose a name (ex: `nc-localities`) and visibility public/private

3) Or use the automated script (prefer `gh` CLI or Docker):
   - Open PowerShell and run:
     ```powershell
     cd 'C:\Users\Registered User\nc-localities'
     .\scripts\auto_setup_and_publish.ps1 -RepoName nc-localities
     ```
   - The script will: bootstrap if needed, run the pipeline (Docker preferred), copy outputs into `site/data`, commit, push to GitHub, and attempt to enable Pages via `gh`.

4) Check GitHub Actions: Open your repo → **Actions** tab → view `update_nc_localities` or `deploy_pages` workflow runs. Wait until the run completes with green check.

5) View your site: Open `Settings` → Pages to find the site URL, e.g., `https://<username>.github.io/nc-localities/`.

Notes:
- If `gh` is not installed, the script opens GitHub Desktop for the final publish step.
- If you prefer not to use Docker (or it’s not available), the script runs locally and uses `conda` or `venv` to install Python dependencies.
- For any errors, re-run `.\scripts\prepublish_check.ps1` to diagnose missing dependencies.
