@PHONY: build run clean sync stop check_version

check_version:
	@required_version="1.1.7"; \
	current_version=$$(sling --version | awk '{print $$2}'); \
	if [ "$$(printf '%s\n' "$$required_version" "$$current_version" | sort -V | head -n1)" = "$$required_version" ]; then \
		exit 0; \
	else \
		echo "sling version is less than $$required_version", run pip install --upgrade sling; \
		exit 1; \
	fi

clean:
	docker ps -q -f name=sling-postgres | xargs -r docker stop && docker ps -aq -f name=sling-postgres | xargs -r docker rm

stop:
	docker ps -q -f name=sling-postgres | xargs -r docker stop

build:
	docker build -t sling-postgres .

run: build stop
	docker run --name sling-postgres --detach -p 54321:5432 -ti --rm sling-postgres

sync: check_version
	MY_POSTGRES=postgres://postgres:postgres@localhost:54321/finance?sslmode=disable \
				MY_DUCKDB=duckdb:///var/tmp/duckdb.db \
				sling run -r sling_replication.yaml

verify:	
	@echo "		POSTGRES"
	@echo "--------------------------------"
	@echo "SELECT * FROM public.\"all_Users\";" | docker exec -i sling-postgres psql -U postgres -d finance
	@echo "		DUCKDB"
	@echo "--------------------------------"
	@echo "SELECT * FROM public.all_users;" | duckdb /var/tmp/duckdb.db
