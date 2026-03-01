from database.db import conectar

LINK_CANONICO = "https://www.amazon.com.br/TCL-QLED-SMART-65P8K-GOOGLE/dp/B0GH2L5MZL/ref=sr_1_9"
PRECO_SIMULADO = 4700.00

conn = conectar()
cursor = conn.cursor()

# procura produto pelo link ORIGINAL (contido dentro do link afiliado)
cursor.execute("""
    SELECT id, link FROM produtos
    WHERE link LIKE ?
""", (f"%{LINK_CANONICO}%",))

resultado = cursor.fetchone()

if not resultado:
    print("Produto ainda não existe no banco (link canônico não encontrado).")
    conn.close()
    exit()

produto_id = resultado[0]

cursor.execute("""
    INSERT INTO historico_precos (produto_id, preco)
    VALUES (?, ?)
""", (produto_id, PRECO_SIMULADO))

conn.commit()
conn.close()

print("Preço antigo simulado com sucesso.")

