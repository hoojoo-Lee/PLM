import sqlite3

conn = sqlite3.connect('plm.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE customers ADD COLUMN background_info TEXT")
    print("Added background_info")
except sqlite3.OperationalError:
    print("background_info already exists")

try:
    cursor.execute("ALTER TABLE customers ADD COLUMN customer_team VARCHAR(500)")
    print("Added customer_team")
except sqlite3.OperationalError:
    print("customer_team already exists")

try:
    cursor.execute("ALTER TABLE customers ADD COLUMN pm_contacts TEXT")
    print("Added pm_contacts")
except sqlite3.OperationalError:
    print("pm_contacts already exists")

try:
    cursor.execute("ALTER TABLE customers ADD COLUMN shipping_address TEXT")
    print("Added shipping_address")
except sqlite3.OperationalError:
    print("shipping_address already exists")

cursor.execute("PRAGMA table_info(customers)")
columns = [col[1] for col in cursor.fetchall()]
print(f"\nCurrent columns: {columns}")

conn.commit()
conn.close()
print("\nDatabase schema synced successfully!")
