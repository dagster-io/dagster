This project is to be used with the [Deploy to Kubernetes](/todo) guide.

The Dagster project is found in `iris_analysis` and contains a single file `definitions.py`. This file defines an asset `iris_dataset_size` that fetches a dataset about irises and logs the number of rows in the dataset. A `Definitions` object is defined that will allow Dagster to load the `iris_dataset_size` asset.
