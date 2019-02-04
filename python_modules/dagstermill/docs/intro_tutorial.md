## Dagstermill Tutorial

A wonderful feature of using Dagster is that you can productionize Jupyter notebooks and involve them in a (production) pipeline as units of computation. 

There are a few stages of data scientists using notebooks in the wild. 
1. Unstructured scratch work, cells are often run out of order
2. More refined prototyping, where cells are run sequentially. Usually the top cells contain inputs and / or parameters that are used in later cells. 
3. Pieces of re-usable code are extracted from a notebook, turned into functions and put in a script (`.py` file)

Typically, only stage 3 would be involved in a production pipeline. However, with dagstermill, if you have a notebook in stage 2 (i.e. the cells run sequentially to produce the desired output), with minimal effort you can register this notebook as a solid in the pipeline and use the entire notebook as a unit of computation in your pipeline that takes in inputs and produces outputs (that can be consumed by later stages of the pipeline).

---
### An Example Pipeline with a Notebook

Say you have a pipeline as shown below:

**TODO**

This is a very simple pipeline, where the solid `return_one` returns 1 and `return_two` returns 2. Say you have a notebook with the following cells that you want to incorporate in your pipeline.

**TODO** make this HTML

```
a = 3
b = 5
```
```
result = a + b
```
Your notebook is effectively a function that takes in inputs `a` and `b` and products output `result`. To use the language of the dagster abstraction, it is a solid with inputs `a`, `b` of dagster-type `Int` and with an ouput `result` of type `Int`. 

To register this notebook as a dagster solid, we use the following lines of code.

```
from dagster import InputDefinition, OutputDefinition, Int
import dagstermill as dm

my_notebook_solid = dm.define_dagstermill_solid(
                            name='add_two_numbers',
                            notebook_path='/path/to/notebook/add_two_numbers.ipynb',
                            inputs = [InputDefinition(name='a', dagster_type=Int),
                            InputDefinition('b', Int)],
                            ouputs = [OutputDefinition(Int)]
                            )
```

The `define_dagstermill_solid` returns an object of type `SolidDefinition` that can be passed into `PipelineDefinition` objects. We see that its arguments are rather self-explanatory: 
* `name`: the name of the solid 
* `notebook_path`: the location of the notebook so that the dagster execution engine can run the code in the notebook
* `inputs`, `outputs`: the named and typed inputs and ouputs of the notebook as a solid

However, we also have to add some boilerplate to the notebook itself to make sure it plays nice with the dagstermill framework. In particular, we must make sure the notebook has code right at the start that
* imports the dagstermill library as dm
* calls `dm.declare_as_solid(repository_defn, solid_name)`, where `repository_defn` argument is a repository definition and the `solid_name` is the name of the solid in the pipeline that the notebook is in.

Finally, we move all parameters in the notebook that are inputs into the solid (so any field that is an `InputDefinition`) into the 2nd cell of the notebook (right after the import cell) and tag the cell with the label `parameters`. Dagstermill works by auto-injecting a cell that replaces the `parameters`-tagged cell at runtime with the runtime value of the parameters, thus it is crucial that the parameters tagged cell contains *only* the parameters that are inputs into the notebook solid (otherwise they will not be instantiated). The final `dagstermill`-ready version of the notebook looks like this:

**TODO**

There is a helpful `dagstermill` CLI that you can use to generate notebooks that will automatically contain the requisite boilerplate. The tutorial for the dagstermill CLI is at the end of this README.

---
### Output Notebooks

The way dagstermill works is by auto-injecting a cell that replaces the `parameters`-tagged cell with the runtime values of the inputs and then running the notebook using the papermill library (at <https://github.com/nteract/papermill>). A nice side-effect of using the papermill library to run the notebook is that the output is contained in an "output notebook", whereas the source notebook remains unchanged. However, since the output notebook is itself a valid Jupyter notebook, debugging can be done within the notebook context! Within dagit, after a solid that is a notebook has run, we provide a link to the output notebook, as seen below so that you can examine and play around with the output as needed (without modifying the source notebook).

**TODO: dagit picture**

---
## Dagstermill CLI
**TODO**






