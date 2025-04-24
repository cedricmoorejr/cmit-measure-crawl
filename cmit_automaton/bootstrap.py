import subprocess, sys, shutil, importlib.util, textwrap, os
from pathlib import Path

def _run_pip(package: str) -> bool:
    """Attempt to install *package*; return True on success."""
    # Make sure we call python.exe, not pythonw.exe
    py_exe = Path(sys.executable)
    if py_exe.name.lower() == "pythonw.exe":
        py_exe = py_exe.with_name("python.exe")

    commands = [
        [str(py_exe), "-m", "pip", "install", package],
        [str(py_exe), "-m", "pip", "install", "--user", package],  # fallback OH NO
    ]
    for cmd in commands:
        try:
            print(f"Running: {' '.join(cmd)}")
            subprocess.check_call(cmd)
            return True
        except subprocess.CalledProcessError as e:
            print(f"pip failed (exit {e.returncode}). Trying fallback…" if cmd is commands[0] else "")
    return False


def install_missing_packages(requirements_path="requirements.txt"):
    """
    Ensure every line in requirements.txt is importable; install if not.
    """
    if not Path(requirements_path).exists():
        raise FileNotFoundError(f"Cannot find {requirements_path}")

    with open(requirements_path) as fh:
        for raw in fh:
            pkg_line = raw.strip()
            if not pkg_line or pkg_line.startswith("#"):
                continue

            # crude parse to get import-friendly name
            name = pkg_line.split("==")[0].split(">=")[0].replace("-", "_")
            if importlib.util.find_spec(name):
                continue  # already importable

            print(f"Missing package: {pkg_line}")
            if not _run_pip(pkg_line):
                raise RuntimeError(textwrap.dedent(f"""
                    Failed to install {pkg_line}.
                    • Check your internet connection
                    • If behind a proxy: set HTTPS_PROXY
                    • You may need to upgrade pip:  python -m pip install --upgrade pip
                """))


def run_main():
    from main  import full_crawl # entry point
    full_crawl()    
    
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    install_missing_packages()
    run_main()

