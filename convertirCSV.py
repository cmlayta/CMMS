import pandas as pd

# Leer usando UTF-16 (por el BOM detectado antes)
df = pd.read_csv(
    "Lista de Artículos 20251107.txt",
    encoding="utf-16",
    sep="\t",
    dtype=str  # evitar que los códigos se conviertan a números
)

# Eliminar columnas completamente vacías
df = df.dropna(axis=1, how="all")

# Guardar como CSV en UTF-8 con BOM (para MySQL y Excel)
df.to_csv("ListadeArtículos20251107.csv", index=False, encoding="utf-8-sig")
