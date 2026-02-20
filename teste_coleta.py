from scraper.ml_scraper import coletar_produto

url = "https://www.mercadolivre.com.br/tenis-fila-racer-skytrail-trilha/up/MLBU3375538915"

produto = coletar_produto(url)

print(produto)
