# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_yielded_results_config_pandas[hello_world_pandas_job_v2-./great_expectations] 1'] = '''
# Validation Results


  

## Overview
### **Expectation Suite:** **basic.warning**
 **Data asset:** **None**
 **Status:**  **Succeeded**





### Statistics


  
  
  

 |  |  |
 | ------------  | ------------ | 
Evaluated Expectations  | 11  
Successful Expectations  | 11  
Unsuccessful Expectations  | 0  
Success Percent  | 100%  



  

## Table-Level Expectations






  

 | Status | Expectation | Observed Value |
 | ------------  | ------------  | ------------ | 
✅  | **expect_table_row_count_to_be_between**(****{'max_value': 33, 'min_value': 27, 'result_format': {'result_format': 'SUMMARY'}}**)  | --  
✅  | **expect_table_column_count_to_equal**(****{'value': 3, 'result_format': {'result_format': 'SUMMARY'}}**)  | --  
✅  | **expect_table_columns_to_match_ordered_list**(****{\'column_list\': [\'Team\', \' "Payroll (millions)"\', \' "Wins"\'], \'result_format\': {\'result_format\': \'SUMMARY\'}}**)  | --  



  

##  "Payroll (millions)"






  

 | Status | Expectation | Observed Value |
 | ------------  | ------------  | ------------ | 
✅  | **expect_column_values_to_not_be_null**(****{\'column\': \' "Payroll (millions)"\', \'result_format\': {\'result_format\': \'SUMMARY\'}}**)  | --  
✅  | **expect_column_min_to_be_between**(****{\'column\': \' "Payroll (millions)"\', \'max_value\': 56.24, \'min_value\': 54.24, \'result_format\': {\'result_format\': \'SUMMARY\'}}**)  | --  
✅  | **expect_column_max_to_be_between**(****{\'column\': \' "Payroll (millions)"\', \'max_value\': 198.96, \'min_value\': 196.96, \'result_format\': {\'result_format\': \'SUMMARY\'}}**)  | --  
✅  | **expect_column_mean_to_be_between**(****{\'column\': \' "Payroll (millions)"\', \'max_value\': 99.01899999999998, \'min_value\': 97.01899999999998, \'result_format\': {\'result_format\': \'SUMMARY\'}}**)  | --  
✅  | **expect_column_median_to_be_between**(****{\'column\': \' "Payroll (millions)"\', \'max_value\': 86.75, \'min_value\': 84.75, \'result_format\': {\'result_format\': \'SUMMARY\'}}**)  | --  
✅  | **expect_column_quantile_values_to_be_between**(****{\'allow_relative_error\': False, \'column\': \' "Payroll (millions)"\', \'quantile_ranges\': {\'quantiles\': [0.05, 0.25, 0.5, 0.75, 0.95], \'value_ranges\': [[54.37, 56.37], [74.48, 76.48], [82.31, 84.31], [116.62, 118.62], [173.54, 175.54]]}, \'result_format\': {\'result_format\': \'SUMMARY\'}}**)  | --  



  

## Team






  

 | Status | Expectation | Observed Value |
 | ------------  | ------------  | ------------ | 
✅  | **expect_column_values_to_not_be_null**(****{'column': 'Team', 'result_format': {'result_format': 'SUMMARY'}}**)  | --  
✅  | **expect_column_value_lengths_to_be_between**(****{'column': 'Team', 'min_value': 1, 'result_format': {'result_format': 'SUMMARY'}}**)  | --  



  



'''

snapshots['test_yielded_results_config_pandas[hello_world_pandas_job_v3-./great_expectations_v3] 1'] = '''
# Validation Results


  

## Overview
### **Expectation Suite:** **basic.warning**
 **Data asset:** **getest**
 **Status:**  **Succeeded**





### Statistics


  
  
  

 |  |  |
 | ------------  | ------------ | 
Evaluated Expectations  | 11  
Successful Expectations  | 11  
Unsuccessful Expectations  | 0  
Success Percent  | 100%  



  

## Table-Level Expectations






  

 | Status | Expectation | Observed Value |
 | ------------  | ------------  | ------------ | 
✅  | Must have greater than or equal to **27** and less than or equal to **33** rows.  | 30  
✅  | Must have exactly **3** columns.  | 3  
✅  | Must have these columns in this order: **Team**, ** "Payroll (millions)"**, ** "Wins"**  | [\'Team\', \' "Payroll (millions)"\', \' "Wins"\']  



  

##  "Payroll (millions)"






  

 | Status | Expectation | Observed Value |
 | ------------  | ------------  | ------------ | 
✅  | values must never be null.  | 100% not null  
✅  | minimum value must be greater than or equal to **54.24** and less than or equal to **56.24**.  | 55.24  
✅  | maximum value must be greater than or equal to **196.96** and less than or equal to **198.96**.  | 197.96  
✅  | mean must be greater than or equal to **97.01899999999998** and less than or equal to **99.01899999999998**.  | ≈98.019  
✅  | median must be greater than or equal to **84.75** and less than or equal to **86.75**.  | 85.75  
✅  | quantiles must be within the following value ranges.


  

 | Quantile | Min Value | Max Value |
 | ------------  | ------------  | ------------ | 
0.05  | 54.37  | 56.37  
Q1  | 74.48  | 76.48  
Median  | 82.31  | 84.31  
Q3  | 116.62  | 118.62  
0.95  | 173.54  | 175.54  
  | 


  

 | Quantile | Value |
 | ------------  | ------------ | 
0.05  | 55.37  
Q1  | 75.48  
Median  | 83.31  
Q3  | 117.62  
0.95  | 174.54  
  



  

## Team






  

 | Status | Expectation | Observed Value |
 | ------------  | ------------  | ------------ | 
✅  | values must never be null.  | 100% not null  
✅  | values must always be greater than or equal to **1** characters long.  | 0% unexpected  



  



'''

snapshots['test_yielded_results_config_pyspark_v2 1'] = '''
# Validation Results


  

## Overview
### **Expectation Suite:** **basic.warning**
 **Data asset:** **None**
 **Status:**  **Succeeded**





### Statistics


  
  
  

 |  |  |
 | ------------  | ------------ | 
Evaluated Expectations  | 11  
Successful Expectations  | 11  
Unsuccessful Expectations  | 0  
Success Percent  | 100%  



  

## Table-Level Expectations






  

 | Status | Expectation | Observed Value |
 | ------------  | ------------  | ------------ | 
✅  | Must have greater than or equal to **27** and less than or equal to **33** rows.  | 30  
✅  | Must have exactly **3** columns.  | 3  
✅  | Must have these columns in this order: **Team**, ** "Payroll (millions)"**, ** "Wins"**  | [\'Team\', \' "Payroll (millions)"\', \' "Wins"\']  



  

##  "Payroll (millions)"






  

 | Status | Expectation | Observed Value |
 | ------------  | ------------  | ------------ | 
✅  | values must never be null.  | 100% not null  
✅  | minimum value must be greater than or equal to **54.24** and less than or equal to **56.24**.  | 55.24  
✅  | maximum value must be greater than or equal to **196.96** and less than or equal to **198.96**.  | 197.96  
✅  | mean must be greater than or equal to **97.01899999999998** and less than or equal to **99.01899999999998**.  | 98.019  
✅  | median must be greater than or equal to **84.75** and less than or equal to **86.75**.  | 85.75  
✅  | quantiles must be within the following value ranges.


  

 | Quantile | Min Value | Max Value |
 | ------------  | ------------  | ------------ | 
0.05  | 54.37  | 56.37  
Q1  | 74.48  | 76.48  
Median  | 82.31  | 84.31  
Q3  | 116.62  | 118.62  
0.95  | 173.54  | 175.54  
  | 


  

 | Quantile | Value |
 | ------------  | ------------ | 
0.05  | 55.37  
Q1  | 75.48  
Median  | 83.31  
Q3  | 117.62  
0.95  | 174.54  
  



  

## Team






  

 | Status | Expectation | Observed Value |
 | ------------  | ------------  | ------------ | 
✅  | values must never be null.  | 100% not null  
✅  | values must always be greater than or equal to **1** characters long.  | 0% unexpected  



  



'''
