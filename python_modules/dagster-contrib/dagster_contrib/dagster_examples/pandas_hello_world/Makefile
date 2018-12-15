# This makefile serves mostly as documentation for how various commands are run

# Execute the pipeline sum --> sum_sq. Do not output anything to disk
execute_sum_sq:
	python3 pipeline.py execute --input num_csv.path=num.csv --through sum_sq
.PHONY: execute_sum_sq

output_sum_sq_csv:
	python3 pipeline.py output \
		--input num_csv.path=num.csv \
		--output sum_sq.path=/tmp/sum_sq.csv \
		--output sum_sq.type=CSV 
.PHONY: output_sum_sq_csv 

output_sum_sq_parquet:
	python3 pipeline.py output \
		--input num_csv.path=num.csv \
		--output sum_sq.path=/tmp/sum_sq.parquet \
		--output sum_sq.type=PARQUET
.PHONY: output_sum_sq_parquet 

output_all_sum_csv:
	python3 pipeline.py output \
		--input num_csv.path=num.csv \
		--output sum_sq.path=/tmp/sum_sq.csv \
		--output sum_sq.type=CSV \
		--output sum.path=/tmp/sum.csv \
		--output sum.type=CSV
.PHONY: output_all_sum_csv
