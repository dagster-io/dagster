CREATE TABLE invoices (
    invoice_id INT,
    organization_id INT,
    amount DECIMAL(10, 2),
    issued_date TIMESTAMP,
    due_date TIMESTAMP,
    payer_user_id INT,
    paid_date TIMESTAMP,
    status VARCHAR(50),
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);