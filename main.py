import sqlite3
from datetime import date

DB_NAME = "blood_bank.db"

BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")


class BloodBank:

    # 1. Database connection
    def __init__(self):
        self.create_tables()

    def connect(self):
        return sqlite3.connect(DB_NAME)

    # 2. Create database tables
    def create_tables(self):

        with self.connect() as con:

            con.execute("""
                CREATE TABLE IF NOT EXISTS donors (
                    donor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    phone TEXT NOT NULL,
                    blood_group TEXT NOT NULL,
                    city TEXT NOT NULL
                )
            """)

            con.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    blood_group TEXT PRIMARY KEY,
                    units INTEGER NOT NULL DEFAULT 0
                )
            """)

            con.execute("""
                CREATE TABLE IF NOT EXISTS donations (
                    donation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    donor_id INTEGER NOT NULL,
                    units INTEGER NOT NULL,
                    donation_date TEXT NOT NULL,
                    FOREIGN KEY (donor_id)
                    REFERENCES donors(donor_id)
                )
            """)

            con.execute("""
                CREATE TABLE IF NOT EXISTS blood_requests (
                    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_name TEXT NOT NULL,
                    blood_group TEXT NOT NULL,
                    units INTEGER NOT NULL,
                    request_date TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """)

            # Insert all blood groups into inventory
            for group in BLOOD_GROUPS:
                con.execute(
                    """INSERT OR IGNORE INTO inventory
                    (blood_group, units) VALUES (?, 0)""",
                    (group,)
                )

    # 3. Validate blood group
    def valid_blood_group(self, group):
        return group.upper() in BLOOD_GROUPS

    # 4. Input validation
    def get_integer(self, message, minimum=0):

        while True:
            try:
                value = int(input(message))

                if value < minimum:
                    print(f"Enter a number greater than or equal to {minimum}.")
                    continue

                return value

            except ValueError:
                print("Please enter a valid number.")

    # 5. Add donor
    def add_donor(self):

        print("\n----- ADD DONOR -----")

        name = input("Enter donor name: ").strip()
        age = self.get_integer("Enter age: ", 18)
        phone = input("Enter phone number: ").strip()

        group = input("Enter blood group: ").strip().upper()
        city = input("Enter city: ").strip()

        if not name or not phone or not city:
            print("Please fill all details.")
            return

        if not self.valid_blood_group(group):
            print("Invalid blood group!")
            return

        with self.connect() as con:

            cursor = con.execute("""
                INSERT INTO donors
                (name, age, phone, blood_group, city)
                VALUES (?, ?, ?, ?, ?)
            """, (name, age, phone, group, city))

            print("Donor added successfully!")
            print("Donor ID:", cursor.lastrowid)

    # 6. View all donors
    def view_donors(self):

        with self.connect() as con:

            donors = con.execute("""
                SELECT * FROM donors
                ORDER BY donor_id
            """).fetchall()

        print("\n----- ALL DONORS -----")

        if not donors:
            print("No donor records found.")
            return

        for donor in donors:

            print("--------------------------------")
            print("Donor ID:", donor[0])
            print("Name:", donor[1])
            print("Age:", donor[2])
            print("Phone:", donor[3])
            print("Blood Group:", donor[4])
            print("City:", donor[5])

    # 7. Search donor by blood group
    def search_donor(self):

        group = input("Enter blood group to search: ").strip().upper()

        if not self.valid_blood_group(group):
            print("Invalid blood group!")
            return

        with self.connect() as con:

            donors = con.execute("""
                SELECT * FROM donors
                WHERE blood_group = ?
            """, (group,)).fetchall()

        print("\n----- SEARCH RESULTS -----")

        if not donors:
            print("No matching donors found.")
            return

        for donor in donors:

            print("--------------------------------")
            print("Donor ID:", donor[0])
            print("Name:", donor[1])
            print("Age:", donor[2])
            print("Phone:", donor[3])
            print("Blood Group:", donor[4])
            print("City:", donor[5])

    # 8. Record blood donation
    def record_donation(self):

        print("\n----- RECORD DONATION -----")

        donor_id = self.get_integer("Enter donor ID: ", 1)
        units = self.get_integer("Enter demo units donated: ", 1)

        with self.connect() as con:

            donor = con.execute("""
                SELECT blood_group FROM donors
                WHERE donor_id = ?
            """, (donor_id,)).fetchone()

            if donor is None:
                print("Donor not found!")
                return

            group = donor[0]

            con.execute("""
                INSERT INTO donations
                (donor_id, units, donation_date)
                VALUES (?, ?, ?)
            """, (donor_id, units, date.today().isoformat()))

            con.execute("""
                UPDATE inventory
                SET units = units + ?
                WHERE blood_group = ?
            """, (units, group))

            self.process_pending_requests(con, group)

        print("Donation recorded successfully!")
        print("Blood Group:", group)
        print("Demo Units Added:", units)

    # 9. View blood inventory
    def view_inventory(self):

        with self.connect() as con:

            inventory = con.execute("""
                SELECT * FROM inventory
                ORDER BY blood_group
            """).fetchall()

        print("\n----- BLOOD INVENTORY -----")

        for group, units in inventory:
            print(group, ":", units, "demo units")

    # 10. Request blood
    def request_blood(self):

        print("\n----- BLOOD REQUEST -----")

        patient = input("Enter patient name: ").strip()

        group = input("Enter required blood group: ").strip().upper()

        units = self.get_integer("Enter demo units required: ", 1)

        if not patient:
            print("Patient name cannot be empty.")
            return

        if not self.valid_blood_group(group):
            print("Invalid blood group!")
            return

        with self.connect() as con:

            available = con.execute("""
                SELECT units FROM inventory
                WHERE blood_group = ?
            """, (group,)).fetchone()[0]

            if available >= units:

                status = "Issued"

                con.execute("""
                    UPDATE inventory
                    SET units = units - ?
                    WHERE blood_group = ?
                """, (units, group))

            else:
                status = "Pending"

            cursor = con.execute("""
                INSERT INTO blood_requests
                (patient_name, blood_group, units,
                 request_date, status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                patient,
                group,
                units,
                date.today().isoformat(),
                status
            ))

            request_id = cursor.lastrowid

        print("Request ID:", request_id)
        print("Request Status:", status)

        if status == "Pending":
            print("Insufficient demo inventory. Request saved as pending.")

    # 11. Process pending requests
    def process_pending_requests(self, con, group):

        pending = con.execute("""
            SELECT request_id, units
            FROM blood_requests
            WHERE blood_group = ?
            AND status = 'Pending'
            ORDER BY request_id
        """, (group,)).fetchall()

        for request_id, units in pending:

            available = con.execute("""
                SELECT units FROM inventory
                WHERE blood_group = ?
            """, (group,)).fetchone()[0]

            if available < units:
                break

            con.execute("""
                UPDATE inventory
                SET units = units - ?
                WHERE blood_group = ?
            """, (units, group))

            con.execute("""
                UPDATE blood_requests
                SET status = 'Issued'
                WHERE request_id = ?
            """, (request_id,))

    # 12. View blood requests
    def view_requests(self):

        with self.connect() as con:

            requests = con.execute("""
                SELECT * FROM blood_requests
                ORDER BY request_id DESC
            """).fetchall()

        print("\n----- BLOOD REQUEST HISTORY -----")

        if not requests:
            print("No requests found.")
            return

        for request in requests:

            print("--------------------------------")
            print("Request ID:", request[0])
            print("Patient Name:", request[1])
            print("Blood Group:", request[2])
            print("Units:", request[3])
            print("Request Date:", request[4])
            print("Status:", request[5])

    # 13. Main menu
    def show_menu(self):

        print("""
========================================
       BLOOD BANK MANAGEMENT SYSTEM
========================================

1. Add Donor
2. View All Donors
3. Search Donor
4. Record Blood Donation
5. View Blood Inventory
6. Request Blood
7. View Blood Requests
8. Exit

========================================
""")

    # 14. Run application
    def run(self):

        while True:

            self.show_menu()

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.add_donor()

            elif choice == "2":
                self.view_donors()

            elif choice == "3":
                self.search_donor()

            elif choice == "4":
                self.record_donation()

            elif choice == "5":
                self.view_inventory()

            elif choice == "6":
                self.request_blood()

            elif choice == "7":
                self.view_requests()

            elif choice == "8":
                print("Thank you for using Blood Bank Management System!")
                break

            else:
                print("Invalid choice! Please select 1 to 8.")


# Main program
if __name__ == "__main__":

    app = BloodBank()
    app.run()
