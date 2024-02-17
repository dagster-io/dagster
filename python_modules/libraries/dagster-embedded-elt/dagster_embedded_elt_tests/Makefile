@PHONY: build run

build:
	docker build -t finance-postgres .

run: build
	docker run --name finance-db -p 5432:5432 -ti --rm finance-postgres

sync: 
	MY_POSTGRES=postgres://postgres:postgres@localhost:5432/finance?sslmode=disable \
				MY_OTHER_POSTGRES=duckdb:///var/tmp/duckdb.db \
				sling run -r sling_replication.yaml

