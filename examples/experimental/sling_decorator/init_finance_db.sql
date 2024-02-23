\c postgres

DROP DATABASE IF EXISTS finance;
DROP DATABASE IF EXISTS clone;
CREATE DATABASE finance;
CREATE DATABASE clone;

\c finance

CREATE TABLE IF NOT EXISTS accounts (
    account_id serial PRIMARY KEY,
    user_id int,
    balance decimal(15,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    user_id serial PRIMARY KEY,
    name varchar(255) NOT NULL,
    email varchar(255) UNIQUE NOT NULL,
    department_id int
);

CREATE TABLE IF NOT EXISTS finance_departments_old (
    department_id serial PRIMARY KEY,
    name varchar(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS "Transactions"(
    id serial PRIMARY KEY,
    account_id int,
    amount decimal(15,2) NOT NULL,
    last_updated_at timestamp without time zone NOT NULL
);

CREATE TABLE IF NOT EXISTS "all_Users" (
    all_user_id serial PRIMARY KEY,
    name varchar(255) NOT NULL
);

INSERT INTO accounts (user_id, balance) VALUES
(1, 1000.00),
(2, 1500.00);

INSERT INTO users (name, email, department_id) VALUES
('John Doe', 'john.doe@example.com', 1),
('Jane Smith', 'jane.smith@example.com', 2);

INSERT INTO finance_departments_old (name) VALUES ('Accounting'), ('Human Resources'), ('Engineering');

INSERT INTO "Transactions" (account_id, amount, last_updated_at) VALUES
(1, -200.00, '2023-01-15 14:30:00'),
(1, 300.00, '2023-02-15 10:00:00'),
(2, -150.00, '2023-01-20 09:00:00');

INSERT INTO "all_Users" (name) VALUES ('Alice Johnson'), ('Bob Williams'), ('Charlie Miller');

