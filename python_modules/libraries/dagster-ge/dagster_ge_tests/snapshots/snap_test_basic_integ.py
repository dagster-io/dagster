# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_yielded_results_config_pandas[hello_world_pandas_pipeline_v2-./great_expectations] 1'] = '''
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

snapshots['test_yielded_results_config_pandas[hello_world_pandas_pipeline_v3-./great_expectations_v3] 1'] = '''
 #   V a l i d a t i o n   R e s u l t s 
 
 
     
 
 # #   O v e r v i e w 
 # # #   * * E x p e c t a t i o n   S u i t e : * *   * * b a s i c . w a r n i n g * * 
   * * D a t a   a s s e t : * *   * * g e t e s t * * 
   * * S t a t u s : * *     * * S u c c e e d e d * * 
 
 
 
 
 
 # # #   S t a t i s t i c s 
 
 
     
     
     
 
   |     |     | 
   |   - - - - - - - - - - - -     |   - - - - - - - - - - - -   |   
 E v a l u a t e d   E x p e c t a t i o n s     |   1 1     
 S u c c e s s f u l   E x p e c t a t i o n s     |   1 1     
 U n s u c c e s s f u l   E x p e c t a t i o n s     |   0     
 S u c c e s s   P e r c e n t     |   1 0 0 %     
 
 
 
     
 
 # #   T a b l e - L e v e l   E x p e c t a t i o n s 
 
 
 
 
 
 
     
 
   |   S t a t u s   |   E x p e c t a t i o n   |   O b s e r v e d   V a l u e   | 
   |   - - - - - - - - - - - -     |   - - - - - - - - - - - -     |   - - - - - - - - - - - -   |   
 ✅     |   M u s t   h a v e   g r e a t e r   t h a n   o r   e q u a l   t o   * * 2 7 * *   a n d   l e s s   t h a n   o r   e q u a l   t o   * * 3 3 * *   r o w s .     |   3 0     
 ✅     |   M u s t   h a v e   e x a c t l y   * * 3 * *   c o l u m n s .     |   3     
 ✅     |   M u s t   h a v e   t h e s e   c o l u m n s   i n   t h i s   o r d e r :   * * T e a m * * ,   * *   " P a y r o l l   ( m i l l i o n s ) " * * ,   * *   " W i n s " * *     |   [ \' T e a m \' ,   \'   " P a y r o l l   ( m i l l i o n s ) " \' ,   \'   " W i n s " \' ]     
 
 
 
     
 
 # #     " P a y r o l l   ( m i l l i o n s ) " 
 
 
 
 
 
 
     
 
   |   S t a t u s   |   E x p e c t a t i o n   |   O b s e r v e d   V a l u e   | 
   |   - - - - - - - - - - - -     |   - - - - - - - - - - - -     |   - - - - - - - - - - - -   |   
 ✅     |   v a l u e s   m u s t   n e v e r   b e   n u l l .     |   1 0 0 %   n o t   n u l l     
 ✅     |   m i n i m u m   v a l u e   m u s t   b e   g r e a t e r   t h a n   o r   e q u a l   t o   * * 5 4 . 2 4 * *   a n d   l e s s   t h a n   o r   e q u a l   t o   * * 5 6 . 2 4 * * .     |   5 5 . 2 4     
 ✅     |   m a x i m u m   v a l u e   m u s t   b e   g r e a t e r   t h a n   o r   e q u a l   t o   * * 1 9 6 . 9 6 * *   a n d   l e s s   t h a n   o r   e q u a l   t o   * * 1 9 8 . 9 6 * * .     |   1 9 7 . 9 6     
 ✅     |   m e a n   m u s t   b e   g r e a t e r   t h a n   o r   e q u a l   t o   * * 9 7 . 0 1 8 9 9 9 9 9 9 9 9 9 9 8 * *   a n d   l e s s   t h a n   o r   e q u a l   t o   * * 9 9 . 0 1 8 9 9 9 9 9 9 9 9 9 9 8 * * .     |   ≈ 9 8 . 0 1 9     
 ✅     |   m e d i a n   m u s t   b e   g r e a t e r   t h a n   o r   e q u a l   t o   * * 8 4 . 7 5 * *   a n d   l e s s   t h a n   o r   e q u a l   t o   * * 8 6 . 7 5 * * .     |   8 5 . 7 5     
 ✅     |   q u a n t i l e s   m u s t   b e   w i t h i n   t h e   f o l l o w i n g   v a l u e   r a n g e s . 
 
 
     
 
   |   Q u a n t i l e   |   M i n   V a l u e   |   M a x   V a l u e   | 
   |   - - - - - - - - - - - -     |   - - - - - - - - - - - -     |   - - - - - - - - - - - -   |   
 0 . 0 5     |   5 4 . 3 7     |   5 6 . 3 7     
 Q 1     |   7 4 . 4 8     |   7 6 . 4 8     
 M e d i a n     |   8 2 . 3 1     |   8 4 . 3 1     
 Q 3     |   1 1 6 . 6 2     |   1 1 8 . 6 2     
 0 . 9 5     |   1 7 3 . 5 4     |   1 7 5 . 5 4     
     |   
 
 
     
 
   |   Q u a n t i l e   |   V a l u e   | 
   |   - - - - - - - - - - - -     |   - - - - - - - - - - - -   |   
 0 . 0 5     |   5 5 . 3 7     
 Q 1     |   7 5 . 4 8     
 M e d i a n     |   8 3 . 3 1     
 Q 3     |   1 1 7 . 6 2     
 0 . 9 5     |   1 7 4 . 5 4     
     
 
 
 
     
 
 # #   T e a m 
 
 
 
 
 
 
     
 
   |   S t a t u s   |   E x p e c t a t i o n   |   O b s e r v e d   V a l u e   | 
   |   - - - - - - - - - - - -     |   - - - - - - - - - - - -     |   - - - - - - - - - - - -   |   
 ✅     |   v a l u e s   m u s t   n e v e r   b e   n u l l .     |   1 0 0 %   n o t   n u l l     
 ✅     |   v a l u e s   m u s t   a l w a y s   b e   g r e a t e r   t h a n   o r   e q u a l   t o   * * 1 * *   c h a r a c t e r s   l o n g .     |   0 %   u n e x p e c t e d     
 
 
 
     
 
 
 
 # # #   I n f o 
 
 
     
     
     
 
   |     |     | 
   |   - - - - - - - - - - - -     |   - - - - - - - - - - - -   |   
 G r e a t   E x p e c t a t i o n s   V e r s i o n     |   0 . 1 3 . 3 1     
 R u n   N a m e     |   g e t e s t   r u n     
 R u n   T i m e     |   2 0 2 1 - 0 8 - 2 7 T 2 0 : 3 5 : 4 1 Z     
 
 
 
 
 
 # # #   B a t c h   M a r k e r s 
 
 
     
     
     
 
   |     |     | 
   |   - - - - - - - - - - - -     |   - - - - - - - - - - - -   |   
 * * g e _ l o a d _ t i m e * *     |   * * 2 0 2 1 0 8 2 7 T 2 0 3 5 4 1 . 8 5 6 8 3 2 Z * *     
 * * p a n d a s _ d a t a _ f i n g e r p r i n t * *     |   * * 8 c 4 6 f d a f 0 b d 3 5 6 f d 5 8 b 7 b c d 9 b 2 e 6 0 1 2 d * *     
 
 
 
 
 
 # # #   B a t c h   S p e c 
 
 
     
     
     
 
   |     |     | 
   |   - - - - - - - - - - - -     |   - - - - - - - - - - - -   |   
 * * b a t c h _ d a t a * *     |   * * P a n d a s D a t a F r a m e * *     
 * * d a t a _ a s s e t _ n a m e * *     |   * * g e t e s t * *     
 
 
 
 
 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
 P o w e r e d   b y   [ G r e a t   E x p e c t a t i o n s ] ( h t t p s : / / g r e a t e x p e c t a t i o n s . i o / )'''
