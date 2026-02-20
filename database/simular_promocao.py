from database.db import conectar

LINK_CANONICO = "https://www.mercadolivre.com.br/monitor-gamer-lg-ultragear-24-24gs60f-b-ips-full-hd-180hz-1ms-gtg-nvidia-g-sync-amd-freesync-hdr10-srgb-99-hdmi-displayport/p/MLB38947984"
PRECO_SIMULADO = 4100.00

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

