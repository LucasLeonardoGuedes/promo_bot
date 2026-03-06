from datetime import datetime, timedelta


class PromoRules:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()

    
    def _buscar_precos_recentes(self, produto_id, limite=10):
        self.cursor.execute("""
            SELECT preco
            FROM historico_precos
            WHERE produto_id = ?
            ORDER BY data_coleta DESC
            LIMIT ?
        """, (produto_id, limite))

        return [row[0] for row in self.cursor.fetchall()]

  
    def verificar_promocao(self, produto, percentual_minimo=10):
        produto_id = produto["id"]

        precos = self._buscar_precos_recentes(produto_id, limite=10)

        if len(precos) < 2:
            return False

        preco_atual = precos[0]

        preco_anterior = None
        for p in precos[1:]:
            if p != preco_atual:
                preco_anterior = p
                break

        
        if not preco_anterior or preco_anterior == 0:
            return False

        queda_percentual = ((preco_anterior - preco_atual) / preco_anterior) * 100

        return queda_percentual >= percentual_minimo

   
    def obter_preco_anterior(self, produto):
        produto_id = produto["id"]

        precos = self._buscar_precos_recentes(produto_id, limite=10)

        if len(precos) < 2:
            return None

        preco_atual = precos[0]

        for p in precos[1:]:
            if p != preco_atual:
                return p

        return None

    
    def promocao_ja_postada(self, produto, preco_atual):
        produto_id = produto["id"]

        self.cursor.execute("""
            SELECT preco_atual
            FROM metricas_promocoes
            WHERE produto_id = ?
            ORDER BY data_evento DESC
            LIMIT 1
        """, (produto_id,))

        row = self.cursor.fetchone()

        if not row:
            return False

        ultimo_preco_postado = row[0]
        return ultimo_preco_postado == preco_atual

   
    def pode_repostar(self, produto, horas=6):
        produto_id = produto["id"]

        self.cursor.execute("""
            SELECT data_evento
            FROM metricas_promocoes
            WHERE produto_id = ?
            ORDER BY data_evento DESC
            LIMIT 1
        """, (produto_id,))

        row = self.cursor.fetchone()

        if not row:
            return True

        try:
            ultima_data = datetime.fromisoformat(row[0])
        except Exception:
            return True

        return datetime.now() - ultima_data >= timedelta(hours=horas)


    def preco_historico(self, produto, minimo_registros=5):
        produto_id = produto["id"]

        precos = self._buscar_precos_recentes(produto_id, limite=50)

       
        if len(precos) - 1 < minimo_registros:
            return False

        preco_atual = precos[0]
        menor_preco_anterior = min(precos[1:])

        return preco_atual < menor_preco_anterior





