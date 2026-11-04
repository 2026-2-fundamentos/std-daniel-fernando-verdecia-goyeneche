import pandas as pd

def pregunta_01():
    with open("data/clusters_report.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    filas = []
    cluster = None
    cantidad = None
    porcentaje = None
    palabras = ""
    
    for line in lines[4:]:
        if not line.strip():
            continue
            
        partes = line.split()
        if partes[0].isdigit():
            if cluster is not None:
                palabras = ' '.join(palabras.split())
                if palabras.endswith('.'):
                    palabras = palabras[:-1]
                filas.append([cluster, cantidad, porcentaje, palabras])
                
            cluster = int(partes[0])
            cantidad = int(partes[1])
            porcentaje = float(partes[2].replace(',', '.'))
            palabras = line[line.find('%')+1:].strip()
        else:
            palabras += ' ' + line.strip()
            
    if cluster is not None:
        palabras = ' '.join(palabras.split())
        if palabras.endswith('.'):
            palabras = palabras[:-1]
        filas.append([cluster, cantidad, porcentaje, palabras])
        
    df = pd.DataFrame(filas, columns=[
        'cluster', 
        'cantidad_de_palabras_clave', 
        'porcentaje_de_palabras_clave', 
        'principales_palabras_clave'
    ])
    
    return df