-- Shared Expenses App — relational schema (PostgreSQL / SQLite compatible)

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    name VARCHAR(80) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE group_memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    joined_at DATE NOT NULL,
    left_at DATE,
    role VARCHAR(20) DEFAULT 'member'
);

CREATE TABLE expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    description VARCHAR(255) NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    amount_inr NUMERIC(12,2) NOT NULL,
    exchange_rate NUMERIC(10,4) DEFAULT 1.0,
    expense_date DATE NOT NULL,
    paid_by_user_id INTEGER REFERENCES users(id),
    split_type VARCHAR(20) DEFAULT 'equal',
    notes TEXT,
    status VARCHAR(20) DEFAULT 'active',
    import_row_number INTEGER,
    import_session_id INTEGER REFERENCES import_sessions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE expense_splits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL REFERENCES expenses(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    share_value NUMERIC(12,4),
    allocated_amount_inr NUMERIC(12,2) NOT NULL
);

CREATE TABLE settlements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    from_user_id INTEGER NOT NULL REFERENCES users(id),
    to_user_id INTEGER NOT NULL REFERENCES users(id),
    amount_inr NUMERIC(12,2) NOT NULL,
    settlement_date DATE NOT NULL,
    notes TEXT,
    import_row_number INTEGER,
    import_session_id INTEGER REFERENCES import_sessions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE import_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    uploaded_by INTEGER NOT NULL REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(30) DEFAULT 'completed',
    report_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE import_anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_session_id INTEGER NOT NULL REFERENCES import_sessions(id),
    row_number INTEGER NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    raw_data TEXT,
    suggested_action TEXT,
    action_taken TEXT,
    status VARCHAR(20) DEFAULT 'auto_resolved',
    requires_approval BOOLEAN DEFAULT 0
);
