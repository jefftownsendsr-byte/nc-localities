# Getting Started — Minimal steps (Beginner-friendly)

1. Open PowerShell and change to your project folder:

```powershell
cd 'C:\Users\Registered User\nc-localities'
```

2. Run environment pre-check (optional but recommended):

```powershell
.\scripts\prepublish_check.ps1
```

3. If the check is OK, run the all-in-one setup, build, and publish script (this will use Docker if available):

```powershell
# Replace <repo-name> with the name you want on GitHub
.\scripts\auto_setup_and_publish.ps1 -RepoName <repo-name>
```

4. After the script completes, the site should be building in GitHub Actions and GitHub Pages should be enabled (if gh CLI was installed and authenticated).

5. If you did not create a repo via `gh` (the script will open GitHub Desktop), publish the repo with GitHub Desktop with a click.

6. View your site once CI finishes: Settings → Pages or via `https://<username>.github.io/<repo-name>/`.

If something doesn't work, re-run `prepublish_check.ps1` and follow any messages that appear.

Testing locally:

If you just want to run a quick smoke test that copies output to `site/` and confirms the map exists, run:

PowerShell:
```powershell
# Create a venv (optional)
python -m venv .\venv
. .\venv\Scripts\Activate
python -m pip install --upgrade pip
python -m pip install pytest
pytest -q
```


Tips:
- If Docker is installed, the script will default to Docker for a reliable build environment.
- If `gh` is not installed, download and sign in with your GitHub account to enable automatic remote creation.
