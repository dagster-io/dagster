#!/usr/bin/env python
# ruff: noqa: T201


import os
import sys

import assets_pandas_type_metadata.lib as bol

sys.path.append(os.path.join(os.path.dirname(__file__), "../../assets_pandas_type_metadata"))


path = bol.normalize_path("all_stocks_5yr.csv")
print(f"Downloading S&P 500 CSV data from {bol.SP500_CSV_URL} to {path}...")
bol.download_file(bol.SP500_CSV_URL, path)
print("Successful.")
