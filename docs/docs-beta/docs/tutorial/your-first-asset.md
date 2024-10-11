---
title: Your First Asset 
description: Get the project data and create your first Asset
last_update:
  date: 2024-10-11
  author: Alex Noonan
---

# Copying Data Files

Before you can make your first Dagster Asset you need to copy the raw data files. 

1. Create a new folder for the raw data:

   ```bash title="Create the data directory"
   mkdir data
   cd data
   ```

2. Copy the raw csv files:

   ```bash title="Copy the csv files"
   curl -L -o products.csv https://raw.githubusercontent.com/dagster-io/dagster/refs/heads/master/examples/docs_beta_snippets/docs_beta_snippets/guides/tutorials/etl_tutorial/data/products.csv

   curl -L -o sales_reps.csv https://raw.githubusercontent.com/dagster-io/dagster/refs/heads/master/examples/docs_beta_snippets/docs_beta_snippets/guides/tutorials/etl_tutorial/data/sales_reps.csv

   curl -L -o sales_data.csv https://raw.githubusercontent.com/dagster-io/dagster/refs/heads/master/examples/docs_beta_snippets/docs_beta_snippets/guides/tutorials/etl_tutorial/data/sales_data.csv

   source venv/bin/activate
   # On Windows, use `venv\Scripts\activate` check this
   
   ```
3. Copy Sample Request json file

   ```bash title="Create the sample request"
   mkdir sample_request
   cd sample_request
   curl -L -o request.json https://raw.githubusercontent.com/dagster-io/dagster/refs/heads/master/examples/docs_beta_snippets/docs_beta_snippets/guides/tutorials/etl_tutorial/data/sample_request/request.json
   
   # navigating back to the root directory
   cd../..
   ```

# Next we will create our Python Definitions file 