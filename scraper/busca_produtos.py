import csv
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

from scraper.selenium_busca import (
    iniciar_driver,
    buscar_mercadolivre_selenium,
    buscar_amazon_selenium
)




class BuscaProdutos:

    def __init__(self):
        self.falhas_marketplace = {
            "mercadolivre": 0,
            "amazon": 0
        }

        self.cooldown_ate = {
            "mercadolivre": None,
            "amazon": None
        }

        self.base_dir = Path(__file__).resolve().parent.parent
        self.lista_busca_path = self.base_dir / "config" / "lista_busca.txt"
        self.csv_path = self.base_dir / "config" / "produtos.csv"

    
    def pode_executar(self, marketplace):
        agora = datetime.now()

        if self.cooldown_ate[marketplace] is None:
            return True

        if agora >= self.cooldown_ate[marketplace]:
            print(f"🔓 Cooldown encerrado para {marketplace}")
            self.falhas_marketplace[marketplace] = 0
            self.cooldown_ate[marketplace] = None
            return True

        print(
            f"⏸ {marketplace} em cooldown até "
            f"{self.cooldown_ate[marketplace].strftime('%H:%M:%S')}"
        )
        return False

    
    def registrar_falha(self, marketplace):
        self.falhas_marketplace[marketplace] += 1

        print(f"⚠ Falha {marketplace}: {self.falhas_marketplace[marketplace]}")

        if self.falhas_marketplace[marketplace] >= 3:
            self.cooldown_ate[marketplace] = (
                datetime.now() + timedelta(minutes=30)
            )
            print(f"🚨 {marketplace} entrou em cooldown por 30 minutos")

    
    def carregar_lista_busca(self):
        grupos = {
            "baixo": [],
            "medio": [],
            "alto": []
        }

        if not self.lista_busca_path.exists():
            print("⚠ lista_busca.txt não encontrado")
            return grupos

        with open(self.lista_busca_path, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue

                try:
                    grupo, termo = linha.split(";")
                    grupo = grupo.strip().lower()
                    termo = termo.strip()

                    if grupo in grupos:
                        grupos[grupo].append(termo)

                except ValueError:
                    continue

        return grupos

    
    def salvar_no_csv(self, nome_base, links, limite_total=800):

        existentes = set()

        
        if not self.csv_path.exists():
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["categoria", "url"])

        with open(self.csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    existentes.add(row[1])

        novos = []

        for link in links:
            if link not in existentes:
                novos.append([nome_base, link])

        espaco_restante = limite_total - len(existentes)

        if espaco_restante <= 0:
            print("⚠ Limite máximo de produtos atingido.")
            return

        novos = novos[:espaco_restante]

        if not novos:
            print("🔁 Nenhum produto novo para adicionar.")
            return

        with open(self.csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(novos)

        print(f"✅ {len(novos)} novos produtos adicionados ao CSV")

    # -------------------------------------------------
    # EXECUTAR CICLO
    # -------------------------------------------------
    def executar(self):

        
        hora = datetime.now().hour
        if hora < 7 or hora > 23:
            print("⛔ Fora do horário operacional (07h–23h)")
            return

        grupos = self.carregar_lista_busca()

        total_por_ciclo = 3

        qtd_baixo = int(total_por_ciclo * 0.6)
        qtd_medio = int(total_por_ciclo * 0.3)
        qtd_alto = total_por_ciclo - qtd_baixo - qtd_medio

        termos = []

        if grupos["baixo"]:
            termos += random.sample(
                grupos["baixo"],
                min(qtd_baixo, len(grupos["baixo"]))
            )

        if grupos["medio"]:
            termos += random.sample(
                grupos["medio"],
                min(qtd_medio, len(grupos["medio"]))
            )

        if grupos["alto"]:
            termos += random.sample(
                grupos["alto"],
                min(qtd_alto, len(grupos["alto"]))
            )

        random.shuffle(termos)

        driver_ml = None
        driver_amz = None

        try:
            driver_ml = iniciar_driver()
            driver_amz = iniciar_driver()

            driver_ml.get("https://www.google.com")
            driver_amz.get("https://www.google.com")
            time.sleep(2)

            for termo in termos:

                print(f"\n🔎 Buscando: {termo}")

                ml_links = []
                amz_links = []

                marketplaces = ["mercadolivre", "amazon"]
                random.shuffle(marketplaces)

                for marketplace in marketplaces:

                    if not self.pode_executar(marketplace):
                        continue

                    limite = random.randint(5, 8)

                    try:
                        if marketplace == "mercadolivre":
                            ml_links = buscar_mercadolivre_selenium(
                                driver_ml, termo, limite=limite
                            )
                            self.falhas_marketplace["mercadolivre"] = 0

                        elif marketplace == "amazon":
                            amz_links = buscar_amazon_selenium(
                                driver_amz, termo, limite=limite
                            )
                            self.falhas_marketplace["amazon"] = 0

                    except Exception as e:
                        print(f"Erro {marketplace}: {e}")
                        self.registrar_falha(marketplace)

                todos_links = ml_links + amz_links

                print(f"ML encontrados: {len(ml_links)}")
                print(f"Amazon encontrados: {len(amz_links)}")

                self.salvar_no_csv(termo, todos_links)

                # Delay adaptativo
                total_encontrados = len(todos_links)

                if total_encontrados == 0:
                    delay = random.uniform(70, 110)
                elif total_encontrados < 5:
                    delay = random.uniform(45, 75)
                else:
                    delay = random.uniform(30, 55)

                print(f"⏳ Aguardando {round(delay,1)} segundos...")
                time.sleep(delay)

            print("🚀 Ciclo finalizado.")

        finally:
            if driver_ml:
                driver_ml.quit()
            if driver_amz:
                driver_amz.quit()




if __name__ == "__main__":
    busca = BuscaProdutos()
    busca.executar()