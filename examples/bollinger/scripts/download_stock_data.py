#!/usr/bin/env python

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../bollinger'))

import bollinger.lib as bol

path = bol.normalize_path("all_stocks_5yr.csv")
print(f"Downloading S&P 500 CSV data from {bol.SP500_CSV_URL} to {path}...")
bol.download_file(bol.SP500_CSV_URL, path)
print("Successful.")
