import subprocess
import sys

packages = ["ttkbootstrap", "matplotlib"]
result = subprocess.run(
    [sys.executable, "-m", "pip", "install"] + packages, capture_output=True, text=True
)
print("STDOUT:", result.stdout[-500:])
print("STDERR:", result.stderr[-500:])
print("Return code:", result.returncode)
