PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE invoice_line_items
(
	invoice_id VARCHAR not null,
	order_date DATE not null,
	customer_id VARCHAR not null,
	customer_name VARCHAR,
	subscription_sku VARCHAR not null,
	subscription_sku_name VARCHAR not null,
	subscription_quantity NUMERIC(12,2) not null
, subscription_term INTEGER default 1 not null);
INSERT INTO invoice_line_items VALUES('INV-001',1635724800000,'CUST-001','Alpha Corp','100_VCPU_BUNDLE','100 VCPUs across any product',1,12);
INSERT INTO invoice_line_items VALUES('INV-002',1635984000000,'CUST-002','Beta Corp','100_VCPU_CLOUD','100 VCPUs for Cloud product',1,24);
INSERT INTO invoice_line_items VALUES('INV-003-invalid-order',1635984000000,'003','Invalid Customer Id','NEW_SKU','Unknown SKU',1,12);
CREATE TABLE cloud_deployment_heartbeats
(
	ts TIMESTAMP not null,
	customer_id VARCHAR not null,
	deployment_id VARCHAR not null,
	infrastructure VARCHAR not null,
	vcpu_usage NUMERIC(12,2) not null,
	memory_usage NUMERIC(12,2) not null
);
INSERT INTO cloud_deployment_heartbeats VALUES(1636372099000,'CUST-001','d5137cd9-4f2b-4eaf-81b2-e27f97c1fe92','AWS_EC2',14,2);
INSERT INTO cloud_deployment_heartbeats VALUES(1636458499000,'CUST-001','d5137cd9-4f2b-4eaf-81b2-e27f97c1fe92','AWS_EC2',16,2);
INSERT INTO cloud_deployment_heartbeats VALUES(1636544899000,'CUST-001','d5137cd9-4f2b-4eaf-81b2-e27f97c1fe92','AWS_EC2',15,2);
INSERT INTO cloud_deployment_heartbeats VALUES(1636631299000,'CUST-001','d5137cd9-4f2b-4eaf-81b2-e27f97c1fe92','AWS_EC2',15,2);
INSERT INTO cloud_deployment_heartbeats VALUES(1636717699000,'CUST-001','d5137cd9-4f2b-4eaf-81b2-e27f97c1fe92','AWS_EC2',15,2);
INSERT INTO cloud_deployment_heartbeats VALUES(1636804099000,'CUST-001','d5137cd9-4f2b-4eaf-81b2-e27f97c1fe92','AWS_EC2',15,2);
INSERT INTO cloud_deployment_heartbeats VALUES(1636890499000,'CUST-001','d5137cd9-4f2b-4eaf-81b2-e27f97c1fe92','AWS_EC2',15,2);
INSERT INTO cloud_deployment_heartbeats VALUES(1636976899000,'CUST-001','d5137cd9-4f2b-4eaf-81b2-e27f97c1fe92','AWS_EC2',15,2);
INSERT INTO cloud_deployment_heartbeats VALUES(1637063299000,'CUST-001','d5137cd9-4f2b-4eaf-81b2-e27f97c1fe92','AWS_EC2',15,2);
INSERT INTO cloud_deployment_heartbeats VALUES(1637149699000,'CUST-001','d5137cd9-4f2b-4eaf-81b2-e27f97c1fe92','AWS_EC2',15,2);
INSERT INTO cloud_deployment_heartbeats VALUES(1637236099000,'CUST-001','d5137cd9-4f2b-4eaf-81b2-e27f97c1fe92','AWS_EC2',15,2);
INSERT INTO cloud_deployment_heartbeats VALUES(1636890499000,'CUST-001','d5137cd9-4f2b-4eaf-81b2-e27f97c1fe92','AWS_EC2',15,2);
INSERT INTO cloud_deployment_heartbeats VALUES(1636976899000,'CUST-002','deac2bdd-ebcb-42fd-85c9-ea486ccf028a','GCP_GCE',1,1);
INSERT INTO cloud_deployment_heartbeats VALUES(1637063299000,'CUST-002','deac2bdd-ebcb-42fd-85c9-ea486ccf028a','GCP_GCE',250,500);
INSERT INTO cloud_deployment_heartbeats VALUES(1637149699000,'CUST-002','deac2bdd-ebcb-42fd-85c9-ea486ccf028a','GCP_GCE',250,500);
INSERT INTO cloud_deployment_heartbeats VALUES(1637236099000,'CUST-002','deac2bdd-ebcb-42fd-85c9-ea486ccf028a','GCP_GCE',250,500);
INSERT INTO cloud_deployment_heartbeats VALUES(1637322499000,'CUST-002','deac2bdd-ebcb-42fd-85c9-ea486ccf028a','GCP_GCE',10,4);
COMMIT;
