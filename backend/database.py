import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "jalrakshak.db")

def get_db_connection():
    """Establishes a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if the tables do not exist."""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            image_path TEXT NOT NULL,
            contamination_signs TEXT NOT NULL, -- Comma-separated list of signs
            risk_level TEXT NOT NULL,          -- Low, Medium, High
            advisory TEXT NOT NULL,            -- Safety advisory details
            cluster_id INTEGER,                -- References clusters(id)
            escalated INTEGER DEFAULT 0        -- 0 = No, 1 = Yes
        )
    """)

    # Create clusters table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            severity TEXT NOT NULL,            -- Low, Medium, High
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'Active'       -- Active, Resolved
        )
    """)

    conn.commit()
    conn.close()

def add_report(latitude, longitude, image_path, contamination_signs, risk_level, advisory):
    """Inserts a new water report into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    # Clean inputs: convert lists to comma-separated strings
    if isinstance(contamination_signs, list):
        signs_str = ", ".join(contamination_signs)
    else:
        signs_str = str(contamination_signs)

    cursor.execute("""
        INSERT INTO reports (timestamp, latitude, longitude, image_path, contamination_signs, risk_level, advisory)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, latitude, longitude, image_path, signs_str, risk_level, advisory))
    
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id

def get_all_reports():
    """Retrieves all reports sorted by timestamp descending."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_unescalated_reports():
    """Retrieves reports that have not yet been escalated and are not part of any cluster."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE escalated = 0 AND cluster_id IS NULL")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def create_cluster(latitude, longitude, severity):
    """Creates a new report cluster."""
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO clusters (latitude, longitude, severity, created_at)
        VALUES (?, ?, ?, ?)
    """, (latitude, longitude, severity, created_at))
    cluster_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return cluster_id

def associate_reports_with_cluster(report_ids, cluster_id):
    """Updates reports to link them to a specific cluster."""
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in report_ids)
    cursor.execute(f"""
        UPDATE reports
        SET cluster_id = ?
        WHERE id IN ({placeholders})
    """, [cluster_id] + list(report_ids))
    conn.commit()
    conn.close()

def mark_reports_as_escalated(report_ids):
    """Flags a list of reports as escalated (alert dispatched)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in report_ids)
    cursor.execute(f"""
        UPDATE reports
        SET escalated = 1
        WHERE id IN ({placeholders})
    """, list(report_ids))
    conn.commit()
    conn.close()

def get_all_clusters():
    """Retrieves all clusters along with the number of associated reports."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, COUNT(r.id) as report_count 
        FROM clusters c 
        LEFT JOIN reports r ON c.id = r.cluster_id 
        GROUP BY c.id
        ORDER BY c.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
