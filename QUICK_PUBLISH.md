# One-Click Setup & Publish (Minimal Interaction)

If you want everything done with minimal interaction — bootstrap files, run the pipeline, and publish to GitHub — follow these steps using PowerShell:

1. Open PowerShell and change to your project folder:

```powershell
cd 'C:\Users\Registered User\nc-localities'
```

2. Run the auto-setup script (this uses Docker if available, or conda/venv fallback):

```powershell
# Replace <repo-name> with the name you want on GitHub
.\scripts\auto_setup_and_publish.ps1 -RepoName <repo-name>
```

3. What the script attempts automatically:
- Bootstraps the project files if they don't exist
- Runs the data pipeline inside Docker (if available) or locally otherwise
- Copies outputs into `site/data` and packages a `ZIP`
- Initializes a local git repo and commits files
- If the GitHub CLI (`gh`) is installed, it will automatically create a remote repo and push your code
- If `gh` isn't installed, it will prompt you to publish using GitHub Desktop with minimal clicks

4. After publish:
- On GitHub, go to the **Actions** tab to view the build & deploy runs
- Click the **Pages** tab under Settings to see your site URL (if `deploy_pages.yml` workflow publishes to Pages or check the workflow logs)

Notes:
- If you prefer not to use Docker, ensure `conda` (recommended) or `python` is installed and available.
- The `run_all` script supports `-UseDocker` to force Docker usage.

If you want me to also automate GitHub Pages enablement via the `gh` CLI, I can add that in a follow-up change.
