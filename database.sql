-- Create Blood Bank Database
CREATE TABLE IF NOT EXISTS donors (
    donor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    phone TEXT NOT NULL,
    blood_group TEXT NOT NULL,
    city TEXT NOT NULL
);

-- Blood Inventory Table
CREATE TABLE IF NOT EXISTS inventory (
    blood_group TEXT PRIMARY KEY,
    units INTEGER NOT NULL DEFAULT 0
);

-- Blood Donation Table
CREATE TABLE IF NOT EXISTS donations (
    donation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id INTEGER NOT NULL,
    units INTEGER NOT NULL,
    donation_date TEXT NOT NULL,
    FOREIGN KEY (donor_id)
    REFERENCES donors(donor_id)
);

-- Blood Request Table
CREATE TABLE IF NOT EXISTS blood_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT NOT NULL,
    blood_group TEXT NOT NULL,
    units INTEGER NOT NULL,
    request_date TEXT NOT NULL,
    status TEXT NOT NULL
);

-- Insert Blood Groups
INSERT OR IGNORE INTO inventory VALUES ('A+', 0);
INSERT OR IGNORE INTO inventory VALUES ('A-', 0);
INSERT OR IGNORE INTO inventory VALUES ('B+', 0);
INSERT OR IGNORE INTO inventory VALUES ('B-', 0);
INSERT OR IGNORE INTO inventory VALUES ('AB+', 0);
INSERT OR IGNORE INTO inventory VALUES ('AB-', 0);
INSERT OR IGNORE INTO inventory VALUES ('O+', 0);
INSERT OR IGNORE INTO inventory VALUES ('O-', 0);
