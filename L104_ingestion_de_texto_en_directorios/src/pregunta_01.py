import os
import pandas as pd
from pathlib import Path

def pregunta_01():
    submission_dir = Path("submission")
    submission_dir.mkdir(parents=True, exist_ok=True)
    
    for split in ["train", "test"]:
        datos = []
        ruta_base = Path(f"data/{split}")
        
        for target in sorted(os.listdir(ruta_base)):
            ruta_target = ruta_base / target
            
            if ruta_target.is_dir():
                for archivo in sorted(os.listdir(ruta_target)):
                    if archivo.endswith(".txt"):
                        ruta_archivo = ruta_target / archivo
                        
                        with open(ruta_archivo, "r", encoding="utf-8") as f:
                            frase = f.read().strip()
                            datos.append([frase, target])
                            
        df = pd.DataFrame(datos, columns=["phrase", "target"])
        df.to_csv(submission_dir / f"{split}_dataset.csv", index=False)