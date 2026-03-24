import os

carpeta = os.path.dirname(os.path.abspath(__file__))
salida = "all_models.txt"
este_script = os.path.basename(__file__)

with open(salida, "w", encoding="utf-8") as out:
    for root, dirs, files in os.walk(carpeta):
        for file in files:
            if file == este_script:
                continue

            ruta = os.path.join(root, file)

            out.write(f"===== {file} =====\n")

            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    out.write(f.read())
            except Exception as e:
                out.write(f"[No se pudo leer: {e}]")

            out.write("\n\n")

print("Dump creado: models.txt")