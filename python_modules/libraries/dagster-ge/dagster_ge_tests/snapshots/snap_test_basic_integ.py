# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_yielded_results_config_pandas 1'] = '''
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
