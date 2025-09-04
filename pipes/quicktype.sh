#!bash

# Python
for schema in pipes/schema/*.schema.json; do
    quicktype -s schema -l python -o pipes/src/python/dagster_pipes/$(basename $schema .schema.json).py $schema
done

# Java
for schema in pipes/schema/*.schema.json; do
    quicktype -s schema -l java -o pipes/src/java/dagster_pipes/$(basename $schema .schema.json).java $schema
done
