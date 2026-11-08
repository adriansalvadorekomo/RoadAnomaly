import json
nb = json.load(open("notebooks/4_Modeling/B_Autoencoder.ipynb"))
for i in (8, 9, 11):
    cell = nb["cells"][i]
    print(f"\n=== Cellule {i} ===")
    print("".join(cell["source"]))
    if i == 11 and cell.get("outputs"):
        print(f"\n=== Cellule {i} output ===")
        for out in cell["outputs"]:
            if "text" in out:
                print("".join(out["text"]))
