import psycopg
conn = psycopg.connect('postgresql://root:secret@postgres:5432/project_monopoly')
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'competitor_profiles' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(r[0])
