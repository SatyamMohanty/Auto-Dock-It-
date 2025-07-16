# backend/repo_cloner.py
import stat

import os
import shutil
from git import Repo
from rich import print


def clone_repository(github_url: str, clone_path: str = "data/cloned_repo") -> bool:
    try:
        # Remove old cloned repo if it exists
        if os.path.exists(clone_path):
            print("🧹 Removing previous clone folder...")
            shutil.rmtree(clone_path, onerror=handle_remove_readonly)


        # Clone the new repository
        print(f"[blue]Cloning repository from:[/blue] {github_url}")
        Repo.clone_from(github_url, clone_path)
        print("[green]✅ Repository cloned successfully![/green]")
        return True

    except Exception as e:
        print(f"[red]❌ Error cloning repository:[/red] {e}")
        return False

def handle_remove_readonly(func, path, _):
    """ Handle read-only files during shutil.rmtree() """
    os.chmod(path, stat.S_IWRITE)
    func(path)
