from database.db import conectar

conn = conectar()
cursor = conn.cursor()

cursor.execute("""
    SELECT categoria, COUNT(*) 
    FROM metricas_promocoes
    GROUP BY categoria
""")

for row in cursor.fetchall():
    print(row)

conn.close()

