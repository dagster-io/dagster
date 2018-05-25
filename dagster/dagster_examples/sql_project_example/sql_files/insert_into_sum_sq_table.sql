INSERT INTO sum_sq_table(num1, num2, sum, sum_sq)
SELECT num1, num2, sum, sum * sum FROM sum_table;