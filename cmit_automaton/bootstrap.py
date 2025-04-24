import subprocess
import sys
from pathlib import Path

def install_missing_packages(requirements_path="requirements.txt"):
    """
    Installs packages listed in the given requirements.txt if they're not already installed.
    """
    if not Path(requirements_path).exists():
        raise FileNotFoundError(f" Could not find {requirements_path}")

    with open(requirements_path, "r") as f:
        for line in f:
            package = line.strip()
            if not package or package.startswith("#"):
                continue  # skip comments and empty lines
            package_name = package.split("==")[0].split(">=")[0]  # crude parse
            try:
                __import__(package_name.replace("-", "_"))  # import pandas, pyyaml, etc.
            except ImportError:
                print(f" Installing missing package: {package}")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def run_main():
    import main  # entry point

if __name__ == "__main__":
    install_missing_packages()
    run_main()
