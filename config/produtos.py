import csv
import random

def carregar_produtos(limite_execucao=400):
    produtos = []
    vistos = set()
    try:
        with open(
            "config/produtos.csv",
            newline="",
            encoding="utf-8-sig"
        ) as f:
            reader = csv.DictReader(f)

            for row in reader:
                url = row.get("url", "").strip()
                categoria = row.get("categoria", "").strip()

                if not url:
                    continue

                if url in vistos:
                    continue  # evita duplicado

                vistos.add(url)

                produtos.append({
                    "categoria": categoria,
                    "url": url
                })
    except FileNotFoundError:
        print("⚠ Arquivo produtos.csv não encontrado.")
        return []
    # 🔀 embaralha ordem (comportamento humano)
    random.shuffle(produtos)
    # 🔒 limita quantidade por execução
    produtos = produtos[:limite_execucao]
    print(f"🔎 {len(produtos)} produtos carregados para monitoramento.")
    return produtos
def identificar_marketplace(url):
    url = url.lower()
    if "mercadolivre" in url:
        return "mercadolivre"
    elif "amazon" in url:
        return "amazon"
    elif "magazinevoce" in url or "magalu" in url:
        return "magalu"
    else:
        return None


