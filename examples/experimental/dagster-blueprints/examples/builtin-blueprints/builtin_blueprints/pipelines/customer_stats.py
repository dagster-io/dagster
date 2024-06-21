import pandas as pd

customers = pd.read_csv("../../data/customers.csv")

num_customers = customers.shape[0]
num_steves = customers[customers["FIRST_NAME"] == "Steve"].shape[0]
customer_stats = pd.DataFrame({"num_customers": [num_customers], "num_steves": [num_steves]})

customer_stats.to_csv("../../data/customer_stats.csv", index=False)
