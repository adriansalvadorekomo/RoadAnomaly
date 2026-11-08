import json
from pathlib import Path

nb_path = Path("notebooks/4_Modeling/B_Autoencoder.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))

print(f"=== Structure de {nb_path.name} ===\n")
code_idx = 0
for i, cell in enumerate(nb["cells"]):
    src = "".join(cell["source"]).strip()
    first_line = src.split("\n")[0][:90] if src else "(vide)"
    if cell["cell_type"] == "markdown":
        # Première ligne non-vide du markdown
        for line in src.split("\n"):
            if line.strip():
                print(f"[{i:3d}] MD    {line[:90]}")
                break
    elif cell["cell_type"] == "code":
        n_outputs = len(cell.get("outputs", []))
        print(f"[{i:3d}] CODE  ({n_outputs} outputs)  {first_line}")
        code_idx += 1

print(f"\n=== Total : {len(nb['cells'])} cellules ({code_idx} code) ===")
