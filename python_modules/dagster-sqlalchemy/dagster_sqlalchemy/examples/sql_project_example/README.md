This demonstrates what a potential project layout would be for a project that is a bunch of sql scripts.

This is **definitely** still on the rougher side but is an improvement:

Usage:

```
python3 pipelines.py
```

serves as the command line for this set of pipelines. Pipelines.py contains the code to construct the
various pipelines and calls into the command line tool if it is invoked as main.

Current _none_ of the pipelines take any arguments. This is simple front-end for running a set of dags.

```
$ python3 pipelines.py pipelines
*** All Pipelines ***
Pipeline: full_pipeline Description: Runs entire pipeline, both setup and running the transform
Pipeline: setup_pipeline Description: Creates all tables and then populates source table
Pipeline: truncate_all_derived_tables Description: Truncates all tables that are populated by the pipeline. Preserves source tables
Pipeline: rerun_pipeline Description: Rerun the pipeline, populating the the derived tables. Assumes pipeline is setup
```

So there are four pipelines that you can script. Descriptions are provided by the developer and exposed to tooling.

Let's use graphviz to see what is going on:

```
$ python3 pipelines.py graphviz full_pipeline
```

This will display a graph showing a serial dag.

create_all_tables --> populate_num_table --> insert_into_sum_table --> insert_into_sum_sq_table

Don't run one. Let's do a more realistic workflow

```
$ python3 pipelines.py graphviz setup_pipeline
```

create_all_tables --> populate_num_table

Cool.

Let's run it.

```
$ python3 pipelines.py execute setup_pipeline
```

There's a script checked in, print_tables.py, that prints the table. More realistically this would be invoked in a notebooking context.

```
$ python3 print_tables.py
num_table
   num1  num2
0     1     2
1     3     4
sum_table
Empty DataFrame
Columns: [num1, num2, sum]
Index: []
sum_sq_table
Empty DataFrame
Columns: [num1, num2, sum, sum_sq]
Index: []
```

So there are three tables. The source table has stuff. The two tables to be created are empty. Ok.

rerun_pipeline does the actual pipeline

Let's check it out in graphviz before we run it.

```
$ python3 pipelines.py graphviz rerun_pipeline
```

insert_into_sum_table --> insert_into_sum_sq_table

That seems right. Let's run it.

```
$ python3 pipelines.py execute rerun_pipeline
```

This should print some log spew to indicate that stuff happened.

Let's print it out.

```
$ python3 print_tables.py
num_table
   num1  num2
0     1     2
1     3     4
sum_table
   num1  num2  sum
0     1     2    3
1     3     4    7
sum_sq_table
   num1  num2  sum  sum_sq
0     1     2    3       9
1     3     4    7      49
```

Stuff was populated. Yay.

Now we can clear it

```
$ python3 pipelines.py execute truncate_all_derived_tables
```

Reprint the tables you'll see they are empty. Now you can edit your scripts and rerun things.
