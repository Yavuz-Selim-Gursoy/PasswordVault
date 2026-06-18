from pathlib import Path

base = Path(__file__).parent.parent.resolve()
dirs = ["vaults"]
for d in dirs:
    (Path(base) / d).mkdir(parents=True, exist_ok=True)
    print(f"Created: {d}")
