"""Simple script to verify required packages can be imported."""
import importlib

modules = [
    "dotenv",
    "telegram",
    "telegram.ext",
]

def check():
    ok = True
    for m in modules:
        try:
            importlib.import_module(m)
            print(f"OK: imported {m}")
        except Exception as e:
            ok = False
            print(f"FAIL: could not import {m}: {e}")
    return ok

if __name__ == "__main__":
    good = check()
    if not good:
        print("Some imports failed. Run 'python -m pip install -r requirements.txt' and ensure your editor is using the same interpreter.")
    else:
        print("All imports successful.")
