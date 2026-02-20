from database.db import conectar

LINK = "https://www.mercadolivre.com.br/tenis-fila-racer-skytrail-trilha/up/MLBU3375538915"

conn = conectar()
cursor = conn.cursor()

cursor.execute("""
    SELECT p.id, p.nome
    FROM produtos p
    WHERE p.link = ?
""", (LINK,))

row = cursor.fetchone()

if not row:
    print("Produto não encontrado no banco")
    exit()

produto_id = row[0]
print("Produto ID:", produto_id)

cursor.execute("""
    SELECT preco, data_coleta
    FROM historico_precos
    WHERE produto_id = ?
    ORDER BY data_coleta DESC
""", (produto_id,))

for preco, data in cursor.fetchall():
    print(preco, data)

conn.close()
