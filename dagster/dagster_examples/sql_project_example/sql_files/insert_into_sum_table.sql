INSERT INTO sum_table(num1, num2, sum)
SELECT num1, num2, num1 + num2 FROM num_table;