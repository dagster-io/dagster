#!bash

# Python
for schema in schema/*.schema.json; do
    quicktype -s schema -l python -o src/python/dagster_pipes/$(basename $schema .schema.json).py $schema
done
