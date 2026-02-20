from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).parent / "posts"

OUTPUT_DIR.mkdir(exist_ok=True)

def salvar_texto(texto):
    agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    arquivo = OUTPUT_DIR / f"oferta_{agora}.txt"

    with open(arquivo, "w", encoding="utf-8") as f:
        f.write(texto)

    return arquivo
