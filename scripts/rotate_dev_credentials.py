import os
import subprocess
import secrets
import re
import sys

def main():
    print("Initiating local development database password rotation...")
    # 1. Generate strong random alphanumeric token
    new_pw = secrets.token_urlsafe(24)

    # 2. Execute ALTER ROLE inside Docker container using postgres superuser
    sql = f"ALTER ROLE consolith_app WITH PASSWORD '{new_pw}';"
    res = subprocess.run(
        ["docker", "exec", "convelina-postgres", "psql", "-U", "postgres", "-d", "consolith", "-c", sql],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        print(f"Failed to alter role password in PostgreSQL: {res.stderr}")
        sys.exit(1)
    print("PostgreSQL role 'consolith_app' password updated successfully.")

    # 3. Update .env file without printing the secret
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    if not os.path.exists(env_path):
        print("Error: .env not found")
        sys.exit(1)

    with open(env_path, "r", encoding="utf-8") as f:
        env_content = f.read()

    new_db_url = f"postgresql://consolith_app:{new_pw}@localhost:5432/consolith"
    if "DATABASE_URL=" in env_content:
        updated_env = re.sub(r"DATABASE_URL=.*", f"DATABASE_URL={new_db_url}", env_content)
    else:
        updated_env = env_content + f"\nDATABASE_URL={new_db_url}\n"

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(updated_env)
    print(".env updated with newly rotated connection string (secret masked).")

    # 4. Verify connection using psycopg2 directly
    import psycopg2
    try:
        conn = psycopg2.connect(
            dbname="consolith",
            user="consolith_app",
            password=new_pw,
            host="localhost",
            port=5432
        )
        cur = conn.cursor()
        cur.execute("SELECT current_user, current_database();")
        row = cur.fetchone()
        cur.close()
        conn.close()
        print(f"Connection verification succeeded: connected as {row[0]} on {row[1]}.")
    except Exception as e:
        print(f"Connection verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
