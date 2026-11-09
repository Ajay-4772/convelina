import psycopg2

def main():
    conn = psycopg2.connect("postgresql://postgres:postgres_dev_password@localhost:5432/consolith")
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("UPDATE users SET email = 'upload_tester@example.com' WHERE id = 'af450100-8aff-4b1c-bae5-941f3abe9803';")
        cur.execute("UPDATE users SET email = 'other_citizen@example.com' WHERE id = 'b9ecab79-ac89-481b-b514-e1c8bfbb043f';")
        cur.execute("SELECT lower(email), count(*) FROM users GROUP BY lower(email) HAVING count(*) > 1;")
        dupes = cur.fetchall()
        print("Remaining duplicate emails:", dupes)

if __name__ == "__main__":
    main()

