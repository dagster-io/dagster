#!/usr/bin/env python

import os

import requests

DATA_URL = "https://raw.githubusercontent.com/plotly/datasets/master/all_stocks_5yr.csv"

DATA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data")

TARGET_PATH = os.path.join(DATA_ROOT, "all_stocks_5yr.csv")

if not os.path.exists(DATA_ROOT):
    os.mkdir(DATA_ROOT)


with open(TARGET_PATH, "wb") as f:
    f.write(requests.get(DATA_URL).content)

print(f"Wrote to {TARGET_PATH}")
