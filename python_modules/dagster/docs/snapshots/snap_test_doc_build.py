# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_build_all_docs 1'] = [
    (
        '.',
        [
            'html',
            'doctrees'
        ],
        [
        ]
    ),
    (
        './html',
        [
            'intro_tutorial',
            '_sources',
            '_static',
            '_images',
            'apidocs'
        ],
        [
            'principles.html',
            'index.html',
            'searchindex.js',
            'py-modindex.html',
            '.buildinfo',
            'genindex.html',
            'contributing.html',
            'search.html',
            'installation.html'
        ]
    ),
    (
        './html/intro_tutorial',
        [
        ],
        [
            'hello_dag.html',
            'repos.html',
            'pipeline_execution.html',
            'part_ten.html',
            'execution_context.html',
            'actual_dag.html',
            'part_eleven.html',
            'inputs.html',
            'part_twelve.html',
            'configuration_schemas.html',
            'part_thirteen.html',
            'config.html',
            'part_fourteen.html',
            'hello_world.html',
            'part_nine.html'
        ]
    ),
    (
        './html/_sources',
        [
            'intro_tutorial',
            'apidocs'
        ],
        [
            'installation.rst.txt',
            'principles.rst.txt',
            'contributing.rst.txt',
            'index.rst.txt'
        ]
    ),
    (
        './html/_sources/intro_tutorial',
        [
        ],
        [
            'part_eleven.rst.txt',
            'config.rst.txt',
            'execution_context.rst.txt',
            'inputs.rst.txt',
            'pipeline_execution.rst.txt',
            'part_twelve.rst.txt',
            'part_nine.rst.txt',
            'part_ten.rst.txt',
            'hello_world.rst.txt',
            'part_fourteen.rst.txt',
            'part_thirteen.rst.txt',
            'repos.rst.txt',
            'hello_dag.rst.txt',
            'actual_dag.rst.txt',
            'configuration_schemas.rst.txt'
        ]
    ),
    (
        './html/_sources/apidocs',
        [
        ],
        [
            'execution.rst.txt',
            'definitions.rst.txt',
            'utilities.rst.txt',
            'types.rst.txt',
            'decorators.rst.txt',
            'errors.rst.txt'
        ]
    ),
    (
        './html/_static',
        [
        ],
        [
            'plus.png',
            'down-pressed.png',
            'jquery-3.2.1.js',
            'underscore.js',
            'ajax-loader.gif',
            'alabaster.css',
            'documentation_options.js',
            'searchtools.js',
            'up.png',
            'file.png',
            'up-pressed.png',
            'down.png',
            'custom.css',
            'underscore-1.3.1.js',
            'minus.png',
            'comment.png',
            'basic.css',
            'pygments.css',
            'comment-close.png',
            'doctools.js',
            'comment-bright.png',
            'websupport.js',
            'jquery.js'
        ]
    ),
    (
        './html/_images',
        [
        ],
        [
            'inputs_figure_two_untyped_execution.png',
            'hello_dag_figure_one.png',
            'hello_world_figure_two.png',
            'inputs_figure_three_error_modal.png',
            'config_figure_one.png',
            'repos_figure_one.png',
            'inputs_figure_one.png',
            'inputs_figure_four_error_prechecked.png',
            'hello_world_figure_one.png',
            'actual_dag_figure_one.png'
        ]
    ),
    (
        './html/apidocs',
        [
        ],
        [
            'decorators.html',
            'execution.html',
            'utilities.html',
            'definitions.html',
            'types.html',
            'errors.html'
        ]
    ),
    (
        './doctrees',
        [
            'intro_tutorial',
            'apidocs'
        ],
        [
            'installation.doctree',
            'principles.doctree',
            'contributing.doctree',
            'environment.pickle',
            'index.doctree'
        ]
    ),
    (
        './doctrees/intro_tutorial',
        [
        ],
        [
            'part_eleven.doctree',
            'config.doctree',
            'execution_context.doctree',
            'inputs.doctree',
            'pipeline_execution.doctree',
            'part_ten.doctree',
            'part_nine.doctree',
            'part_twelve.doctree',
            'part_fourteen.doctree',
            'hello_world.doctree',
            'part_thirteen.doctree',
            'repos.doctree',
            'configuration_schemas.doctree',
            'actual_dag.doctree',
            'hello_dag.doctree'
        ]
    ),
    (
        './doctrees/apidocs',
        [
        ],
        [
            'execution.doctree',
            'definitions.doctree',
            'types.doctree',
            'utilities.doctree',
            'decorators.doctree',
            'errors.doctree'
        ]
    )
]

snapshots['test_build_all_docs 2'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Principles &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="./" src="_static/documentation_options.js"></script>
    <script type="text/javascript" src="_static/jquery.js"></script>
    <script type="text/javascript" src="_static/underscore.js"></script>
    <script type="text/javascript" src="_static/doctools.js"></script>
    <link rel="index" title="Index" href="genindex.html" />
    <link rel="search" title="Search" href="search.html" />
    <link rel="next" title="Installation" href="installation.html" />
    <link rel="prev" title="Intro Tutorial" href="index.html" />
   
  <link rel="stylesheet" href="_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="principles">
<h1>Principles<a class="headerlink" href="#principles" title="Permalink to this headline">¶</a></h1>
<p>Dagster is opinionated about how data pipelines should be built and structured. What do we think
is important?</p>
<div class="section" id="functional">
<h2>Functional<a class="headerlink" href="#functional" title="Permalink to this headline">¶</a></h2>
<p>Data pipelines should be expressed as DAGs (directed acyclic graphs) of functional, idempotent
computations. Individual nodes in the graph consume their inputs, perform some computation, and
yield outputs, either with no side effects or with clealy advertised side effects. Given the
same inputs and configuration, the computation should always produce the same output. If these
computations have external dependencies, these should be parametrizable, so that the computations
may execute in different environments.</p>
<blockquote>
<div><ul class="simple">
<li>See Maxime Beauchemin’s Medium article on <a class="reference external" href="https://bit.ly/2LxDgnr">Functional Data Engineering</a>
for an excellent overview of functional programing in batch computations.</li>
</ul>
</div></blockquote>
</div>
<div class="section" id="self-describing">
<h2>Self-describing<a class="headerlink" href="#self-describing" title="Permalink to this headline">¶</a></h2>
<p>Data pipelines should be self-describing, with rich metadata and types. Users should be able to
approach an unfamiliar pipeline and use tooling to inspect it and discover its structure,
capabilities, and requirements. Pipeline metadata should be co-located with the pipeline’s actual
code: documentation and code should be delivered as a single artifact.</p>
</div>
<div class="section" id="compute-agnostic">
<h2>Compute-agnostic<a class="headerlink" href="#compute-agnostic" title="Permalink to this headline">¶</a></h2>
<p>Heterogeneity in data pipelines is the norm, rather than the exception. Data pipelines are written
collaboratively by many people in different personas – data engineers, machine-learning engineers,
data scientists, analysts and so on – who have different needs and tools, and are particular about
those tools.</p>
<p>Dagster has opinions about best practices for structuring data pipelines. It has no opinions
about what libraries and engines should do actual compute. Dagster pipelines can be made up of
any Python computations, whether they use Pandas, Spark, or call out to SQL or any other DSL or
library deemed appropriate to the task.</p>
</div>
<div class="section" id="testable">
<h2>Testable<a class="headerlink" href="#testable" title="Permalink to this headline">¶</a></h2>
<p>Testing data pipelines is notoriously difficult. Because testing is so difficult, it is often never
done, or done poorly. Dagster pipelines are designed to be tested. Dagster provides explicit support
for pipeline authors to manage and maintain multiple execution environments – for example, unit
testing, integration testing, and production environments. Dagster can also execute arbitrary
subsets and nodes of pipelines, which is critical for testability (and useful in operational
contexts as well).</p>
</div>
<div class="section" id="verifiable-data-quality">
<h2>Verifiable data quality<a class="headerlink" href="#verifiable-data-quality" title="Permalink to this headline">¶</a></h2>
<p>Testing code is important in data pipelines, but it is not sufficient. Data quality tests – run
during every meaningful stage of computation in production – are critical to reduce the
maintenance burden of data pipelines. Pipeline authors generally do not have control over their
input data, and make many implicit assumptions about that data. Data formats can also change
over time. In order to control this entropy, Dagster encourages users to computationally verify
assumptions (known as expectations) about the data as part of the pipeline process. This way, when
those assumptions break, the breakage can be reported quickly, easily, and with rich metadata
and diagnostic information. These expectations can also serve as contracts between teams.</p>
<blockquote>
<div><ul class="simple">
<li>See <a class="reference external" href="https://bit.ly/2mxDS1R">https://bit.ly/2mxDS1R</a> for a primer on pipeline tests for data quality.</li>
</ul>
</div></blockquote>
</div>
<div class="section" id="gradual-optional-typing">
<h2>Gradual, optional typing<a class="headerlink" href="#gradual-optional-typing" title="Permalink to this headline">¶</a></h2>
<p>Dagster contains a type system to describe the values flowing through the pipeline and the
configuration of the pipeline. As pipelines mature, gradual typing lets nodes in a pipeline
know if they are properly arranged and configured prior to execution, and provides rich
documentation and runtime error checking.</p>
</div>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="index.html">Table Of Contents</a></h3>
<ul class="current">
<li class="toctree-l1 current"><a class="current reference internal" href="#">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="contributing.html">Contributing</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="index.html">Documentation overview</a><ul>
      <li>Previous: <a href="index.html" title="previous chapter">Intro Tutorial</a></li>
      <li>Next: <a href="installation.html" title="next chapter">Installation</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="_sources/principles.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="_sources/principles.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 3'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Intro Tutorial &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="./" src="_static/documentation_options.js"></script>
    <script type="text/javascript" src="_static/jquery.js"></script>
    <script type="text/javascript" src="_static/underscore.js"></script>
    <script type="text/javascript" src="_static/doctools.js"></script>
    <link rel="index" title="Index" href="genindex.html" />
    <link rel="search" title="Search" href="search.html" />
    <link rel="next" title="Principles" href="principles.html" />
   
  <link rel="stylesheet" href="_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <img alt="https://user-images.githubusercontent.com/28738937/44878798-b6e17e00-ac5c-11e8-8d25-2e47e5a53418.png" class="align-center" src="https://user-images.githubusercontent.com/28738937/44878798-b6e17e00-ac5c-11e8-8d25-2e47e5a53418.png" />
<p>Welcome to Dagster, an opinionated programming model for data pipelines.</p>
<div class="toctree-wrapper compound" id="documentation">
<ul>
<li class="toctree-l1"><a class="reference internal" href="principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="contributing.html">Contributing</a></li>
</ul>
</div>
<div class="section" id="intro-tutorial">
<h1>Intro Tutorial<a class="headerlink" href="#intro-tutorial" title="Permalink to this headline">¶</a></h1>
<div class="toctree-wrapper compound" id="id1">
<ul>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
</div>
</div>
<div class="section" id="api-reference">
<h1>API Reference<a class="headerlink" href="#api-reference" title="Permalink to this headline">¶</a></h1>
<div class="toctree-wrapper compound" id="id2">
<ul>
<li class="toctree-l1"><a class="reference internal" href="apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/utilities.html">Utilities</a></li>
</ul>
</div>
</div>
<div class="section" id="indices-and-tables">
<h1>Indices and tables<a class="headerlink" href="#indices-and-tables" title="Permalink to this headline">¶</a></h1>
<ul class="simple">
<li><a class="reference internal" href="genindex.html"><span class="std std-ref">Index</span></a></li>
<li><a class="reference internal" href="py-modindex.html"><span class="std std-ref">Module Index</span></a></li>
<li><a class="reference internal" href="search.html"><span class="std std-ref">Search Page</span></a></li>
</ul>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="#">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="contributing.html">Contributing</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="#">Documentation overview</a><ul>
      <li>Next: <a href="principles.html" title="next chapter">Principles</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="_sources/index.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="_sources/index.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 4'] = 'Search.setIndex({docnames:["apidocs/decorators","apidocs/definitions","apidocs/errors","apidocs/execution","apidocs/types","apidocs/utilities","contributing","index","installation","intro_tutorial/actual_dag","intro_tutorial/config","intro_tutorial/configuration_schemas","intro_tutorial/execution_context","intro_tutorial/hello_dag","intro_tutorial/hello_world","intro_tutorial/inputs","intro_tutorial/part_eleven","intro_tutorial/part_fourteen","intro_tutorial/part_nine","intro_tutorial/part_ten","intro_tutorial/part_thirteen","intro_tutorial/part_twelve","intro_tutorial/pipeline_execution","intro_tutorial/repos","principles"],envversion:53,filenames:["apidocs/decorators.rst","apidocs/definitions.rst","apidocs/errors.rst","apidocs/execution.rst","apidocs/types.rst","apidocs/utilities.rst","contributing.rst","index.rst","installation.rst","intro_tutorial/actual_dag.rst","intro_tutorial/config.rst","intro_tutorial/configuration_schemas.rst","intro_tutorial/execution_context.rst","intro_tutorial/hello_dag.rst","intro_tutorial/hello_world.rst","intro_tutorial/inputs.rst","intro_tutorial/part_eleven.rst","intro_tutorial/part_fourteen.rst","intro_tutorial/part_nine.rst","intro_tutorial/part_ten.rst","intro_tutorial/part_thirteen.rst","intro_tutorial/part_twelve.rst","intro_tutorial/pipeline_execution.rst","intro_tutorial/repos.rst","principles.rst"],objects:{"dagster.DependencyDefinition":{description:[1,2,1,""],output:[1,2,1,""],solid:[1,2,1,""]},"dagster.ExpectationDefinition":{description:[1,2,1,""],expectation_fn:[1,2,1,""],name:[1,2,1,""]},"dagster.ExpectationResult":{message:[1,2,1,""],result_context:[1,2,1,""],success:[1,2,1,""]},"dagster.Field":{config_type:[1,2,1,""],default_provided:[1,2,1,""],default_value:[1,2,1,""],description:[1,2,1,""],is_optional:[1,2,1,""]},"dagster.InputDefinition":{description:[1,2,1,""],expectations:[1,2,1,""],name:[1,2,1,""],runtime_type:[1,2,1,""]},"dagster.MultipleResults":{from_dict:[0,3,1,""],results:[0,2,1,""]},"dagster.OutputDefinition":{description:[1,2,1,""],name:[1,2,1,""],runtime_type:[1,2,1,""]},"dagster.PipelineContextDefinition":{passthrough_context_definition:[1,3,1,""]},"dagster.PipelineDefinition":{context_definitions:[1,2,1,""],dependencies:[1,2,1,""],dependency_structure:[1,2,1,""],description:[1,2,1,""],display_name:[1,2,1,""],has_solid:[1,4,1,""],name:[1,2,1,""],solid_named:[1,4,1,""],solids:[1,2,1,""]},"dagster.PipelineExecutionResult":{context:[3,2,1,""],pipeline:[3,2,1,""],result_for_solid:[3,4,1,""],result_list:[3,2,1,""],success:[3,2,1,""]},"dagster.RepositoryDefinition":{get_all_pipelines:[1,4,1,""],get_pipeline:[1,4,1,""],iterate_over_pipelines:[1,4,1,""],name:[1,2,1,""],pipeline_dict:[1,2,1,""]},"dagster.Result":{output_name:[1,2,1,""],value:[1,2,1,""]},"dagster.SolidDefinition":{config_field:[1,2,1,""],description:[1,2,1,""],input_defs:[1,2,1,""],metadata:[1,2,1,""],name:[1,2,1,""],outputs_defs:[1,2,1,""],transform_fn:[1,2,1,""]},"dagster.SolidExecutionResult":{context:[3,2,1,""],dagster_error:[3,2,1,""],solid:[3,2,1,""],success:[3,2,1,""],transformed_value:[3,4,1,""],transformed_values:[3,2,1,""]},"dagster.TransformExecutionInfo":{config:[1,2,1,""],context:[1,2,1,""]},"dagster.core":{types:[4,5,0,"-"]},"dagster.core.types":{Any:[4,2,1,""],Bool:[4,2,1,""],Int:[4,2,1,""],List:[4,6,1,""],Nullable:[4,6,1,""],Path:[4,2,1,""],PythonObjectType:[4,0,1,""],String:[4,2,1,""]},dagster:{ContextCreationExecutionInfo:[1,0,1,""],DagsterExpectationFailedError:[2,1,1,""],DagsterInvalidDefinitionError:[2,1,1,""],DagsterInvariantViolationError:[2,1,1,""],DagsterRuntimeCoercionError:[2,1,1,""],DagsterTypeError:[2,1,1,""],DagsterUserCodeExecutionError:[2,1,1,""],DependencyDefinition:[1,0,1,""],ExecutionContext:[3,0,1,""],ExpectationDefinition:[1,0,1,""],ExpectationExecutionInfo:[1,0,1,""],ExpectationResult:[1,0,1,""],Field:[1,0,1,""],InputDefinition:[1,0,1,""],MultipleResults:[0,0,1,""],OutputDefinition:[1,0,1,""],PipelineConfigEvaluationError:[3,1,1,""],PipelineContextDefinition:[1,0,1,""],PipelineDefinition:[1,0,1,""],PipelineExecutionResult:[3,0,1,""],ReentrantInfo:[3,0,1,""],RepositoryDefinition:[1,0,1,""],ResourceDefinition:[1,0,1,""],Result:[1,0,1,""],SolidDefinition:[1,0,1,""],SolidExecutionResult:[3,0,1,""],SolidInstance:[1,0,1,""],TransformExecutionInfo:[1,0,1,""],define_stub_solid:[5,6,1,""],execute_pipeline:[3,6,1,""],execute_pipeline_iterator:[3,6,1,""],execute_solid:[5,6,1,""],lambda_solid:[0,6,1,""],solid:[0,6,1,""]}},objnames:{"0":["py","class","Python class"],"1":["py","exception","Python exception"],"2":["py","attribute","Python attribute"],"3":["py","staticmethod","Python static method"],"4":["py","method","Python method"],"5":["py","module","Python module"],"6":["py","function","Python function"]},objtypes:{"0":"py:class","1":"py:exception","2":"py:attribute","3":"py:staticmethod","4":"py:method","5":"py:module","6":"py:function"},terms:{"06c7":14,"0db53fdb":21,"1563854b":14,"183c":21,"18adec0afdfc":21,"25faadf5":14,"2ee26bc76636":21,"2mxds1r":24,"408a":19,"40a9b608":12,"40ea":16,"424047dd":21,"42b8":16,"43f5":14,"44f6":12,"46cc":14,"477c":21,"47db":19,"48cda39e79a1":16,"497c9d47":12,"49eb":14,"49ef":16,"4aa0":12,"4ae2":14,"4b3f":19,"4d71":14,"4f15":12,"4f75":12,"571a":12,"583d":16,"5878513a":14,"5b233906":12,"5c829421":14,"604dc47c":14,"66b0b6ecdcad":19,"675f905d":21,"677247b1b07b":14,"6b80d12155de":16,"6d6dbe6b296b":16,"744a":14,"758f":14,"7d62dcbf":16,"7e828e37eab8":14,"7f4d":16,"80c2":19,"81ba":14,"88cb":14,"89211a12":12,"8b76":19,"8f24049b0f66":12,"938ab7fa":19,"941f":16,"95af":16,"95ef":16,"97ae58fda0f4":14,"9b36":12,"9ca21f5c":19,"9cbe4fa0f5e6":16,"9de556c1":16,"9f44":19,"9f4a":12,"\\u4e16\\u754c":10,"\\u4f60\\u597d":10,"abstract":1,"break":[6,24],"case":[1,10,11,12,13,15,17,19],"catch":[11,15],"class":[0,1,2,3,4,16,18,19,21],"default":[0,1,8,11,12,16,18,19,22,23],"final":[17,20,22],"function":[0,1,3,10,13,14,15,16,18,20,21,23],"import":[9,10,11,12,13,14,15,18,22,23,24],"instanceof":11,"int":[1,4,11,16,17,18,19,20,22],"long":23,"new":[6,8,12,13,17,18,23],"public":18,"return":[0,1,3,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],"short":21,"static":[0,1],"super":21,"switch":[8,10],"throw":[1,2,3,19],"true":[1,3,10],"try":[9,10,22,23],And:[8,11,12,15,18,19,20,21,22],But:[12,15,23],For:[1,3,6,8,10,12,15,16,21],Lying:19,One:[1,12,13,17,18,19,21],That:[10,11,21],The:[0,1,3,9,10,11,12,13,14,15,16,17,18,19,21,22],Then:[8,10,14],There:[1,14,20],These:[1,11,16,20,24],Used:1,Useful:0,Using:14,Was:1,With:[16,22],Yes:1,__fieldvaluesentinel:1,__inferoptionalcompositefieldsentinel:1,__init__:[18,21],__main__:[14,16,21],__name__:[14,16,21],_conn:18,_info:[1,16,18,19],_kei:18,_read_csv:1,_valu:18,a04c:12,a1d6:12,a220:12,a463:16,a531:14,a801:14,a850a1643b9f:12,a_plus_b:[17,20],aab70a2cb603:12,abil:[13,17,19],abl:[10,12,14,18,20,21,23,24],about:[1,10,12,13,19,22,24],abov:[12,16,18],accept:[1,18],access:[1,12,18],accomplish:18,acronym:1,across:[12,22],action:11,activ:[6,8],actual:[7,13,16,24],actual_dag:9,actual_dag_pipelin:9,acycl:[1,13,24],add:[14,18,19],add_hello_to_word:15,add_hello_to_word_typ:15,add_int:[18,19],added:19,adder:[17,20],adding:[12,19],addit:[0,10],addition:16,advertis:24,aed8162cc25c:16,af26:21,aff9:21,afford:10,after:9,again:[9,12,21],against:22,alia:[1,20],all:[1,3,10,14,15,16,23],allow:[0,1,3,12,13,16,18,22],aloha:10,along:17,alreadi:[8,17,21,23],also:[6,8,11,12,15,16,17,18,19,21,22,23,24],although:[12,23],alwai:[12,15,24],amazon:18,amount:21,anaconda:8,analyst:24,ani:[1,3,4,6,8,9,11,12,14,15,18,21,23,24],annot:[10,11,21],anoth:10,apach:6,api:[0,1,3,10,23],appli:[1,15],applic:[19,22],approach:24,appropri:[15,24],apt:8,arbitrari:[1,13,16,17,19,24],aren:8,arg:[2,3,4],arg_a:9,arg_b:9,arg_c:9,arg_on:13,argument:[0,1,2,10,13,15,16,22,23],aris:11,arithmet:[18,20],around:16,arrai:1,arrang:[1,14,24],arrow:6,articl:24,artifact:24,aspect:19,assert:[14,17,20],asset:[1,14],assign:15,associ:12,assum:[1,14],assumpt:[19,24],attach:[1,11,18,19],attent:9,attribut:[1,18],author:[1,12,13,18,24],auto:[6,15],automat:15,autoreload:6,avail:1,avoid:10,awar:19,b150:16,b27fb70a:14,b510:14,b5a8:14,b602e4409f74:14,b757:21,b85c:14,back:11,bad:18,bake:19,bar:[0,22],barb:0,bare:18,base:[15,16],bash:8,basi:[9,12],basic:12,batch:24,beauchemin:24,becaus:[6,9,12,15,16,18,19,21,24],becom:0,been:[2,16,17,20],befor:[9,11,12,15],begin:14,behavior:19,behaviour:0,being:[3,18,20],besid:11,best:24,better:[15,23],between:[1,3,11,13,18,21,24],bin:[6,8],bit:[8,24],bodi:0,bool:[1,3,4],both:[8,9,11,21],bottom:14,branch:16,breakag:24,brew:8,broadli:[17,22],browser:14,bug:22,build:[8,9,13,14,23],built:[10,15,21,24],bulk:21,bunch:[19,22],burden:24,busi:[12,18],c008:19,c12bdc2d:19,c1f4:21,c25e:16,c28d23a757b:21,c955:19,c98f:12,c_plus_d:[17,20],cach:[1,18],call:[13,14,18,19,20,21,24],callabl:1,callback:1,caller:3,can:[1,2,6,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24],capabilti:19,capabitili:13,capabl:[12,17,18,19,24],captur:19,caus:[11,19],cb10:16,cb75946b0055:14,cc2ae784:16,certain:1,chang:[6,12,18,24],check:[1,2,6,8,11,13,21,24],check_posit:19,check_positivevalu:19,choic:14,choos:13,circuit:21,cleali:24,clear:[11,19],cli:[22,23],click:15,clone:[6,8],cloud:[18,20],code:[2,10,11,18,19,21,24],coerc:21,coerce_runtime_valu:21,collabor:24,collect:[1,11,22,23],com:[6,8],combin:12,combo:18,come:[1,8,21],comfort:12,command:[9,10,12,13,15,22,23],comment:17,common:[10,12],commun:19,compar:6,complet:[1,14,15,18],complex:9,complic:20,compos:1,compris:1,comput:[1,10,12,13,14,18,19,21],computation:24,concaten:13,concept:[13,14,18,19],conceptu:10,concis:0,conda:8,condit:3,condition:16,conf:18,config:[0,1,10,11,12,15,16,17,18,19,20,22,23],config_env:10,config_field:[0,1,10,11,16,17,18,19,20,22],config_typ:1,config_valu:[1,3],configdefinit:[16,17,18,19,20],configtyp:1,configur:[0,1,2,7,12,15,16,18,19,22,24],configurable_hello:10,configurable_hello_pipelin:10,configuration_schema:11,configuration_schemas_error_1:11,configuration_schemas_error_2:11,conform:[1,11],conn:18,connect:[1,9,13,15,18,20],consol:[12,15],console_log:18,constant:22,constant_env:22,constitut:1,construct:1,consum:[1,11,21,22,24],consume_ssn:21,consume_string_tupl:21,contain:[1,6,15,17,24],context:[0,1,3,7,10,11,16,17,19,21,22,24],context_definit:[1,18],context_fn:[1,18],context_param:1,contextcreationexecutioninfo:1,contract:24,contribut:7,control:[1,12,18,19,24],convent:18,copi:[13,22],core:[0,1,2,4,11,13,14,16,18,19,20,21],correct:1,correspond:10,could:[1,9,15,18],count:[11,22],count_lett:[11,22],coupl:[10,21],creat:[0,1,6,12,17,18,22,23],create_single_solid_pipelin:17,create_sub_pipelin:17,creation:[0,18],cred:18,credenti:[12,18],critic:[19,24],current:[1,19],custom:[7,12,14],d129552525a4:19,d548ea66:16,dag:[1,7,10,14,15,17,24],dagit:[8,9,10,11,12,13,19,20,21],dagster:[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,21,22,23,24],dagster_error:3,dagster_exampl:6,dagster_pd:1,dagster_typ:1,dagsterenv:6,dagsterevaluatevalueerror:21,dagsterexpectationfailederror:[2,19],dagsterinvaliddefinitionerror:2,dagsterinvariantviolationerror:[2,11],dagsterruntimecoercionerror:2,dagstertyp:[1,21],dagstertypeerror:[2,21],dagsterusercodeexecutionerror:2,data:[1,7,13,14,17,18,19,21],databas:[1,12,18],datafram:1,dea6d00d99f0:14,deal:18,debug:[11,12,18,19,22],debug_messag:12,declar:[1,9,10,12,18,20,23],decor:[7,14],deem:24,deep:11,deepli:9,def:[0,1,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],default_output:3,default_provid:1,default_valu:[1,10],defaultdict:[11,22],defin:[0,1,2,7,10,13,14,18,22,23],define_configurable_hello_pipelin:10,define_demo_configuration_schema_pipelin:11,define_demo_configuration_schema_repo:11,define_demo_execution_pipelin:22,define_demo_execution_repo:22,define_diamond_dag_pipelin:9,define_execution_context_pipeline_step_on:12,define_execution_context_pipeline_step_thre:12,define_execution_context_pipeline_step_two:12,define_hello_dag_pipelin:13,define_hello_inputs_pipelin:15,define_hello_world_pipelin:[14,23],define_part_eleven_step_on:16,define_part_eleven_step_thre:16,define_part_eleven_step_two:16,define_part_fourteen_step_on:17,define_part_nine_step_on:18,define_part_ten_step_on:19,define_part_thirteen_step_on:20,define_part_thirteen_step_thre:20,define_part_thirteen_step_two:20,define_part_twelve_step_on:21,define_part_twelve_step_thre:21,define_part_twelve_step_two:21,define_repo:23,define_repo_demo_pipelin:23,define_stub_solid:[5,17],define_typed_demo_configuration_schema_error_pipelin:11,define_typed_demo_configuration_schema_pipelin:11,definit:[2,7,10,11,18,20,23],deliv:24,demand:1,demo_configuration_schema:11,demo_configuration_schema_repo:11,demo_execut:22,demo_execution_repo:22,demo_repo:23,demo_repositori:23,demonstr:[9,15,18],depend:[1,6,9,10,11,12,13,15,16,17,18,19,20,21,22,24],dependency_structur:1,dependencydefiniion:1,dependencydefinit:[1,9,11,13,16,17,18,19,20,21,22],dependencystructur:1,describ:[11,19,21],descript:[0,1,11,16,21],design:[1,18,24],destruct:1,detail:[10,15],deteremin:2,determin:[1,9,13],dev:[1,6],develop:[8,10,12,18,19],dfc8165a:14,diagnost:24,dict:[0,1,3,10,11,13,15,18,22],dictionari:[0,1,3,9,13,15],did:[16,21],differ:[1,6,10,12,14,18,19,20,21,24],difficult:[17,18,24],dimens:18,dimension:1,direct:[1,13,24],directli:[14,15],directori:[6,18],discov:24,discuss:17,disk:1,displai:1,display_nam:1,distinguish:13,document:[6,8,11,22,24],doe:[1,9,16,18,21],doing:[18,20],don:[9,12,13],done:[10,17,24],dot:15,double_the_word:[11,22],double_the_word_with_typed_config:11,download:8,downstream:[16,18],dramat:18,drive:22,dropdown:13,dsl:[12,24],dure:[3,24],dynam:16,dynamodb:18,e257262eab79:19,e835:21,each:[1,3,9,10,12,13,14,15,18,20,22],earlier:[15,22],easier:[1,23],easili:24,edg:1,edit:[10,11],editor:[10,15],effect:24,either:[1,3,12,13,16,18,24],element:22,elif:[10,16],els:[10,16],emit:[14,16,17],emittedoutput:16,enabl:17,encod:13,encourag:[8,24],encout:3,end:[16,18],enforce_uniqu:1,engin:[13,24],enrich:22,ensur:[1,11,21],enter:[15,19],entir:[10,12,15,17,18,19],entit:1,entri:9,entropi:24,env:[11,18,22],enviro:3,environ:[1,3,5,6,9,10,12,15,18,24],error:[3,7,11,12,13,15,19,21,22,24],error_messag:12,especi:23,etc:[1,6,12,20],evalu:[1,11,19],evaluate_valu:21,even:12,event_typ:14,ever:11,everi:[1,12,14,18,24],everyth:15,examin:16,exampl:[0,1,6,9,10,12,14,15,16,18,21,23,24],excel:24,except:[1,2,3,16,21,24],execut:[1,7,9,10,11,13,15,16,17,18,19,23,24],execute_pipelin:[3,10,12,14,15,16,17,19,20,21],execute_pipeline_iter:3,execute_solid:5,execute_with_another_world:15,execution_context:12,execution_context_pipelin:12,execution_plan_step_start:14,execution_plan_step_success:14,executioncontext:[1,3,12,18],exist:[1,17],expect:[1,2,7,11,18,21,24],expectation_fn:[1,19],expectationdefinit:[1,19],expectationexecutioninfo:1,expectationresult:[1,19],expedit:6,expens:[11,19],experi:[11,15],explain:18,explicit:[19,24],explictli:19,explod:0,explor:[9,10,13,14],expos:12,express:[12,13,21,24],extern:[1,9,10,12,15,18,24],extract:1,f37e:14,f6fd78c5:16,f77205931abb:14,facil:[10,12],fact:13,fail:[15,18,19,21],faild:2,failur:[1,2,11],fals:19,far:[15,16,18,20,21],fashion:18,fast:1,fe29:14,featur:[8,10,13,19],few:[13,14],field:[0,1,10,11,18,22],file:[6,10,11,12,15,18,20,22,23],filesystem:18,filter:[12,14],fire:16,first:[8,9,10,13,14,16,18,19,21],flag:15,flexibl:[10,21],flow:[1,11,13,15,18,21,24],fly:10,focu:17,foe:18,follow:[8,10,17,18,20,22],foo:[0,12,13],forget:13,form:[1,15,16,21],format:[12,16,18,21,24],forth:1,fragment:12,frame:19,framework:1,frequent:1,from:[0,1,6,9,10,11,12,13,14,15,16,17,18,19,21,22,23],from_dict:[0,16],front:21,frontend:6,fulli:10,further:[14,15],futur:19,gener:[1,6,12,18,20,24],get:[1,3,11,14,20,21,23],get_all_pipelin:1,get_pipelin:1,git:[6,8],github:[6,8],give:13,given:[1,3,24],glarb:0,glob:22,goal:[18,19],going:[18,21],good:12,got:[11,21],gradual:1,graph:[1,13,17,20,24],graphql:6,group:12,guarante:11,guard:22,gui:14,had:[16,19],halt:[11,19],handi:6,handl:[1,18],hang:1,happen:[3,11],hard:18,hardcod:[10,13,15],has:[1,2,14,15,16,17,19,21,24],has_solid:1,hash:21,have:[0,1,6,9,10,13,15,16,17,18,19,20,21,23,24],haw:10,hello:[0,7,10,15],hello_dag:13,hello_dag_pipelin:13,hello_input:15,hello_world:[0,14,23],hello_world_pipelin:14,help:[11,13,21],here:[10,11,15,21],heterogen:24,highli:8,highlight:14,hit:18,homebrew:8,honua:10,hook:20,host:19,how:[1,9,10,11,12,13,14,15,16,18,20,21,23,24],howev:[16,18,20,21],html:6,http:[6,13,14,15,23,24],idea:18,idempot:[1,24],identifi:1,illustr:10,imagin:[11,15,18,19,20,21],immatur:19,implement:[0,1,16,18],implicit:[19,24],implicitli:16,implict:19,improv:[11,15],includ:[11,12,17,18,20],incom:21,inde:20,indetermin:12,index:[1,7],indic:[2,18,19],individu:[1,10,12,24],info:[0,1,2,10,11,12,14,16,17,18,19,20,21,22],inform:[1,12,13,14,15,23,24],ingest:[18,19],ingest_a:[18,19],ingest_b:[18,19],inherit:21,inject:17,injected_solid:17,inmemorystor:18,inner_typ:4,input:[0,1,5,7,9,10,11,13,14,16,17,18,19,20,21,22,24],input_def:1,input_nam:1,inputdefinit:[0,1,9,11,13,15,16,17,18,19,20,21,22],inputs_env:15,insert:18,insid:[8,11],inspect:[19,24],instal:[6,7,14],instanc:[1,12,13,16,18,20],instanti:20,instead:[0,1,10,11,15,17,23],instruct:14,integr:[1,18,24],intend:3,interact:[1,6,9,10,15,18],interest:[13,15,20],interfac:[14,18],intermitt:18,intern:1,internet:18,interpret:8,intro_tutori:23,introduc:[13,14,21],invalid:16,invari:2,invoc:1,invok:[15,18],involv:[12,20],is_opt:[1,10],is_posit:1,isinst:21,isn:3,isol:[8,17,18],issu:6,iter:[1,3,16],iterate_over_pipelin:1,its:[1,9,10,11,13,14,15,18,24],itself:[0,1,16],javascript:6,jest:6,job:19,just:[8,9,10,13,14,15,16,17,21,22,23],keep:22,kei:[0,1,3,10,13,15,18],kept:12,know:[15,23,24],known:[15,24],kwarg:[0,2,3,4],label:20,lambda:[0,1,18,19],lambda_solid:[0,9,10,11,13,14,15,17,20,21,22,23],languag:10,last:[9,22],later:[13,14,18,22],latest:8,layer:13,learn:[10,11,23,24],left:[0,17],len:[10,17],less:15,let:[9,11,12,13,14,15,16,17,18,19,21,22,23,24],letter:[11,22],level:[12,14,18,22],librari:[8,24],like:[0,1,8,10,12,15,16,18,19,20,21,22,23],line:[9,10,12,13,14,15,22,23],link:10,list:[0,1,3,4,9,23],littl:23,live:[6,18],livehtml:6,load:[15,20,22,23],load_a:20,load_b:20,load_numb:[17,20],local:18,localhost:[6,23],locat:24,log:[0,1,12,14,16,18,19,21,22],log_level:[11,12,18,19,22],log_message_id:[12,14,16,19,21],log_num:16,log_num_squar:16,logic:[12,18],longer:18,look:[9,18,22],lot:[12,14],machin:24,made:[11,12,20,21,24],mai:[1,10,15,23,24],maintain:24,mainten:24,make:[3,6,8,11,12,15,19,20,23,24],malform:19,manag:[6,8,12,24],mani:[1,10,12,13,15,20,23,24],manual:1,map:1,mar:15,mark:14,match:21,matter:[9,12,22],matur:24,maxim:24,maximum:10,mean:[15,21],meaning:[12,24],mechan:[14,16,17],medium:24,memori:[1,17,18],messag:[1,11,12,13,14,21],met:23,metadata:[1,11,12,19,21,24],method:1,microsoft:8,might:[10,11,12],milli:14,mismatch:2,miss:[11,13],mistak:[11,15],mistyp:11,mode:6,model:[7,13,23],modifi:16,modul:[7,18,23],more:[0,9,10,12,16,18,19,20,21,22],most:[12,23],mostli:1,move:18,much:[1,10],mult:18,mult_int:18,multer:[17,20],multi:14,multipl:[0,1,7,18,20,22,24],multipleresult:[0,16],must:[1,10,13,15,16,17,18,19],my_solid:0,my_solid_from_dict:0,myenv:8,naiv:18,name:[0,1,3,5,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],namedtupl:[18,21],natur:19,navig:[13,14],necessari:1,need:[0,6,8,15,18,22,24],never:[16,17,21,24],next:[9,10,12,13,14,15,16,22,23],nice:[12,18],nine:19,node:[3,14,20,21,24],non:1,none:[0,1,3,5],norm:24,not_a_tupl:21,note:[3,9,12,15,16,18,21],notic:[12,13,15,16,18,19,20,21],notori:[18,24],now:[9,10,11,12,13,15,17,18,19,20,21,22,23],nullabl:4,num1:[17,20],num2:[17,20],num:16,num_on:[18,19],num_squar:16,num_two:[18,19],number:[1,16,18,19,21],object:[0,1,12,16,18,21],obvious:20,occur:[12,18,21],off:[1,17],often:[15,24],omit:0,onc:23,one:[1,3,10,12,14,15,16,17,18,20,21,22],onli:[1,2,10,12,14,15,16,18,19,20,21,22],oper:[1,8,11,12,15,18,19,20,24],opinion:[7,24],option:[1,8,11,13,19],order:[9,10,12,13,15,18,19,21,22,23,24],orig_messag:[12,14,16,19,21],osx:8,other:[1,8,9,12,13,16,17,23,24],other_nam:1,otherwis:0,our:[10,11,12,13,14,15,18,21,22,23],out:[12,24],out_on:16,out_two:16,output:[0,1,3,7,9,10,11,12,13,14,15,17,18,19,20,21,24],output_nam:[1,3],outputdefinit:[0,1,11,15,16,17,18,19,20,21],outputs_def:1,outsid:15,over:[1,24],overrid:22,overview:24,own:[14,15,18,21],packag:8,page:7,panda:[1,24],pane:14,paramet:[0,1,3,10,12,20],parameter:[3,15],parameteriz:1,parametr:[10,15],parametriz:24,part:[8,10,19,22,23,24],part_eight:11,part_eleven:16,part_eleven_step_on:16,part_eleven_step_thre:16,part_eleven_step_two:16,part_nin:18,part_seven:22,part_ten:19,part_ten_step_on:19,part_thirteen:20,part_twelv:21,part_twelve_step_on:21,part_twelve_step_thre:21,part_twelve_step_two:21,particular:[3,10,12,16,18,20,24],particularli:20,partnineresourc:18,pass:[1,10,11,17,18,21,23],passthrough:1,passthrough_context_definit:1,password:18,path:[1,4,8,11],pattern:[12,23],peopl:[23,24],per:[0,1,9,10,12,15,18],perform:[1,19,24],persona:24,piec:18,pieplin:1,pip3:8,pip:6,pipelin:[1,2,3,7,9,10,11,12,13,15,16,18,19,20,21,23,24],pipeline_def:5,pipeline_dict:[1,11,22,23],pipeline_execut:22,pipeline_result:[17,20],pipeline_start:14,pipeline_success:14,pipelineconfigevaluationerror:[3,11],pipelinecontextdefinit:[1,18],pipelinedefinit:[1,3,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],pipelinedefiniton:1,pipelinedefint:1,pipelineexecutionresult:3,place:22,plain:21,plan:[6,19],platform:[14,23],plu:17,point:[9,16,23],pool:18,poorli:24,pop:[12,15],popd:8,port:6,posit:19,possibl:11,practic:[12,24],pre:1,prefer:12,present:[1,8],prevent:[11,19],previou:[1,10,11,16,23],previous:18,primari:[15,18],primer:24,principl:7,print:[0,12],prior:[15,24],probabl:1,proce:10,process:[19,21,24],prod:[1,12],produc:[0,1,14,24],produce_invalid_valu:21,produce_valid_ssn_str:21,produce_valid_valu:21,product:[1,10,18,24],program:[7,12,13,23,24],programmat:23,project:[6,8,12,23],prone:[15,22],properli:24,properti:[1,10,12,18,19],provid:[1,10,11,12,13,15,16,17,18,24],publiccloudconn:18,publiccloudstor:18,publish:6,pure:[1,18],purpos:[12,20],pushd:8,put:18,python3:[6,8],python:[6,12,14,16,18,19,21,24],python_modul:6,python_packag:8,python_typ:[4,21],pythonobjecttyp:[4,21],qualiti:[1,19],quickli:24,quit:[17,19],quux:11,quuxquux:11,rais:[2,16,21],ran:11,rather:[3,9,12,13,14,15,16,17,20,24],react_app_graphql_uri:6,read_csv:1,reason:[1,18,20],recal:15,receiv:21,recommend:8,record:18,record_valu:18,recours:19,red:15,redistribut:8,reduc:24,reentrant_info:3,reentrantinfo:3,regex:21,regret:8,regular:21,rel:18,releas:8,relev:21,reliabl:18,render:6,repeat:21,repetit:23,replac:11,repo:23,repo_demo_pipelin:23,report:24,repositori:[1,6,7,8,12,22],repositorydefinit:[1,11,22,23],repostori:23,repr:21,repres:1,requir:[0,1,6,11,18,19,21,24],rerun:10,resid:20,resourc:[1,18],resource_fn:1,resourcedefinit:1,respect:18,restrict:12,result:[0,1,3,6,11,14,16,17,18,19],result_context:1,result_dict:0,result_for_solid:[3,17,20],result_list:[3,17],retriev:1,return_dict_result:16,reus:[12,20],reusabl:[7,10],rewrit:10,rich:[11,15,24],richer:12,right:[0,14,15,19],root:[8,11],rout:12,rudimentari:18,rule:2,run:[3,8,10,11,12,13,14,16,18,19,21,22,23,24],run_id:[12,14,16,19,21],runner:6,runtim:[2,11,12,13,15,21,24],runtime_typ:[1,16],sai:[17,18,19,21],salient:10,same:[0,1,9,10,12,15,16,23,24],satisfi:[1,9,17],save:[14,21,23],scalar:[1,10],scenario:18,schema:[7,10,22],scientist:24,scope:[18,20],scratch:18,script:[6,14],seam:18,search:7,second:[10,13,15,18],section:[10,13,15],secur:21,see:[1,3,8,9,11,12,13,14,15,16,18,20,24],seen:[9,12,15],select:8,self:[11,18,21],semi:12,sensibl:6,separ:[8,12,13],serial:21,serv:[14,15,23,24],server:6,servic:18,set:[6,12,14,18,22],set_value_in_cloud_stor:18,setup:1,sever:[0,15],shell:8,shine:18,shortcut:0,should:[0,1,8,10,12,13,14,16,18,20,21,23,24],shouldn:20,show:21,side:24,signatur:1,signifi:21,signific:21,silli:21,simpl:[0,13,18],simpler:0,simplifi:[0,19],sinc:9,singl:[0,1,10,12,14,16,17,18,20,24],site:20,skip:19,slightli:[9,19,21],slow:18,snapshot:6,social:21,softwar:[1,8,18,19],solid:[0,1,2,3,7,9,10,11,12,13,14,15,16,17,18,19,21,22,23],solid_1:1,solid_2:1,solid_a:9,solid_b:9,solid_c:9,solid_d:9,solid_definit:[12,14,16],solid_nam:[1,5],solid_on:[12,13],solid_result:20,solid_subset:3,solid_two:[12,13],soliddefinit:[0,1,3],solidexecutionresult:3,solidinst:[1,17,20],some:[1,2,6,18,19,21,22,24],some_input:1,some_kei:18,some_password:18,some_pwd:18,some_us:18,some_valu:18,someth:[0,6,18],sophist:[9,19],sort:18,sourc:[6,12],space:2,spark:24,speak:[10,17],special:20,specif:[12,16,21,22],specifi:[0,1,10,11,12,13,15,16,18,22,23],specific_env:22,spew:[16,18,19,21],split:22,sql:24,ssd:1,ssn:21,ssnstring:21,ssnstringtyp:21,ssnstringtypeclass:21,stack:21,stacktrac:15,stage:24,start:[6,9,17],state:[3,12,18],step:[3,13,14,15],step_eleven:16,step_kei:14,step_results_by_tag:3,still:9,storag:[18,20],store:18,str:[0,1,21],str_one:21,str_two:21,str_valu:0,stream:[1,14],strict:21,string:[0,4,10,11,13,15,16,18,21,22],string_tupl:21,stringtupl:21,stringtupletyp:21,strongli:[8,11,22],structur:[1,11,12,15,21,24],stub_a:17,stub_b:17,stub_c_plus_d:17,studio:8,subdag:17,subset:[17,24],substitut:18,substrat:12,subtl:18,succeed:[14,19],success:[1,3,14,17,19,20],suck:18,sudo:8,suffici:24,suitabl:[1,18],suppli:1,support:[0,1,16,24],suppos:[6,22],surfac:[15,18,21],swappabl:[18,23],sync:22,synchron:3,syntax:12,system:[1,2,4,8,11,12,19,21,24],tab:14,tabl:1,tailor:20,take:[0,1,10,14,17,18],talk:18,target:[1,23],task:[9,13,24],team:24,tediou:[11,22],tell:[13,19,22,23],term:[16,19],test:[1,3,6,7,8,10,12,18,19,24],test_a_plus_b_final_subdag:17,test_intro_tutorial_part_four:10,test_part_thirteen_step_on:20,test_part_thirteen_step_two:20,testabl:[10,18],than:[3,6,9,12,13,15,16,17,20,22,24],thei:[0,1,9,12,19,20,21,24],them:[8,10,12,14,15,18,20],thi:[0,1,3,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,24],thing:[3,12,18,20,21],think:[20,24],third:14,thirteen_step_on:20,thirteen_step_two:20,those:[1,6,8,10,18,19,22,24],though:12,thread:14,three:[14,15,20],through:[1,12,15,18,21,24],throughout:21,throw_on_error:[3,19],thrown:[2,21],thu:1,tie:16,tied:20,time:[1,9,10,11,12,14,15,16,18,19,20,23,24],timestamp:12,tiresom:23,togeth:[9,12,20],toi:21,tool:[6,8,11,12,14,18,19,21,22,23,24],topolog:[9,13],total:15,touch:12,tox:6,trace:[11,21],tradit:19,transform:[0,1,3,14,15,16,18,21],transform_fn:1,transformed_valu:[3,17,20],transformexecutioninfo:[1,10],tree:6,trigger:16,trivial:[18,21],tupl:21,turn:[9,10],tutori:[10,16,22,23],tutorial_part_thirteen_step_on:17,tutorial_part_thirteen_step_thre:20,two:[1,12,13,16,17,18,20,22],txt:6,type:[0,1,2,7,10,11,12,13,16,17,18,19,20,22,23],typecheck:21,typed_demo_configuration_schema:11,typed_demo_configuration_schema_error:11,typed_double_the_word:11,typed_double_the_word_error:11,typed_double_word:11,typed_double_word_mismatch:11,typic:[1,17,19,21],ubuntu:8,undefin:11,under:[10,15],unexpect:19,unfamiliar:24,uniqu:[1,16],unit:[1,7,12,13,14,18,24],unittest:1,univers:12,unlik:19,unnam:[1,12,17],until:15,untyp:15,unzip:20,updat:[6,8,19],upload:20,upstream:17,usag:1,use:[1,6,8,10,12,14,15,17,18,22,23,24],used:[1,10,11,14,16,18,20,21],useful:[1,3,12,15,17,19,20,21,22,24],user:[1,2,7,10,12,15,18,19,24],usernam:18,uses:23,using:[6,8,10,12,14,15,18,20,22,23],util:[7,10,14],valid:[11,21],valu:[0,1,2,3,5,10,11,14,15,16,17,18,19,21,22,24],value_on:21,value_two:21,vari:[1,18,22],venv:[6,8],veri:[1,3,11,13,20,21],verifi:21,version:[3,6,16,18,19],via:[14,15,18,19],view:[11,14],viewabl:19,violat:[2,11],virtualenv:6,virtualenviron:8,virtualenvwrapp:8,visual:[8,13,14,23],wai:[0,14,15,16,18,19,24],want:[1,10,12,15,17,18,19,21,22,23],watch:6,web:14,webapp:8,welcom:7,well:[2,15,21,24],were:20,what:[1,9,11,12,13,18,19,20,21,24],whatev:18,when:[0,1,3,6,9,11,15,18,19,22,23,24],whenev:18,where:[1,10,12,13,14,17,18,19],whether:[1,3,19,24],which:[1,3,6,10,11,12,13,14,15,16,18,21,22,23,24],who:[12,24],whole:[3,19,21],whose:[0,1,8,13,15],why:20,wide:[8,18],window:8,wire:[9,21],within:[1,13,14,15,18,19,20],without:[10,12,14,15,23],won:8,word:[11,15,22],work:[0,11,12,19,23],workflow:13,world:[7,10,15],worri:13,worth:9,would:[1,9,15,18],wrap:16,write:14,written:24,wrong:[11,21],wrong_word:11,yaml:[10,12,15,18,22],yarn:6,yellow:14,yet:6,yield:[0,1,3,15,16,24],yield_output:16,yml:[6,10,11,12,15,18,22,23],you:[1,6,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],your:[8,9,14,15,18,19,21,23],zero:18},titles:["Decorators","Definitions","Errors","Execution","Types","Utilities","Contributing","Intro Tutorial","Installation","An actual DAG","Configuration","Configuration Schemas","Execution Context","Hello, DAG","Hello, World","Inputs","Multiple Outputs","Unit-testing Pipelines","Custom Contexts","Expectations","Reusable Solids","User-defined Types","Pipeline Execution","Repositories","Principles"],titleterms:{"function":24,actual:9,agnost:24,api:[7,15],cli:[14,15],comput:24,condit:16,configur:[10,11],context:[12,18],contribut:6,creat:8,custom:[18,21],dag:[9,13],dagit:[6,14,15,23],data:24,decor:0,defin:21,definit:[1,4],describ:24,dev:8,develop:6,direct:21,doc:6,environ:8,error:2,execut:[3,12,14,22],expect:19,from:8,futur:21,gradual:24,hello:[13,14],indic:7,input:15,instal:8,intro:7,librari:14,local:6,multipl:16,option:24,output:16,pip:8,pipelin:[14,17,22],principl:24,pypi:8,python:[8,15],qualiti:24,refer:7,releas:6,repositori:23,reusabl:20,run:6,schema:11,self:24,setup:6,solid:20,sourc:8,stabl:8,tabl:7,test:17,testabl:24,tutori:7,type:[4,15,21,24],unit:17,user:21,util:5,verifi:24,version:8,virtual:8,virtualenv:8,webapp:6,world:14,yarn:8}})'

snapshots['test_build_all_docs 5'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Python Module Index &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="./" src="_static/documentation_options.js"></script>
    <script type="text/javascript" src="_static/jquery.js"></script>
    <script type="text/javascript" src="_static/underscore.js"></script>
    <script type="text/javascript" src="_static/doctools.js"></script>
    <link rel="index" title="Index" href="genindex.html" />
    <link rel="search" title="Search" href="search.html" />

   
  <link rel="stylesheet" href="_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />



  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            

   <h1>Python Module Index</h1>

   <div class="modindex-jumpbox">
   <a href="#cap-d"><strong>d</strong></a>
   </div>

   <table class="indextable modindextable">
     <tr class="pcap"><td></td><td>&#160;</td><td></td></tr>
     <tr class="cap" id="cap-d"><td></td><td>
       <strong>d</strong></td><td></td></tr>
     <tr>
       <td><img src="_static/minus.png" class="toggler"
              id="toggle-1" style="display: none" alt="-" /></td>
       <td>
       <code class="xref">dagster</code></td><td>
       <em></em></td></tr>
     <tr class="cg-1">
       <td></td>
       <td>&#160;&#160;&#160;
       <a href="apidocs/types.html#module-dagster.core.types"><code class="xref">dagster.core.types</code></a></td><td>
       <em></em></td></tr>
   </table>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="contributing.html">Contributing</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="index.html">Documentation overview</a><ul>
  </ul></li>
</ul>
</div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 6'] = '''# Sphinx build info version 1
# This file hashes the configuration used when building these files. When it is not found, a full rebuild will be done.
config: 60669317f959338d907c02d78b4de87c
tags: 645f666f9bcd5a90fca523b33c5a78b7
'''

snapshots['test_build_all_docs 7'] = '''

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Index &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="./" src="_static/documentation_options.js"></script>
    <script type="text/javascript" src="_static/jquery.js"></script>
    <script type="text/javascript" src="_static/underscore.js"></script>
    <script type="text/javascript" src="_static/doctools.js"></script>
    <link rel="index" title="Index" href="#" />
    <link rel="search" title="Search" href="search.html" />
   
  <link rel="stylesheet" href="_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            

<h1 id="index">Index</h1>

<div class="genindex-jumpbox">
 <a href="#A"><strong>A</strong></a>
 | <a href="#B"><strong>B</strong></a>
 | <a href="#C"><strong>C</strong></a>
 | <a href="#D"><strong>D</strong></a>
 | <a href="#E"><strong>E</strong></a>
 | <a href="#F"><strong>F</strong></a>
 | <a href="#G"><strong>G</strong></a>
 | <a href="#H"><strong>H</strong></a>
 | <a href="#I"><strong>I</strong></a>
 | <a href="#L"><strong>L</strong></a>
 | <a href="#M"><strong>M</strong></a>
 | <a href="#N"><strong>N</strong></a>
 | <a href="#O"><strong>O</strong></a>
 | <a href="#P"><strong>P</strong></a>
 | <a href="#R"><strong>R</strong></a>
 | <a href="#S"><strong>S</strong></a>
 | <a href="#T"><strong>T</strong></a>
 | <a href="#V"><strong>V</strong></a>
 
</div>
<h2 id="A">A</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/types.html#dagster.core.types.Any">Any (in module dagster.core.types)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="B">B</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/types.html#dagster.core.types.Bool">Bool (in module dagster.core.types)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="C">C</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.TransformExecutionInfo.config">config (dagster.TransformExecutionInfo attribute)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.SolidDefinition.config_field">config_field (dagster.SolidDefinition attribute)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.Field.config_type">config_type (dagster.Field attribute)</a>
</li>
      <li><a href="apidocs/execution.html#dagster.PipelineExecutionResult.context">context (dagster.PipelineExecutionResult attribute)</a>

      <ul>
        <li><a href="apidocs/execution.html#dagster.SolidExecutionResult.context">(dagster.SolidExecutionResult attribute)</a>
</li>
        <li><a href="apidocs/definitions.html#dagster.TransformExecutionInfo.context">(dagster.TransformExecutionInfo attribute)</a>
</li>
      </ul></li>
  </ul></td>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.PipelineDefinition.context_definitions">context_definitions (dagster.PipelineDefinition attribute)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.ContextCreationExecutionInfo">ContextCreationExecutionInfo (class in dagster)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="D">D</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/types.html#module-dagster.core.types">dagster.core.types (module)</a>
</li>
      <li><a href="apidocs/execution.html#dagster.SolidExecutionResult.dagster_error">dagster_error (dagster.SolidExecutionResult attribute)</a>
</li>
      <li><a href="apidocs/errors.html#dagster.DagsterExpectationFailedError">DagsterExpectationFailedError</a>
</li>
      <li><a href="apidocs/errors.html#dagster.DagsterInvalidDefinitionError">DagsterInvalidDefinitionError</a>
</li>
      <li><a href="apidocs/errors.html#dagster.DagsterInvariantViolationError">DagsterInvariantViolationError</a>
</li>
      <li><a href="apidocs/errors.html#dagster.DagsterRuntimeCoercionError">DagsterRuntimeCoercionError</a>
</li>
      <li><a href="apidocs/errors.html#dagster.DagsterTypeError">DagsterTypeError</a>
</li>
      <li><a href="apidocs/errors.html#dagster.DagsterUserCodeExecutionError">DagsterUserCodeExecutionError</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.Field.default_provided">default_provided (dagster.Field attribute)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.Field.default_value">default_value (dagster.Field attribute)</a>
</li>
      <li><a href="apidocs/utilities.html#dagster.define_stub_solid">define_stub_solid() (in module dagster)</a>
</li>
  </ul></td>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.PipelineDefinition.dependencies">dependencies (dagster.PipelineDefinition attribute)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.PipelineDefinition.dependency_structure">dependency_structure (dagster.PipelineDefinition attribute)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.DependencyDefinition">DependencyDefinition (class in dagster)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.DependencyDefinition.description">description (dagster.DependencyDefinition attribute)</a>

      <ul>
        <li><a href="apidocs/definitions.html#dagster.ExpectationDefinition.description">(dagster.ExpectationDefinition attribute)</a>
</li>
        <li><a href="apidocs/definitions.html#dagster.Field.description">(dagster.Field attribute)</a>
</li>
        <li><a href="apidocs/definitions.html#dagster.InputDefinition.description">(dagster.InputDefinition attribute)</a>
</li>
        <li><a href="apidocs/definitions.html#dagster.OutputDefinition.description">(dagster.OutputDefinition attribute)</a>
</li>
        <li><a href="apidocs/definitions.html#dagster.PipelineDefinition.description">(dagster.PipelineDefinition attribute)</a>
</li>
        <li><a href="apidocs/definitions.html#dagster.SolidDefinition.description">(dagster.SolidDefinition attribute)</a>
</li>
      </ul></li>
      <li><a href="apidocs/definitions.html#dagster.PipelineDefinition.display_name">display_name (dagster.PipelineDefinition attribute)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="E">E</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/execution.html#dagster.execute_pipeline">execute_pipeline() (in module dagster)</a>
</li>
      <li><a href="apidocs/execution.html#dagster.execute_pipeline_iterator">execute_pipeline_iterator() (in module dagster)</a>
</li>
      <li><a href="apidocs/utilities.html#dagster.execute_solid">execute_solid() (in module dagster)</a>
</li>
      <li><a href="apidocs/execution.html#dagster.ExecutionContext">ExecutionContext (class in dagster)</a>
</li>
  </ul></td>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.ExpectationDefinition.expectation_fn">expectation_fn (dagster.ExpectationDefinition attribute)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.ExpectationDefinition">ExpectationDefinition (class in dagster)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.ExpectationExecutionInfo">ExpectationExecutionInfo (class in dagster)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.ExpectationResult">ExpectationResult (class in dagster)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.InputDefinition.expectations">expectations (dagster.InputDefinition attribute)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="F">F</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.Field">Field (class in dagster)</a>
</li>
  </ul></td>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/decorators.html#dagster.MultipleResults.from_dict">from_dict() (dagster.MultipleResults static method)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="G">G</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.RepositoryDefinition.get_all_pipelines">get_all_pipelines() (dagster.RepositoryDefinition method)</a>
</li>
  </ul></td>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.RepositoryDefinition.get_pipeline">get_pipeline() (dagster.RepositoryDefinition method)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="H">H</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.PipelineDefinition.has_solid">has_solid() (dagster.PipelineDefinition method)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="I">I</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.SolidDefinition.input_defs">input_defs (dagster.SolidDefinition attribute)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.InputDefinition">InputDefinition (class in dagster)</a>
</li>
  </ul></td>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/types.html#dagster.core.types.Int">Int (in module dagster.core.types)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.Field.is_optional">is_optional (dagster.Field attribute)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.RepositoryDefinition.iterate_over_pipelines">iterate_over_pipelines() (dagster.RepositoryDefinition method)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="L">L</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/decorators.html#dagster.lambda_solid">lambda_solid() (in module dagster)</a>
</li>
  </ul></td>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/types.html#dagster.core.types.List">List() (in module dagster.core.types)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="M">M</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.ExpectationResult.message">message (dagster.ExpectationResult attribute)</a>
</li>
  </ul></td>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.SolidDefinition.metadata">metadata (dagster.SolidDefinition attribute)</a>
</li>
      <li><a href="apidocs/decorators.html#dagster.MultipleResults">MultipleResults (class in dagster)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="N">N</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.ExpectationDefinition.name">name (dagster.ExpectationDefinition attribute)</a>

      <ul>
        <li><a href="apidocs/definitions.html#dagster.InputDefinition.name">(dagster.InputDefinition attribute)</a>
</li>
        <li><a href="apidocs/definitions.html#dagster.OutputDefinition.name">(dagster.OutputDefinition attribute)</a>
</li>
        <li><a href="apidocs/definitions.html#dagster.PipelineDefinition.name">(dagster.PipelineDefinition attribute)</a>
</li>
        <li><a href="apidocs/definitions.html#dagster.RepositoryDefinition.name">(dagster.RepositoryDefinition attribute)</a>
</li>
        <li><a href="apidocs/definitions.html#dagster.SolidDefinition.name">(dagster.SolidDefinition attribute)</a>
</li>
      </ul></li>
  </ul></td>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/types.html#dagster.core.types.Nullable">Nullable() (in module dagster.core.types)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="O">O</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.DependencyDefinition.output">output (dagster.DependencyDefinition attribute)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.Result.output_name">output_name (dagster.Result attribute)</a>
</li>
  </ul></td>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.OutputDefinition">OutputDefinition (class in dagster)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.SolidDefinition.outputs_defs">outputs_defs (dagster.SolidDefinition attribute)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="P">P</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.PipelineContextDefinition.passthrough_context_definition">passthrough_context_definition() (dagster.PipelineContextDefinition static method)</a>
</li>
      <li><a href="apidocs/types.html#dagster.core.types.Path">Path (in module dagster.core.types)</a>
</li>
      <li><a href="apidocs/execution.html#dagster.PipelineExecutionResult.pipeline">pipeline (dagster.PipelineExecutionResult attribute)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.RepositoryDefinition.pipeline_dict">pipeline_dict (dagster.RepositoryDefinition attribute)</a>
</li>
  </ul></td>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/execution.html#dagster.PipelineConfigEvaluationError">PipelineConfigEvaluationError</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.PipelineContextDefinition">PipelineContextDefinition (class in dagster)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.PipelineDefinition">PipelineDefinition (class in dagster)</a>
</li>
      <li><a href="apidocs/execution.html#dagster.PipelineExecutionResult">PipelineExecutionResult (class in dagster)</a>
</li>
      <li><a href="apidocs/types.html#dagster.core.types.PythonObjectType">PythonObjectType (class in dagster.core.types)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="R">R</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/execution.html#dagster.ReentrantInfo">ReentrantInfo (class in dagster)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.RepositoryDefinition">RepositoryDefinition (class in dagster)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.ResourceDefinition">ResourceDefinition (class in dagster)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.Result">Result (class in dagster)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.ExpectationResult.result_context">result_context (dagster.ExpectationResult attribute)</a>
</li>
  </ul></td>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/execution.html#dagster.PipelineExecutionResult.result_for_solid">result_for_solid() (dagster.PipelineExecutionResult method)</a>
</li>
      <li><a href="apidocs/execution.html#dagster.PipelineExecutionResult.result_list">result_list (dagster.PipelineExecutionResult attribute)</a>
</li>
      <li><a href="apidocs/decorators.html#dagster.MultipleResults.results">results (dagster.MultipleResults attribute)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.InputDefinition.runtime_type">runtime_type (dagster.InputDefinition attribute)</a>

      <ul>
        <li><a href="apidocs/definitions.html#dagster.OutputDefinition.runtime_type">(dagster.OutputDefinition attribute)</a>
</li>
      </ul></li>
  </ul></td>
</tr></table>

<h2 id="S">S</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.DependencyDefinition.solid">solid (dagster.DependencyDefinition attribute)</a>

      <ul>
        <li><a href="apidocs/execution.html#dagster.SolidExecutionResult.solid">(dagster.SolidExecutionResult attribute)</a>
</li>
      </ul></li>
      <li><a href="apidocs/decorators.html#dagster.solid">solid() (in module dagster)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.PipelineDefinition.solid_named">solid_named() (dagster.PipelineDefinition method)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.SolidDefinition">SolidDefinition (class in dagster)</a>
</li>
      <li><a href="apidocs/execution.html#dagster.SolidExecutionResult">SolidExecutionResult (class in dagster)</a>
</li>
  </ul></td>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.SolidInstance">SolidInstance (class in dagster)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.PipelineDefinition.solids">solids (dagster.PipelineDefinition attribute)</a>, <a href="apidocs/definitions.html#dagster.PipelineDefinition.solids">[1]</a>
</li>
      <li><a href="apidocs/types.html#dagster.core.types.String">String (in module dagster.core.types)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.ExpectationResult.success">success (dagster.ExpectationResult attribute)</a>

      <ul>
        <li><a href="apidocs/execution.html#dagster.PipelineExecutionResult.success">(dagster.PipelineExecutionResult attribute)</a>
</li>
        <li><a href="apidocs/execution.html#dagster.SolidExecutionResult.success">(dagster.SolidExecutionResult attribute)</a>
</li>
      </ul></li>
  </ul></td>
</tr></table>

<h2 id="T">T</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.SolidDefinition.transform_fn">transform_fn (dagster.SolidDefinition attribute)</a>
</li>
      <li><a href="apidocs/execution.html#dagster.SolidExecutionResult.transformed_value">transformed_value() (dagster.SolidExecutionResult method)</a>
</li>
  </ul></td>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/execution.html#dagster.SolidExecutionResult.transformed_values">transformed_values (dagster.SolidExecutionResult attribute)</a>
</li>
      <li><a href="apidocs/definitions.html#dagster.TransformExecutionInfo">TransformExecutionInfo (class in dagster)</a>
</li>
  </ul></td>
</tr></table>

<h2 id="V">V</h2>
<table style="width: 100%" class="indextable genindextable"><tr>
  <td style="width: 33%; vertical-align: top;"><ul>
      <li><a href="apidocs/definitions.html#dagster.Result.value">value (dagster.Result attribute)</a>
</li>
  </ul></td>
</tr></table>



          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="contributing.html">Contributing</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="index.html">Documentation overview</a><ul>
  </ul></li>
</ul>
</div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 8'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Contributing &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="./" src="_static/documentation_options.js"></script>
    <script type="text/javascript" src="_static/jquery.js"></script>
    <script type="text/javascript" src="_static/underscore.js"></script>
    <script type="text/javascript" src="_static/doctools.js"></script>
    <link rel="index" title="Index" href="genindex.html" />
    <link rel="search" title="Search" href="search.html" />
    <link rel="next" title="Hello, World" href="intro_tutorial/hello_world.html" />
    <link rel="prev" title="Installation" href="installation.html" />
   
  <link rel="stylesheet" href="_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="contributing">
<h1>Contributing<a class="headerlink" href="#contributing" title="Permalink to this headline">¶</a></h1>
<p>If you are planning to contribute to dagster, you will need to set up a local
development environment.</p>
<div class="section" id="local-development-setup">
<h2>Local development setup<a class="headerlink" href="#local-development-setup" title="Permalink to this headline">¶</a></h2>
<ol class="arabic simple">
<li>Install Python 3.6.</li>
</ol>
<blockquote>
<div><ul class="simple">
<li>You can’t use Python 3.7+ yet because of <a class="reference external" href="https://github.com/apache/arrow/issues/1125">https://github.com/apache/arrow/issues/1125</a></li>
</ul>
</div></blockquote>
<p>2. Create and activate a virtualenv</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">python3</span> <span class="o">-</span><span class="n">m</span> <span class="n">venv</span> <span class="n">dagsterenv</span>
<span class="n">source</span> <span class="n">dagsterenv</span><span class="o">/</span><span class="nb">bin</span><span class="o">/</span><span class="n">activate</span>
</pre></div>
</div>
<p>3. Install dagster locally and install dev tools</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">git</span> <span class="n">clone</span> <span class="n">git</span><span class="nd">@github</span><span class="o">.</span><span class="n">com</span><span class="p">:</span><span class="n">dagster</span><span class="o">-</span><span class="n">io</span><span class="o">/</span><span class="n">dagster</span><span class="o">.</span><span class="n">git</span>
<span class="n">cd</span> <span class="n">dagster</span><span class="o">/</span><span class="n">python_modules</span>
<span class="n">pip</span> <span class="n">install</span> <span class="o">-</span><span class="n">e</span> <span class="o">./</span><span class="n">dagit</span>
<span class="n">pip</span> <span class="n">install</span> <span class="o">-</span><span class="n">e</span> <span class="o">./</span><span class="n">dagster</span>
<span class="n">pip</span> <span class="n">install</span> <span class="o">-</span><span class="n">r</span> <span class="o">./</span><span class="n">dagster</span><span class="o">/</span><span class="n">dev</span><span class="o">-</span><span class="n">requirements</span><span class="o">.</span><span class="n">txt</span>
</pre></div>
</div>
<p>4. Install dagit webapp dependencies</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">cd</span> <span class="n">dagster</span><span class="o">/</span><span class="n">python_modules</span><span class="o">/</span><span class="n">dagit</span><span class="o">/</span><span class="n">dagit</span><span class="o">/</span><span class="n">webapp</span>
<span class="n">yarn</span> <span class="n">install</span>
</pre></div>
</div>
<p>5. Run tests
We use tox to manage test environments for python.</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">cd</span> <span class="n">dagster</span><span class="o">/</span><span class="n">python_modules</span><span class="o">/</span><span class="n">dagster</span>
<span class="n">tox</span>
<span class="n">cd</span> <span class="n">dagster</span><span class="o">/</span><span class="n">python_modules</span><span class="o">/</span><span class="n">dagit</span>
<span class="n">tox</span>
</pre></div>
</div>
<p>To run JavaScript tests for the dagit frontend, you can run:</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">cd</span> <span class="n">dagster</span><span class="o">/</span><span class="n">python_modules</span><span class="o">/</span><span class="n">dagit</span><span class="o">/</span><span class="n">dagit</span><span class="o">/</span><span class="n">webapp</span>
<span class="n">yarn</span> <span class="n">test</span>
</pre></div>
</div>
<p>In webapp development it’s handy to run <cite>yarn run jest –watch</cite> to have an
interactive test runner.</p>
<p>Some webapp tests use snapshots–auto-generated results to which the test
render tree is compared. Those tests are supposed to break when you change
something.</p>
<p>Check that the change is sensible and run <cite>yarn run jest -u</cite> to update the
snapshot to the new result. You can also update snapshots interactively
when you are in <cite>–watch</cite> mode.</p>
<div class="section" id="running-dagit-webapp-in-development">
<h3>Running dagit webapp in development<a class="headerlink" href="#running-dagit-webapp-in-development" title="Permalink to this headline">¶</a></h3>
<p>For development, run the dagit GraphQL server on a different port than the
webapp, from any directory that contains a repository.yml file. For example:</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">cd</span> <span class="n">dagster</span><span class="o">/</span><span class="n">python_modules</span><span class="o">/</span><span class="n">dagster</span><span class="o">/</span><span class="n">dagster</span><span class="o">/</span><span class="n">dagster_examples</span>
<span class="n">dagit</span> <span class="o">-</span><span class="n">p</span> <span class="mi">3333</span>
</pre></div>
</div>
<p>Run the local development (autoreloading, etc.) version of the webapp.</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">cd</span> <span class="n">dagster</span><span class="o">/</span><span class="n">python_modules</span><span class="o">/</span><span class="n">dagit</span><span class="o">/</span><span class="n">dagit</span><span class="o">/</span><span class="n">webapp</span>
<span class="n">REACT_APP_GRAPHQL_URI</span><span class="o">=</span><span class="s2">&quot;http://localhost:3333/graphql&quot;</span> <span class="n">yarn</span> <span class="n">start</span>
</pre></div>
</div>
</div>
<div class="section" id="releasing">
<h3>Releasing<a class="headerlink" href="#releasing" title="Permalink to this headline">¶</a></h3>
<p>Projects are released using the Python script at <cite>dagster/bin/publish.py</cite>.</p>
</div>
<div class="section" id="developing-docs">
<h3>Developing docs<a class="headerlink" href="#developing-docs" title="Permalink to this headline">¶</a></h3>
<p>Running a live html version of the docs can expedite documentation development.</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">cd</span> <span class="n">python_modules</span><span class="o">/</span><span class="n">dagster</span><span class="o">/</span><span class="n">docs</span>
<span class="n">make</span> <span class="n">livehtml</span>
</pre></div>
</div>
</div>
</div>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="index.html">Table Of Contents</a></h3>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="installation.html">Installation</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">Contributing</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="index.html">Documentation overview</a><ul>
      <li>Previous: <a href="installation.html" title="previous chapter">Installation</a></li>
      <li>Next: <a href="intro_tutorial/hello_world.html" title="next chapter">Hello, World</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="_sources/contributing.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="_sources/contributing.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 9'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Search &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="./" src="_static/documentation_options.js"></script>
    <script type="text/javascript" src="_static/jquery.js"></script>
    <script type="text/javascript" src="_static/underscore.js"></script>
    <script type="text/javascript" src="_static/doctools.js"></script>
    <script type="text/javascript" src="_static/searchtools.js"></script>
    <link rel="index" title="Index" href="genindex.html" />
    <link rel="search" title="Search" href="#" />
  <script type="text/javascript">
    jQuery(function() { Search.loadIndex("searchindex.js"); });
  </script>
  
  <script type="text/javascript" id="searchindexloader"></script>
  
   
  <link rel="stylesheet" href="_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />


  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <h1 id="search-documentation">Search</h1>
  <div id="fallback" class="admonition warning">
  <script type="text/javascript">$(\'#fallback\').hide();</script>
  <p>
    Please activate JavaScript to enable the search
    functionality.
  </p>
  </div>
  <p>
    From here you can search these documents. Enter your search
    words into the box below and click "search". Note that the search
    function will automatically search for all of the words. Pages
    containing fewer words won't appear in the result list.
  </p>
  <form action="" method="get">
    <input type="text" name="q" value="" />
    <input type="submit" value="search" />
    <span id="search-progress" style="padding-left: 10px"></span>
  </form>
  
  <div id="search-results">
  
  </div>

          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="contributing.html">Contributing</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="index.html">Documentation overview</a><ul>
  </ul></li>
</ul>
</div>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 10'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Installation &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="./" src="_static/documentation_options.js"></script>
    <script type="text/javascript" src="_static/jquery.js"></script>
    <script type="text/javascript" src="_static/underscore.js"></script>
    <script type="text/javascript" src="_static/doctools.js"></script>
    <link rel="index" title="Index" href="genindex.html" />
    <link rel="search" title="Search" href="search.html" />
    <link rel="next" title="Contributing" href="contributing.html" />
    <link rel="prev" title="Principles" href="principles.html" />
   
  <link rel="stylesheet" href="_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="id1">
<h1>Installation<a class="headerlink" href="#id1" title="Permalink to this headline">¶</a></h1>
<p>Dagster is tested on Python 3.6.6, 3.5.6, and 2.7.15. Python 3 is strongly
encouraged – if you can, you won’t regret making the switch!</p>
<div class="section" id="installing-python-pip-virtualenv-and-yarn">
<h2>Installing Python, pip, virtualenv, and yarn<a class="headerlink" href="#installing-python-pip-virtualenv-and-yarn" title="Permalink to this headline">¶</a></h2>
<p>To check that Python, the pip package manager, and virtualenv (highly
recommended) are already installed, you can run:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> python --version
<span class="gp">$</span> pip --version
<span class="gp">$</span> virtualenv --version
</pre></div>
</div>
<p>If these tools aren’t present on your system, you can install them as follows:</p>
<p>On Ubuntu:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> sudo apt update
<span class="gp">$</span> sudo apt install python3-dev python3-pip
<span class="gp">$</span> sudo pip3 install -U virtualenv  <span class="c1"># system-wide install</span>
</pre></div>
</div>
<p>On OSX, using <a class="reference external" href="https://brew.sh/">Homebrew</a>:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> brew update
<span class="gp">$</span> brew install python  <span class="c1"># Python 3</span>
<span class="gp">$</span> sudo pip3 install -U virtualenv  <span class="c1"># system-wide install</span>
</pre></div>
</div>
<p>On Windows (Python 3):
- Install the <em>Microsoft Visual C++ 2015 Redistributable Update 3</em>. This</p>
<blockquote>
<div><dl class="docutils">
<dt>comes with <em>Visual Studio 2015</em> but can be installed separately as follows:</dt>
<dd><ol class="first last arabic simple">
<li>Go to the Visual Studio downloads,</li>
<li>Select <em>Redistributables and Build Tools</em>,</li>
<li>Download and install the <em>Microsoft Visual C++ 2015 Redistributable
Update 3</em>.</li>
</ol>
</dd>
</dl>
</div></blockquote>
<ul class="simple">
<li>Install the 64-bit Python 3 release for Windows (select <code class="docutils literal notranslate"><span class="pre">pip</span></code> as an
optional feature).</li>
<li>Then run <code class="docutils literal notranslate"><span class="pre">pip3</span> <span class="pre">install</span> <span class="pre">-U</span> <span class="pre">pip</span> <span class="pre">virtualenv</span></code></li>
</ul>
<p>To use the dagit tool, you will also need to
<a class="reference external" href="https://yarnpkg.com/lang/en/docs/install/">install yarn</a>.</p>
</div>
<div class="section" id="creating-a-virtual-environment">
<h2>Creating a virtual environment<a class="headerlink" href="#creating-a-virtual-environment" title="Permalink to this headline">¶</a></h2>
<p>We strongly recommend installing dagster inside a Python virtualenv. If you are
running Anaconda, you should install dagster inside a Conda environment.</p>
<p>To create a virtual environment on Python 3, you can just run:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> python3 -m venv /path/to/new/virtual/environment
</pre></div>
</div>
<p>This will create a new Python environment whose interpreter and libraries
are isolated from those installed in other virtual environments, and
(by default) any libraries installed in a “system” Python installed as part
of your operating system.</p>
<p>On Python 2, you can use a tool like
<a class="reference external" href="https://virtualenvwrapper.readthedocs.io/en/latest/">virtualenvwrapper</a>
to manage your virtual environments, or just run:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> virtualenv /path/to/new/virtual/environment
</pre></div>
</div>
<p>You’ll then need to ‘activate’ the virtualenvironment, in bash by
running:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> <span class="nb">source</span> /path/to/new/virtual/environment/bin/activate
</pre></div>
</div>
<p>(For other shells, see the
<a class="reference external" href="https://docs.python.org/3/library/venv.html#creating-virtual-environments">venv documentation</a>.)</p>
<p>If you are using Anaconda, you can run:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> conda create --name myenv
</pre></div>
</div>
<p>And then, on OSX or Ubuntu:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> <span class="nb">source</span> activate myenv
</pre></div>
</div>
<p>Or, on Windows:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> activate myenv
</pre></div>
</div>
</div>
<div class="section" id="installing-the-stable-version-from-pypi">
<h2>Installing the stable version from PyPI<a class="headerlink" href="#installing-the-stable-version-from-pypi" title="Permalink to this headline">¶</a></h2>
<p>To install dagster and dagit, run:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> pip install dagster
<span class="gp">$</span> pip install dagit
</pre></div>
</div>
<p>This will install the latest stable version of both packages.</p>
</div>
<div class="section" id="installing-the-dev-version-from-source">
<h2>Installing the dev version from source<a class="headerlink" href="#installing-the-dev-version-from-source" title="Permalink to this headline">¶</a></h2>
<p>To install the development version of the software, first clone the project
from Github:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> git clone git@github.com:dagster-io/dagster.git
</pre></div>
</div>
<p>From the root of the repository, you can then run:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> pip install -e python_packages/dagster <span class="o">&amp;&amp;</span> <span class="se">\\</span>
  <span class="nb">pushd</span> python_packages/dagit/webapp <span class="o">&amp;&amp;</span> <span class="se">\\</span>
  yarn install <span class="o">&amp;&amp;</span> <span class="se">\\</span>
  yarn build <span class="o">&amp;&amp;</span> <span class="se">\\</span>
  <span class="nb">popd</span> <span class="o">&amp;&amp;</span> <span class="se">\\</span>
  pip install -e python_packages/dagit
</pre></div>
</div>
</div>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="index.html">Table Of Contents</a></h3>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="principles.html">Principles</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="contributing.html">Contributing</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="intro_tutorial/part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="index.html">Documentation overview</a><ul>
      <li>Previous: <a href="principles.html" title="previous chapter">Principles</a></li>
      <li>Next: <a href="contributing.html" title="next chapter">Contributing</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="_sources/installation.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="_sources/installation.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 11'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Hello, DAG &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="An actual DAG" href="actual_dag.html" />
    <link rel="prev" title="Hello, World" href="hello_world.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="hello-dag">
<h1>Hello, DAG<a class="headerlink" href="#hello-dag" title="Permalink to this headline">¶</a></h1>
<p>One of the core capabitilies of dagster is the ability to express data pipelines as arbitrary
directed acyclic graphs (DAGs) of solids.</p>
<p>We’ll define a very simple two-solid pipeline whose first solid returns a hardcoded string,
and whose second solid concatenates two copies of its input. The output of the pipeline should be
two concatenated copies of the hardcoded string.</p>
<div class="literal-block-wrapper docutils container" id="id1">
<div class="code-block-caption"><span class="caption-text">hello_dag.py</span><a class="headerlink" href="#id1" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre> 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="kn">from</span> <span class="nn">dagster</span> <span class="k">import</span> <span class="p">(</span>
    <span class="n">DependencyDefinition</span><span class="p">,</span>
    <span class="n">InputDefinition</span><span class="p">,</span>
    <span class="n">PipelineDefinition</span><span class="p">,</span>
    <span class="n">lambda_solid</span><span class="p">,</span>
<span class="p">)</span>


<span class="nd">@lambda_solid</span>
<span class="k">def</span> <span class="nf">solid_one</span><span class="p">():</span>
    <span class="k">return</span> <span class="s1">&#39;foo&#39;</span>


<span class="nd">@lambda_solid</span><span class="p">(</span><span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;arg_one&#39;</span><span class="p">)])</span>
<span class="k">def</span> <span class="nf">solid_two</span><span class="p">(</span><span class="n">arg_one</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">arg_one</span> <span class="o">*</span> <span class="mi">2</span>


<span class="k">def</span> <span class="nf">define_hello_dag_pipeline</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;hello_dag_pipeline&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">solid_one</span><span class="p">,</span> <span class="n">solid_two</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;solid_two&#39;</span><span class="p">:</span> <span class="p">{</span><span class="s1">&#39;arg_one&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;solid_one&#39;</span><span class="p">)}</span>
        <span class="p">},</span>
    <span class="p">)</span>
</pre></div>
</td></tr></table></div>
</div>
<p>This pipeline introduces a few new concepts.</p>
<ol class="arabic">
<li><p class="first">Solids can have <strong>inputs</strong> defined by instances of
<a class="reference internal" href="../apidocs/definitions.html#dagster.InputDefinition" title="dagster.InputDefinition"><code class="xref py py-class docutils literal notranslate"><span class="pre">InputDefinition</span></code></a>. Inputs allow us to connect solids to
each other, and give dagster information about solids’ dependencies on each other (and, as
we’ll see later, optionally let dagster check the types of the inputs at runtime).</p>
</li>
<li><p class="first">Solids’ <strong>dependencies</strong> on each other are expressed by instances of
<a class="reference internal" href="../apidocs/definitions.html#dagster.DependencyDefinition" title="dagster.DependencyDefinition"><code class="xref py py-class docutils literal notranslate"><span class="pre">DependencyDefinition</span></code></a>.
You’ll notice the new argument to <a class="reference internal" href="../apidocs/definitions.html#dagster.PipelineDefinition" title="dagster.PipelineDefinition"><code class="xref py py-class docutils literal notranslate"><span class="pre">PipelineDefinition</span></code></a>
called <code class="docutils literal notranslate"><span class="pre">dependencies</span></code>, which is a dict that defines the connections between solids in a
pipeline’s DAG.</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">solid_one</span><span class="p">,</span> <span class="n">solid_two</span><span class="p">],</span>
<span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
    <span class="s1">&#39;solid_two&#39;</span><span class="p">:</span> <span class="p">{</span><span class="s1">&#39;arg_one&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;solid_one&#39;</span><span class="p">)}</span>
<span class="p">},</span>

</pre></div>
</div>
<p>The first layer of keys in this dict are the <em>names</em> of solids in the pipeline. The second layer
of keys are the <em>names</em> of the inputs to each solid. Each input in the DAG must be provided a
<a class="reference internal" href="../apidocs/definitions.html#dagster.DependencyDefinition" title="dagster.DependencyDefinition"><code class="xref py py-class docutils literal notranslate"><span class="pre">DependencyDefinition</span></code></a>. (Don’t worry – if you forget
to specify an input, a helpful error message will tell you what you missed.)</p>
<p>In this case the dictionary encodes the fact that the input <code class="docutils literal notranslate"><span class="pre">arg_one</span></code> of solid <code class="docutils literal notranslate"><span class="pre">solid_two</span></code>
should flow from the output of <code class="docutils literal notranslate"><span class="pre">solid_one</span></code>.</p>
</li>
</ol>
<p>Let’s visualize the DAG we’ve just defined in dagit.</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagit -f hello_dag.py -n define_hello_dag_pipeline
</pre></div>
</div>
<p>Navigate to <a class="reference external" href="http://127.0.0.1:3000/hello_dag_pipeline/explore">http://127.0.0.1:3000/hello_dag_pipeline/explore</a> or choose the hello_dag_pipeline
from the dropdown:</p>
<img alt="../_images/hello_dag_figure_one.png" src="../_images/hello_dag_figure_one.png" />
<p>One of the distinguishing features of dagster that separates it from many workflow engines is that
dependencies connect <em>inputs</em> and <em>outputs</em> rather than just <em>tasks</em>. An author of a dagster
pipeline defines the flow of execution by defining the flow of <em>data</em> within that
execution. This is core to the the programming model of dagster, where each step in the pipeline
– the solid – is a <em>functional</em> unit of computation.</p>
<p>Now run the pipeline we’ve just defined, either from dagit or from the command line:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagster pipeline execute -f hello_dag.py -n define_hello_dag_pipeline
</pre></div>
</div>
<p>In the next section, <a class="reference internal" href="actual_dag.html"><span class="doc">An actual DAG</span></a>, we’ll build our first DAG with interesting
topology and see how dagster determines the execution order of a pipeline.</p>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="hello_world.html">Hello, World</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="hello_world.html" title="previous chapter">Hello, World</a></li>
      <li>Next: <a href="actual_dag.html" title="next chapter">An actual DAG</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/hello_dag.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/hello_dag.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 12'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Repositories &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="Pipeline Execution" href="pipeline_execution.html" />
    <link rel="prev" title="Execution Context" href="execution_context.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="repositories">
<h1>Repositories<a class="headerlink" href="#repositories" title="Permalink to this headline">¶</a></h1>
<p>Dagster is a not just a programming model for pipelines, it is also a platform for
tool-building. You’ve already met the dagster and dagit CLI tools, which let you programmatically
run and visualize pipelines.</p>
<p>In previous examples we have specified a file (<code class="docutils literal notranslate"><span class="pre">-f</span></code>) and named a pipeline definition function
(<code class="docutils literal notranslate"><span class="pre">-n</span></code>) in order to tell the CLI tools how to load a pipeline, e.g.:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagit -f hello_world.py -n define_hello_world_pipeline
<span class="gp">$</span> dagster pipeline execute -f hello_world.py -n define_hello_world_pipeline
</pre></div>
</div>
<p>But most of the time, especially when working on long-running projects with other people, we will
want to be able to target many pipelines at once with our tools.</p>
<p>A <strong>repository</strong> is a collection of pipelines at which dagster tools may be pointed.</p>
<p>Repostories are declared using a new API,
<a class="reference internal" href="../apidocs/definitions.html#dagster.RepositoryDefinition" title="dagster.RepositoryDefinition"><code class="xref py py-func docutils literal notranslate"><span class="pre">RepositoryDefinition</span></code></a>:</p>
<div class="literal-block-wrapper docutils container" id="id1">
<div class="code-block-caption"><span class="caption-text">repos.py</span><a class="headerlink" href="#id1" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre> 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
17</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="kn">from</span> <span class="nn">dagster</span> <span class="k">import</span> <span class="n">lambda_solid</span><span class="p">,</span> <span class="n">PipelineDefinition</span><span class="p">,</span> <span class="n">RepositoryDefinition</span>


<span class="nd">@lambda_solid</span>
<span class="k">def</span> <span class="nf">hello_world</span><span class="p">():</span>
    <span class="k">pass</span>


<span class="k">def</span> <span class="nf">define_repo_demo_pipeline</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span><span class="n">name</span><span class="o">=</span><span class="s2">&quot;repo_demo_pipeline&quot;</span><span class="p">,</span> <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">hello_world</span><span class="p">])</span>


<span class="k">def</span> <span class="nf">define_repo</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">RepositoryDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s2">&quot;demo_repository&quot;</span><span class="p">,</span>
        <span class="n">pipeline_dict</span><span class="o">=</span><span class="p">{</span><span class="s2">&quot;repo_demo_pipeline&quot;</span><span class="p">:</span> <span class="n">define_repo_demo_pipeline</span><span class="p">},</span>
    <span class="p">)</span>
</pre></div>
</td></tr></table></div>
</div>
<p>If you save this file as <code class="docutils literal notranslate"><span class="pre">repos.py</span></code>, you can then run the command line tools on it. Try running:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagster pipeline list -f repos.py -n define_repo
<span class="go">Repository demo_repo</span>
<span class="go">************************</span>
<span class="go">Pipeline: repo_demo_pipeline</span>
<span class="go">Solids: (Execution Order)</span>
<span class="go">    hello_world</span>
</pre></div>
</div>
<p>Typing the name of the file and function defining the repository gets tiresome and repetitive, so
let’s create a declarative config file with this information to make using the command line tools
easier. Save this file as <code class="docutils literal notranslate"><span class="pre">repository.yml</span></code>. This is the default name for a repository config file,
although you can tell the CLI tools to use any file you like.</p>
<div class="literal-block-wrapper docutils container" id="id2">
<div class="code-block-caption"><span class="caption-text">repository.yml</span><a class="headerlink" href="#id2" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre>1
2
3</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="n">repository</span><span class="p">:</span>
  <span class="n">file</span><span class="p">:</span> <span class="n">repos</span><span class="o">.</span><span class="n">py</span>
  <span class="n">fn</span><span class="p">:</span> <span class="n">define_repo</span>
</pre></div>
</td></tr></table></div>
</div>
<p>Now you should be able to list the pipelines in this repo without all the typing:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagster pipeline list
<span class="go">Repository demo_repo</span>
<span class="go">************************</span>
<span class="go">Pipeline: repo_demo_pipeline</span>
<span class="go">Solids: (Execution Order)</span>
<span class="go">    hello_world</span>
</pre></div>
</div>
<p>You can also specify a module instead of a file in the repository.yml file.</p>
<div class="literal-block-wrapper docutils container" id="id3">
<div class="code-block-caption"><span class="caption-text">repository.yml</span><a class="headerlink" href="#id3" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre>1
2
3</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="n">repository</span><span class="p">:</span>
    <span class="n">module</span><span class="p">:</span> <span class="n">dagster</span><span class="o">.</span><span class="n">tutorials</span><span class="o">.</span><span class="n">intro_tutorial</span><span class="o">.</span><span class="n">repos</span>
    <span class="n">fn</span><span class="p">:</span> <span class="n">define_repo</span> 
</pre></div>
</td></tr></table></div>
</div>
<div class="section" id="dagit">
<h2>Dagit<a class="headerlink" href="#dagit" title="Permalink to this headline">¶</a></h2>
<p>Dagit uses the same pattern as the other dagster CLI tools. If you’ve defined a repository.yml file,
just run dagit with no arguments, and you can visualize and execute all the pipelines in your
repository:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagit
<span class="go">Serving on http://localhost:3000</span>
</pre></div>
</div>
<img alt="../_images/repos_figure_one.png" src="../_images/repos_figure_one.png" />
<p>In the next part of the tutorial, we’ll get to know <a class="reference internal" href="pipeline_execution.html"><span class="doc">Pipeline Execution</span></a>
a little better, and learn how to execute pipelines in a repository from the command line by name,
with swappable config.</p>
</div>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="execution_context.html">Execution Context</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="execution_context.html" title="previous chapter">Execution Context</a></li>
      <li>Next: <a href="pipeline_execution.html" title="next chapter">Pipeline Execution</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/repos.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/repos.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 13'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Pipeline Execution &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="Configuration Schemas" href="configuration_schemas.html" />
    <link rel="prev" title="Repositories" href="repos.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="pipeline-execution">
<h1>Pipeline Execution<a class="headerlink" href="#pipeline-execution" title="Permalink to this headline">¶</a></h1>
<p>Just as in the last part of the tutorial, we’ll define a pipeline and a repository, and create
a yaml file to tell the CLI tool about the repository.</p>
<div class="literal-block-wrapper docutils container" id="id1">
<div class="code-block-caption"><span class="caption-text">pipeline_execution.py</span><a class="headerlink" href="#id1" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre> 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="kn">from</span> <span class="nn">collections</span> <span class="k">import</span> <span class="n">defaultdict</span>

<span class="kn">from</span> <span class="nn">dagster</span> <span class="k">import</span> <span class="p">(</span>
    <span class="n">DependencyDefinition</span><span class="p">,</span>
    <span class="n">Dict</span><span class="p">,</span>
    <span class="n">Field</span><span class="p">,</span>
    <span class="n">InputDefinition</span><span class="p">,</span>
    <span class="n">PipelineDefinition</span><span class="p">,</span>
    <span class="n">String</span><span class="p">,</span>
    <span class="n">lambda_solid</span><span class="p">,</span>
    <span class="n">solid</span><span class="p">,</span>
<span class="p">)</span>


<span class="nd">@solid</span><span class="p">(</span><span class="n">config_field</span><span class="o">=</span><span class="n">Field</span><span class="p">(</span><span class="n">Dict</span><span class="p">({</span><span class="s1">&#39;word&#39;</span><span class="p">:</span> <span class="n">Field</span><span class="p">(</span><span class="n">String</span><span class="p">)})))</span>
<span class="k">def</span> <span class="nf">double_the_word</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">[</span><span class="s1">&#39;word&#39;</span><span class="p">]</span> <span class="o">*</span> <span class="mi">2</span>


<span class="nd">@lambda_solid</span><span class="p">(</span><span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;word&#39;</span><span class="p">)])</span>
<span class="k">def</span> <span class="nf">count_letters</span><span class="p">(</span><span class="n">word</span><span class="p">):</span>
    <span class="n">counts</span> <span class="o">=</span> <span class="n">defaultdict</span><span class="p">(</span><span class="nb">int</span><span class="p">)</span>
    <span class="k">for</span> <span class="n">letter</span> <span class="ow">in</span> <span class="n">word</span><span class="p">:</span>
        <span class="n">counts</span><span class="p">[</span><span class="n">letter</span><span class="p">]</span> <span class="o">+=</span> <span class="mi">1</span>
    <span class="k">return</span> <span class="nb">dict</span><span class="p">(</span><span class="n">counts</span><span class="p">)</span>


<span class="k">def</span> <span class="nf">define_demo_execution_pipeline</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;demo_execution&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">double_the_word</span><span class="p">,</span> <span class="n">count_letters</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;count_letters&#39;</span><span class="p">:</span> <span class="p">{</span><span class="s1">&#39;word&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;double_the_word&#39;</span><span class="p">)}</span>
        <span class="p">},</span>
    <span class="p">)</span>


<span class="k">def</span> <span class="nf">define_demo_execution_repo</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">RepositoryDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;demo_execution_repo&#39;</span><span class="p">,</span>
        <span class="n">pipeline_dict</span><span class="o">=</span><span class="p">{</span><span class="s1">&#39;part_seven&#39;</span><span class="p">:</span> <span class="n">define_demo_execution_pipeline</span><span class="p">},</span>
    <span class="p">)</span>
</pre></div>
</td></tr></table></div>
</div>
<p>And now the repository file:</p>
<div class="literal-block-wrapper docutils container" id="id2">
<div class="code-block-caption"><span class="caption-text">repository.yml</span><a class="headerlink" href="#id2" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre>1
2
3</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="n">repository</span><span class="p">:</span>
  <span class="n">file</span><span class="p">:</span> <span class="n">pipeline_execution</span><span class="o">.</span><span class="n">py</span>
  <span class="n">fn</span><span class="p">:</span> <span class="n">define_demo_execution_repo</span>
</pre></div>
</td></tr></table></div>
</div>
<p>Finally, we’ll need to define the pipeline config in a yaml file in order to
execute our pipeline from the command line.</p>
<div class="literal-block-wrapper docutils container" id="id3">
<div class="code-block-caption"><span class="caption-text">env.yml</span><a class="headerlink" href="#id3" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre>1
2
3
4
5
6
7
8
9</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="n">context</span><span class="p">:</span>
  <span class="n">default</span><span class="p">:</span>
    <span class="n">config</span><span class="p">:</span>
      <span class="n">log_level</span><span class="p">:</span> <span class="n">DEBUG</span>

<span class="n">solids</span><span class="p">:</span>
  <span class="n">double_the_word</span><span class="p">:</span>
    <span class="n">config</span><span class="p">:</span>
      <span class="n">word</span><span class="p">:</span> <span class="n">bar</span>
</pre></div>
</td></tr></table></div>
</div>
<p>With these elements in place we can now drive execution from the CLI specifying only the pipeline
name. The tool loads the repository using the <cite>repository.yml</cite> file and looks up the pipeline by
name.</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagster pipeline execute part_seven -e env.yml
</pre></div>
</div>
<p>Suppose that we want to keep some settings (like our context-level logging config) constant across
a bunch of our pipeline executions, and vary only pipeline-specific settings. It’d be tedious to
copy the broadly-applicable settings into each of our config yamls, and error-prone to try to keep
those copies in sync. So the command line tools allow us to specify more than one yaml file to use
for config.</p>
<p>Let’s split up our env.yml into two parts:</p>
<div class="literal-block-wrapper docutils container" id="id4">
<div class="code-block-caption"><span class="caption-text">constant_env.yml</span><a class="headerlink" href="#id4" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">context</span><span class="p">:</span>
  <span class="n">default</span><span class="p">:</span>
    <span class="n">config</span><span class="p">:</span>
      <span class="n">log_level</span><span class="p">:</span> <span class="n">DEBUG</span>
</pre></div>
</div>
</div>
<div class="literal-block-wrapper docutils container" id="id5">
<div class="code-block-caption"><span class="caption-text">specific_env.yml</span><a class="headerlink" href="#id5" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">solids</span><span class="p">:</span>
  <span class="n">double_the_word</span><span class="p">:</span>
    <span class="n">config</span><span class="p">:</span>
      <span class="n">word</span><span class="p">:</span> <span class="n">bar</span>
</pre></div>
</div>
</div>
<p>Now we can run our pipeline as follows:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagster pipeline execute part_seven -e constant_env.yml -e specific_env.yml
</pre></div>
</div>
<p>Order matters when specifying yaml files to use – values specified in later files will override
values in earlier files, which can be useful. You can also use globs in the CLI arguments to consume
multiple yaml files.</p>
<p>Next, we’ll look at defining strongly-typed <a class="reference internal" href="configuration_schemas.html"><span class="doc">Configuration Schemas</span></a>
to guard against bugs and enrich pipeline documentation.</p>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="repos.html">Repositories</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="repos.html" title="previous chapter">Repositories</a></li>
      <li>Next: <a href="configuration_schemas.html" title="next chapter">Configuration Schemas</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/pipeline_execution.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/pipeline_execution.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 14'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Expectations &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="Multiple Outputs" href="part_eleven.html" />
    <link rel="prev" title="Custom Contexts" href="part_nine.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="expectations">
<h1>Expectations<a class="headerlink" href="#expectations" title="Permalink to this headline">¶</a></h1>
<p>Dagster has a first-class concept to capture data quality tests. We call these
data quality tests expectations.</p>
<p>Data pipelines have the property that they typically do not control
what data they ingest. Unlike a traditional application where you can
prevent users from entering malformed data, data pipelines do not have
that option. When unexpected data enters a pipeline and causes a software
error, typically the only recourse is to update your code.</p>
<p>Lying within the code of data pipelines are a whole host of implicit
assumptions about the nature of the data. One way to frame the goal of
expectations is to say that they make those implict assumption explicit.
And by making these a first class concept they can be described with metadata,
inspected, and configured to run in different ways.</p>
<p>Let us return to a slightly simplified version of the data pipeline from part nine.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">ConfigDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">ingest_a</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span>


<span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">ConfigDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">ingest_b</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span>

<span class="nd">@solid</span><span class="p">(</span>
    <span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num_one&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
            <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num_two&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">add_ints</span><span class="p">(</span><span class="n">_info</span><span class="p">,</span> <span class="n">num_one</span><span class="p">,</span> <span class="n">num_two</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">num_one</span> <span class="o">+</span> <span class="n">num_two</span>


<span class="k">def</span> <span class="nf">define_part_ten_step_one</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;part_ten_step_one&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">ingest_a</span><span class="p">,</span> <span class="n">ingest_b</span><span class="p">,</span> <span class="n">add_ints</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;add_ints&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;num_one&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;ingest_a&#39;</span><span class="p">),</span>
                <span class="s1">&#39;num_two&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;ingest_b&#39;</span><span class="p">),</span>
            <span class="p">},</span>
        <span class="p">},</span>
    <span class="p">)</span>
</pre></div>
</div>
<p>Imagine that we had assumptions baked into the code of this pipeline such that the code only
worked on positive numbers, and we wanted to communicate that requirement to the user
in clear terms. We’ll add an expectation in order to do this.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">ConfigDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span>
        <span class="n">OutputDefinition</span><span class="p">(</span>
            <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">,</span>
            <span class="n">expectations</span><span class="o">=</span><span class="p">[</span>
                <span class="n">ExpectationDefinition</span><span class="p">(</span>
                    <span class="n">name</span><span class="o">=</span><span class="s2">&quot;check_positive&quot;</span><span class="p">,</span>
                    <span class="n">expectation_fn</span><span class="o">=</span><span class="k">lambda</span> <span class="n">_info</span><span class="p">,</span> <span class="n">value</span><span class="p">:</span> <span class="n">ExpectationResult</span><span class="p">(</span><span class="n">success</span><span class="o">=</span><span class="n">value</span> <span class="o">&gt;</span> <span class="mi">0</span><span class="p">)</span>
                <span class="p">),</span>
            <span class="p">],</span>
        <span class="p">),</span>
    <span class="p">],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">ingest_a</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span>
</pre></div>
</div>
<p>You’ll notice that we added an ExpectationDefinition to the output of ingest_a. Expectations
can be attached to inputs or outputs and operate on the value of that input or output.</p>
<p>Expectations perform arbitrary computation on that value and then return an ExpectationResult.
The user communicates whether or not the expectation succeeded via this return value.</p>
<p>If you run this pipeline, you’ll notice some logging that indicates that the expectation
was processed:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="n">execute_pipeline</span><span class="p">(</span>
    <span class="n">define_part_ten_step_one</span><span class="p">(),</span>
    <span class="p">{</span>
        <span class="s1">&#39;context&#39;</span><span class="p">:</span> <span class="p">{</span>
            <span class="s1">&#39;default&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="p">{</span>
                    <span class="s1">&#39;log_level&#39;</span><span class="p">:</span> <span class="s1">&#39;DEBUG&#39;</span><span class="p">,</span>
                <span class="p">}</span>
            <span class="p">}</span>
        <span class="p">},</span>
        <span class="s1">&#39;solids&#39;</span><span class="p">:</span> <span class="p">{</span>
            <span class="s1">&#39;ingest_a&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="mi">2</span><span class="p">,</span>
            <span class="p">},</span>
            <span class="s1">&#39;ingest_b&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="mi">3</span><span class="p">,</span>
            <span class="p">},</span>
        <span class="p">}</span>
    <span class="p">},</span>
<span class="p">)</span>
</pre></div>
</div>
<p>And run it…</p>
<div class="highlight-sh notranslate"><div class="highlight"><pre><span></span>$ python part_ten.py
... log spew
<span class="m">2018</span>-09-14 <span class="m">13</span>:13:13 - dagster - DEBUG - <span class="nv">orig_message</span><span class="o">=</span><span class="s2">&quot;Expectation ingest_a.result.expectation.check_positive succeeded on 2.&quot;</span> <span class="nv">log_message_id</span><span class="o">=</span><span class="s2">&quot;938ab7fa-c955-408a-9f44-66b0b6ecdcad&quot;</span> <span class="nv">pipeline</span><span class="o">=</span><span class="s2">&quot;part_ten_step_one&quot;</span> <span class="nv">solid</span><span class="o">=</span><span class="s2">&quot;ingest_a&quot;</span> <span class="nv">output</span><span class="o">=</span><span class="s2">&quot;result&quot;</span> <span class="nv">expectation</span><span class="o">=</span><span class="s2">&quot;check_positive&quot;</span>
... more log spew
</pre></div>
</div>
<p>Now let’s make this fail. Currently the default behavior is to throw an error and halt execution
when an expectation fails. So:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="n">execute_pipeline</span><span class="p">(</span>
    <span class="n">define_part_ten_step_one</span><span class="p">(),</span>
    <span class="p">{</span>
        <span class="s1">&#39;context&#39;</span><span class="p">:</span> <span class="p">{</span>
            <span class="s1">&#39;default&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="p">{</span>
                    <span class="s1">&#39;log_level&#39;</span><span class="p">:</span> <span class="s1">&#39;DEBUG&#39;</span><span class="p">,</span>
                <span class="p">}</span>
            <span class="p">}</span>
        <span class="p">},</span>
        <span class="s1">&#39;solids&#39;</span><span class="p">:</span> <span class="p">{</span>
            <span class="s1">&#39;ingest_a&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="o">-</span><span class="mi">5</span><span class="p">,</span>
            <span class="p">},</span>
            <span class="s1">&#39;ingest_b&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="mi">3</span><span class="p">,</span>
            <span class="p">},</span>
        <span class="p">}</span>
    <span class="p">},</span>
<span class="p">)</span>
</pre></div>
</div>
<p>And then:</p>
<div class="highlight-sh notranslate"><div class="highlight"><pre><span></span>$ python part_ten.py
... bunch of log spew
dagster.core.errors.DagsterExpectationFailedError: DagsterExpectationFailedError<span class="o">(</span><span class="nv">solid</span><span class="o">=</span>add_ints, <span class="nv">output</span><span class="o">=</span>result, <span class="nv">expectation</span><span class="o">=</span><span class="nv">check_positivevalue</span><span class="o">=</span>-2<span class="o">)</span>
</pre></div>
</div>
<p>We can also tell execute_pipeline to not throw on error:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="n">execute_pipeline</span><span class="p">(</span>
    <span class="n">define_part_ten_step_one</span><span class="p">(),</span>
    <span class="p">{</span>
        <span class="s1">&#39;context&#39;</span><span class="p">:</span> <span class="p">{</span>
            <span class="s1">&#39;default&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="p">{</span>
                    <span class="s1">&#39;log_level&#39;</span><span class="p">:</span> <span class="s1">&#39;DEBUG&#39;</span><span class="p">,</span>
                <span class="p">}</span>
            <span class="p">}</span>
        <span class="p">},</span>
        <span class="s1">&#39;solids&#39;</span><span class="p">:</span> <span class="p">{</span>
            <span class="s1">&#39;ingest_a&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="o">-</span><span class="mi">5</span><span class="p">,</span>
            <span class="p">},</span>
            <span class="s1">&#39;ingest_b&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="mi">3</span><span class="p">,</span>
            <span class="p">},</span>
        <span class="p">}</span>
    <span class="p">},</span>
    <span class="n">throw_on_error</span><span class="o">=</span><span class="bp">False</span><span class="p">,</span>
<span class="p">)</span>
</pre></div>
</div>
<div class="highlight-sh notranslate"><div class="highlight"><pre><span></span>$ python part_ten.py
... log spew
<span class="m">2018</span>-11-08 <span class="m">10</span>:38:28 - dagster - DEBUG - <span class="nv">orig_message</span><span class="o">=</span><span class="s2">&quot;Expectation add_ints.result.expectation.check_positive failed on -2.&quot;</span> <span class="nv">log_message_id</span><span class="o">=</span><span class="s2">&quot;9ca21f5c-0578-4b3f-80c2-d129552525a4&quot;</span> <span class="nv">run_id</span><span class="o">=</span><span class="s2">&quot;c12bdc2d-c008-47db-8b76-e257262eab79&quot;</span> <span class="nv">pipeline</span><span class="o">=</span><span class="s2">&quot;part_ten_step_one&quot;</span> <span class="nv">solid</span><span class="o">=</span><span class="s2">&quot;add_ints&quot;</span> <span class="nv">output</span><span class="o">=</span><span class="s2">&quot;result&quot;</span> <span class="nv">expectation</span><span class="o">=</span><span class="s2">&quot;check_positive&quot;</span>
</pre></div>
</div>
<p>Because the system is explictly aware of these expectations they are viewable in tools like dagit.
It can also configure the execution of these expectations. The capabilities of this aspect of the
system are currently quite immature, but we expect to develop these more in the future. The only
feature right now is the ability to skip expectations entirely. This is useful in a case where
expectations are expensive and you have a time-critical job you must. In that case you can
configure the pipeline to skip expectations entirely.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="n">execute_pipeline</span><span class="p">(</span>
    <span class="n">define_part_ten_step_one</span><span class="p">(),</span>
    <span class="p">{</span>
        <span class="s1">&#39;context&#39;</span><span class="p">:</span> <span class="p">{</span>
            <span class="s1">&#39;default&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="p">{</span>
                    <span class="s1">&#39;log_level&#39;</span><span class="p">:</span> <span class="s1">&#39;DEBUG&#39;</span><span class="p">,</span>
                <span class="p">}</span>
            <span class="p">}</span>
        <span class="p">},</span>
        <span class="s1">&#39;solids&#39;</span><span class="p">:</span> <span class="p">{</span>
            <span class="s1">&#39;ingest_a&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="mi">2</span><span class="p">,</span>
            <span class="p">},</span>
            <span class="s1">&#39;ingest_b&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="mi">3</span><span class="p">,</span>
            <span class="p">},</span>
        <span class="p">},</span>
        <span class="s1">&#39;expectations&#39;</span><span class="p">:</span> <span class="p">{</span>
            <span class="s1">&#39;evaluate&#39;</span><span class="p">:</span> <span class="bp">False</span><span class="p">,</span>
        <span class="p">},</span>
    <span class="p">},</span>
<span class="p">)</span>
</pre></div>
</div>
<div class="highlight-sh notranslate"><div class="highlight"><pre><span></span>$ python part_ten.py
... expectations will not in the log spew
</pre></div>
</div>
<p>We plan on adding more sophisticated capabilties to this in the future.</p>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="part_nine.html" title="previous chapter">Custom Contexts</a></li>
      <li>Next: <a href="part_eleven.html" title="next chapter">Multiple Outputs</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/part_ten.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/part_ten.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 15'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Execution Context &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="Repositories" href="repos.html" />
    <link rel="prev" title="Configuration" href="config.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="execution-context">
<h1>Execution Context<a class="headerlink" href="#execution-context" title="Permalink to this headline">¶</a></h1>
<p>We use <strong>configuration</strong> to set parameters on a per-solid basis. The <strong>execution context</strong> lets
us set parameters for the entire pipeline.</p>
<p>The execution context is exposed to individual solids as the <code class="docutils literal notranslate"><span class="pre">context</span></code> property of the <code class="docutils literal notranslate"><span class="pre">info</span></code>
object. The context is an object of type <a class="reference internal" href="../apidocs/execution.html#dagster.ExecutionContext" title="dagster.ExecutionContext"><code class="xref py py-class docutils literal notranslate"><span class="pre">ExecutionContext</span></code></a>.
For every execution of a particular pipeline, one instance of this context is created, no matter how
many solids are involved. Runtime state or information that is particular to a single execution,
rather than particular to an individual solid, should be associated with the context.</p>
<p>One of the most basic pipeline-level facilities is logging.</p>
<div class="literal-block-wrapper docutils container" id="id1">
<div class="code-block-caption"><span class="caption-text">execution_context.py</span><a class="headerlink" href="#id1" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="kn">from</span> <span class="nn">dagster</span> <span class="k">import</span> <span class="n">PipelineDefinition</span><span class="p">,</span> <span class="n">execute_pipeline</span><span class="p">,</span> <span class="n">solid</span>


<span class="nd">@solid</span>
<span class="k">def</span> <span class="nf">debug_message</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="o">.</span><span class="n">debug</span><span class="p">(</span><span class="s1">&#39;A debug message.&#39;</span><span class="p">)</span>
    <span class="k">return</span> <span class="s1">&#39;foo&#39;</span>


<span class="nd">@solid</span>
<span class="k">def</span> <span class="nf">error_message</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="o">.</span><span class="n">error</span><span class="p">(</span><span class="s1">&#39;An error occurred.&#39;</span><span class="p">)</span>


<span class="k">def</span> <span class="nf">define_execution_context_pipeline_step_one</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span><span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">debug_message</span><span class="p">,</span> <span class="n">error_message</span><span class="p">])</span>
</pre></div>
</div>
</div>
<p>If you run this either on the command line or in dagit, you’ll see our new error message pop up
in the logs.</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagster pipeline execute -f execution_context.py -n define_execution_context_pipeline_step_one
<span class="go">...</span>
<span class="go">2018-12-17 16:06:53 - dagster - ERROR - orig_message=&quot;An error occurred.&quot; log_message_id=&quot;89211a12-4f75-4aa0-a1d6-786032641986&quot; run_id=&quot;40a9b608-c98f-4200-9f4a-aab70a2cb603&quot; pipeline=&quot;&lt;&lt;unnamed&gt;&gt;&quot; solid=&quot;solid_two&quot; solid_definition=&quot;solid_two&quot;</span>
<span class="go">...</span>
</pre></div>
</div>
<p>Notice that even though the user only logged the message “An error occurred”, by routing logging
through the context we are able to provide richer error information – including the name of the
solid and a timestamp – in a semi-structured format.</p>
<p>(Note that the order of execution of these two solids is indeterminate – they don’t depend on each
other.)</p>
<p>Let’s change the example by adding a name to the pipeline. (Naming things is good practice).</p>
<div class="literal-block-wrapper docutils container" id="id2">
<div class="code-block-caption"><span class="caption-text">execution_context.py</span><a class="headerlink" href="#id2" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="k">def</span> <span class="nf">define_execution_context_pipeline_step_two</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;execution_context_pipeline&#39;</span><span class="p">,</span> <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">debug_message</span><span class="p">,</span> <span class="n">error_message</span><span class="p">]</span>
    <span class="p">)</span>
</pre></div>
</div>
</div>
<p>And then run it:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagster pipeline execute -f execution_context.py -n define_execution_context_pipeline_step_two
<span class="go">...</span>
<span class="go">2018-12-17 16:06:53 - dagster - ERROR - orig_message=&quot;An error occurred.&quot; log_message_id=&quot;89211a12-4f75-4aa0-a1d6-786032641986&quot; run_id=&quot;40a9b608-c98f-4200-9f4a-aab70a2cb603&quot; pipeline=&quot;execution_context_pipeline&quot; solid=&quot;solid_two&quot; solid_definition=&quot;solid_two&quot;</span>
<span class="go">...</span>
</pre></div>
</div>
<p>You’ll note that the metadata in the log message now includes the pipeline name,
<code class="docutils literal notranslate"><span class="pre">execution_context_pipeline</span></code>, where before it was <code class="docutils literal notranslate"><span class="pre">&lt;&lt;unnamed&gt;&gt;</span></code>.</p>
<p>But what about the <code class="docutils literal notranslate"><span class="pre">DEBUG</span></code> message in <code class="docutils literal notranslate"><span class="pre">solid_one</span></code>? The default context provided by dagster
logs error messages to the console only at the <code class="docutils literal notranslate"><span class="pre">INFO</span></code> level or above. (In dagit, you can always
filter error messages at any level.) In order to print <code class="docutils literal notranslate"><span class="pre">DEBUG</span></code> messages to the console, we’ll
use the configuration system again – this time, to configure the context rather than an individual
solid.</p>
<div class="literal-block-wrapper docutils container" id="id3">
<div class="code-block-caption"><span class="caption-text">execution_context.py</span><a class="headerlink" href="#id3" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="k">def</span> <span class="nf">define_execution_context_pipeline_step_three</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;execution_context_pipeline&#39;</span><span class="p">,</span> <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">debug_message</span><span class="p">,</span> <span class="n">error_message</span><span class="p">]</span>
    <span class="p">)</span>
</pre></div>
</div>
</div>
<p>We can use the same config syntax as we’ve seen before in order to configure the pipeline:</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">execute_pipeline</span><span class="p">(</span>
    <span class="n">define_execution_context_pipeline_step_three</span><span class="p">(),</span>
    <span class="p">{</span><span class="s1">&#39;context&#39;</span><span class="p">:</span> <span class="p">{</span><span class="s1">&#39;default&#39;</span><span class="p">:</span> <span class="p">{</span><span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="p">{</span><span class="s1">&#39;log_level&#39;</span><span class="p">:</span> <span class="s1">&#39;DEBUG&#39;</span><span class="p">}}}},</span>
<span class="p">)</span>
</pre></div>
</div>
<p>But in generally, we’ll prefer to use a yaml file to declaratively specify our config.</p>
<p>Separating config into external files is a nice pattern because it allows users who might not be
comfortable in a general-purpose programming environment like Python to do meaningful work
configuring pipelines in a restricted DSL.</p>
<p>Fragments of config expressed in yaml can also be reused (for instance, pipeline-level config that
is common across many projects) or kept out of source control (for instance, credentials or
information specific to a developer environment) and combined at pipeline execution time.</p>
<div class="literal-block-wrapper docutils container" id="id4">
<div class="code-block-caption"><span class="caption-text">execution_context.yml</span><a class="headerlink" href="#id4" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">context</span><span class="p">:</span>
  <span class="n">default</span><span class="p">:</span>
    <span class="n">config</span><span class="p">:</span>
      <span class="n">log_level</span><span class="p">:</span> <span class="n">DEBUG</span>
</pre></div>
</div>
</div>
<p>If we re-run the pipeline, you’ll see a lot more output, now including our custom <code class="docutils literal notranslate"><span class="pre">DEBUG</span></code> message.</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagster pipeline execute -f execution_context.py <span class="se">\\</span>
-n define_execution_context_pipeline_step_three -e execution_context.yaml
<span class="go">...</span>
<span class="go">2018-12-17 17:18:06 - dagster - DEBUG - orig_message=&quot;A debug message.&quot; log_message_id=&quot;497c9d47-571a-44f6-a04c-8f24049b0f66&quot; run_id=&quot;5b233906-9b36-4f15-a220-a850a1643b9f&quot; pipeline=&quot;execution_context_pipeline&quot; solid=&quot;solid_one&quot; solid_definition=&quot;solid_one&quot;</span>
<span class="go">...</span>
</pre></div>
</div>
<p>Although logging is a universally useful case for the execution context, this example only touches
on the capabilities of the context. Any pipeline-level facilities that pipeline authors might want
to make configurable for different environments – for instance, access to file systems, databases,
or compute substrates – can be configured using the context.</p>
<p>This is how pipelines can be made executable in different operating environments (e.g. unit-testing,
CI/CD, prod, etc) without changing business logic.</p>
<p>Next, we’ll see how to declare <a class="reference internal" href="repos.html"><span class="doc">Repositories</span></a>, which let us group pipelines together
so that the dagster tools can manage them.</p>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="config.html">Configuration</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="config.html" title="previous chapter">Configuration</a></li>
      <li>Next: <a href="repos.html" title="next chapter">Repositories</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/execution_context.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/execution_context.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 16'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>An actual DAG &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="Inputs" href="inputs.html" />
    <link rel="prev" title="Hello, DAG" href="hello_dag.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="an-actual-dag">
<h1>An actual DAG<a class="headerlink" href="#an-actual-dag" title="Permalink to this headline">¶</a></h1>
<p>Next we will build a slightly more topologically complex DAG that demonstrates how dagster
determines the execution order of solids in a pipeline:</p>
<img alt="../_images/actual_dag_figure_one.png" src="../_images/actual_dag_figure_one.png" />
<div class="literal-block-wrapper docutils container" id="id1">
<div class="code-block-caption"><span class="caption-text">actual_dag.py</span><a class="headerlink" href="#id1" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre> 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="kn">from</span> <span class="nn">dagster</span> <span class="k">import</span> <span class="p">(</span>
    <span class="n">DependencyDefinition</span><span class="p">,</span>
    <span class="n">InputDefinition</span><span class="p">,</span>
    <span class="n">PipelineDefinition</span><span class="p">,</span>
    <span class="n">lambda_solid</span><span class="p">,</span>
<span class="p">)</span>


<span class="nd">@lambda_solid</span>
<span class="k">def</span> <span class="nf">solid_a</span><span class="p">():</span>
    <span class="k">return</span> <span class="mi">1</span>


<span class="nd">@lambda_solid</span><span class="p">(</span><span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s2">&quot;arg_a&quot;</span><span class="p">)])</span>
<span class="k">def</span> <span class="nf">solid_b</span><span class="p">(</span><span class="n">arg_a</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">arg_a</span> <span class="o">*</span> <span class="mi">2</span>


<span class="nd">@lambda_solid</span><span class="p">(</span><span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s2">&quot;arg_a&quot;</span><span class="p">)])</span>
<span class="k">def</span> <span class="nf">solid_c</span><span class="p">(</span><span class="n">arg_a</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">arg_a</span> <span class="o">*</span> <span class="mi">3</span>


<span class="nd">@lambda_solid</span><span class="p">(</span><span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s2">&quot;arg_b&quot;</span><span class="p">),</span> <span class="n">InputDefinition</span><span class="p">(</span><span class="s2">&quot;arg_c&quot;</span><span class="p">)])</span>
<span class="k">def</span> <span class="nf">solid_d</span><span class="p">(</span><span class="n">arg_b</span><span class="p">,</span> <span class="n">arg_c</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">arg_b</span> <span class="o">*</span> <span class="n">arg_c</span>


<span class="k">def</span> <span class="nf">define_diamond_dag_pipeline</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s2">&quot;actual_dag_pipeline&quot;</span><span class="p">,</span>
        <span class="c1"># The order of this list does not matter:</span>
        <span class="c1"># dependencies determine execution order</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">solid_d</span><span class="p">,</span> <span class="n">solid_c</span><span class="p">,</span> <span class="n">solid_b</span><span class="p">,</span> <span class="n">solid_a</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s2">&quot;solid_b&quot;</span><span class="p">:</span> <span class="p">{</span><span class="s2">&quot;arg_a&quot;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s2">&quot;solid_a&quot;</span><span class="p">)},</span>
            <span class="s2">&quot;solid_c&quot;</span><span class="p">:</span> <span class="p">{</span><span class="s2">&quot;arg_a&quot;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s2">&quot;solid_a&quot;</span><span class="p">)},</span>
            <span class="s2">&quot;solid_d&quot;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s2">&quot;arg_b&quot;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s2">&quot;solid_b&quot;</span><span class="p">),</span>
                <span class="s2">&quot;arg_c&quot;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s2">&quot;solid_c&quot;</span><span class="p">),</span>
            <span class="p">},</span>
        <span class="p">},</span>
    <span class="p">)</span>
</pre></div>
</td></tr></table></div>
</div>
<p>Again, it is worth noting how we are connecting <em>inputs</em> and <em>outputs</em> rather than just <em>tasks</em>.
Point your attention to the <code class="docutils literal notranslate"><span class="pre">solid_d</span></code> entry in the dependencies dictionary: we declare
dependencies on a per-input basis.</p>
<p>When you execute this example, you’ll see that <code class="docutils literal notranslate"><span class="pre">solid_a</span></code> executes first, then <code class="docutils literal notranslate"><span class="pre">solid_b</span></code> and
<code class="docutils literal notranslate"><span class="pre">solid_c</span></code> – in any order – and <code class="docutils literal notranslate"><span class="pre">solid_d</span></code> executes last, after <code class="docutils literal notranslate"><span class="pre">solid_b</span></code> and <code class="docutils literal notranslate"><span class="pre">solid_c</span></code>
have both executed.</p>
<p>In more sophisticated execution environments, <code class="docutils literal notranslate"><span class="pre">solid_b</span></code> and <code class="docutils literal notranslate"><span class="pre">solid_c</span></code> could execute not just
in any order, but at the same time, since their inputs don’t depend on each other’s outputs –
but both would still have to execute after <code class="docutils literal notranslate"><span class="pre">solid_a</span></code> (because they depend on its output to
satisfy their inputs) and before <code class="docutils literal notranslate"><span class="pre">solid_d</span></code> (because their outputs in turn are depended on by
the input of <code class="docutils literal notranslate"><span class="pre">solid_d</span></code>).</p>
<p>Try it in dagit or from the command line:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagster pipeline execute -f actual_dag.py -n define_diamond_dag_pipeline
</pre></div>
</div>
<p>What’s the output of this DAG?</p>
<p>We’ve seen how to wire solids together into DAGs. Now let’s look more deeply at their
<a class="reference internal" href="inputs.html"><span class="doc">Inputs</span></a>, and start to explore how solids can interact with their external
environment.</p>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="hello_dag.html" title="previous chapter">Hello, DAG</a></li>
      <li>Next: <a href="inputs.html" title="next chapter">Inputs</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/actual_dag.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/actual_dag.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 17'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Multiple Outputs &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="User-defined Types" href="part_twelve.html" />
    <link rel="prev" title="Expectations" href="part_ten.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="multiple-outputs">
<h1>Multiple Outputs<a class="headerlink" href="#multiple-outputs" title="Permalink to this headline">¶</a></h1>
<p>So far all of the examples have been solids that have a single output. However
solids support an arbitrary number of outputs. This allows for downstream
solids to only tie their dependency to a single output. Additionally – by
allowing for multiple outputs to conditionally fire – this also ends up
supporting dynamic branching and conditional execution of pipelines.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@solid</span><span class="p">(</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span>
        <span class="n">OutputDefinition</span><span class="p">(</span><span class="n">runtime_type</span><span class="o">=</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">,</span> <span class="n">name</span><span class="o">=</span><span class="s1">&#39;out_one&#39;</span><span class="p">),</span>
        <span class="n">OutputDefinition</span><span class="p">(</span><span class="n">runtime_type</span><span class="o">=</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">,</span> <span class="n">name</span><span class="o">=</span><span class="s1">&#39;out_two&#39;</span><span class="p">),</span>
    <span class="p">],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">return_dict_results</span><span class="p">(</span><span class="n">_info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">MultipleResults</span><span class="o">.</span><span class="n">from_dict</span><span class="p">({</span>
        <span class="s1">&#39;out_one&#39;</span><span class="p">:</span> <span class="mi">23</span><span class="p">,</span>
        <span class="s1">&#39;out_two&#39;</span><span class="p">:</span> <span class="mi">45</span><span class="p">,</span>
    <span class="p">})</span>

<span class="nd">@solid</span><span class="p">(</span><span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num&#39;</span><span class="p">,</span> <span class="n">runtime_type</span><span class="o">=</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)])</span>
<span class="k">def</span> <span class="nf">log_num</span><span class="p">(</span><span class="n">info</span><span class="p">,</span> <span class="n">num</span><span class="p">):</span>
    <span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="o">.</span><span class="n">info</span><span class="p">(</span><span class="s1">&#39;num {num}&#39;</span><span class="o">.</span><span class="n">format</span><span class="p">(</span><span class="n">num</span><span class="o">=</span><span class="n">num</span><span class="p">))</span>
    <span class="k">return</span> <span class="n">num</span>

<span class="nd">@solid</span><span class="p">(</span><span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num&#39;</span><span class="p">,</span> <span class="n">runtime_type</span><span class="o">=</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)])</span>
<span class="k">def</span> <span class="nf">log_num_squared</span><span class="p">(</span><span class="n">info</span><span class="p">,</span> <span class="n">num</span><span class="p">):</span>
    <span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="o">.</span><span class="n">info</span><span class="p">(</span>
        <span class="s1">&#39;num_squared {num_squared}&#39;</span><span class="o">.</span><span class="n">format</span><span class="p">(</span><span class="n">num_squared</span><span class="o">=</span><span class="n">num</span> <span class="o">*</span> <span class="n">num</span><span class="p">)</span>
    <span class="p">)</span>
    <span class="k">return</span> <span class="n">num</span> <span class="o">*</span> <span class="n">num</span>
</pre></div>
</div>
<p>Notice how <code class="docutils literal notranslate"><span class="pre">return_dict_results</span></code> has two outputs. For the first time
we have provided the name argument to an <code class="xref py py-class docutils literal notranslate"><span class="pre">OutputDefinition</span></code>. (It
defaults to <code class="docutils literal notranslate"><span class="pre">\'result\'</span></code>, as it does in a <code class="xref py py-class docutils literal notranslate"><span class="pre">DependencyDefinition</span></code>)
These names must be unique and results returns by a solid transform function
must be named one of these inputs. (In all previous examples the value returned
by the transform had been implicitly wrapped in a <code class="xref py py-class docutils literal notranslate"><span class="pre">Result</span></code> object
with the name <code class="docutils literal notranslate"><span class="pre">\'result\'</span></code>.)</p>
<p>So from <code class="docutils literal notranslate"><span class="pre">return_dict_results</span></code> we used <code class="xref py py-class docutils literal notranslate"><span class="pre">MultipleResults</span></code> to return
all outputs from this transform.</p>
<p>Next let’s examine the <code class="xref py py-class docutils literal notranslate"><span class="pre">PipelineDefinition</span></code>:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="k">def</span> <span class="nf">define_part_eleven_step_one</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;part_eleven_step_one&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">return_dict_results</span><span class="p">,</span> <span class="n">log_num</span><span class="p">,</span> <span class="n">log_num_squared</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;log_num&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;num&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span>
                    <span class="s1">&#39;return_dict_results&#39;</span><span class="p">,</span>
                    <span class="s1">&#39;out_one&#39;</span><span class="p">,</span>
                <span class="p">),</span>
            <span class="p">},</span>
            <span class="s1">&#39;log_num_squared&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;num&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span>
                    <span class="s1">&#39;return_dict_results&#39;</span><span class="p">,</span>
                    <span class="s1">&#39;out_two&#39;</span><span class="p">,</span>
                <span class="p">),</span>
            <span class="p">},</span>
        <span class="p">},</span>
    <span class="p">)</span>
</pre></div>
</div>
<p>Just like this tutorial is the first example of an <code class="xref py py-class docutils literal notranslate"><span class="pre">OutputDefinition</span></code> with
a name, this is also the first time that a <code class="xref py py-class docutils literal notranslate"><span class="pre">DependencyDefinition</span></code> has
specified name, because dependencies point to a particular <strong>output</strong> of a solid,
rather than to the solid itself. In previous examples the name of output has
defaulted to <code class="docutils literal notranslate"><span class="pre">\'result\'</span></code>.</p>
<p>With this we can run the pipeline:</p>
<div class="highlight-sh notranslate"><div class="highlight"><pre><span></span>python step_eleven.py
... log spew
<span class="m">2018</span>-11-08 <span class="m">10</span>:52:06 - dagster - INFO - <span class="nv">orig_message</span><span class="o">=</span><span class="s2">&quot;Solid return_dict_results emittedoutput \\&quot;out_one\\&quot; value 23&quot;</span> <span class="nv">log_message_id</span><span class="o">=</span><span class="s2">&quot;7d62dcbf-583d-4640-941f-48cda39e79a1&quot;</span> <span class="nv">run_id</span><span class="o">=</span><span class="s2">&quot;9de556c1-7f4d-4702-95af-6d6dbe6b296b&quot;</span> <span class="nv">pipeline</span><span class="o">=</span><span class="s2">&quot;part_eleven_step_one&quot;</span> <span class="nv">solid</span><span class="o">=</span><span class="s2">&quot;return_dict_results&quot;</span> <span class="nv">solid_definition</span><span class="o">=</span><span class="s2">&quot;return_dict_results&quot;</span>
<span class="m">2018</span>-11-08 <span class="m">10</span>:52:06 - dagster - INFO - <span class="nv">orig_message</span><span class="o">=</span><span class="s2">&quot;Solid return_dict_results emittedoutput \\&quot;out_two\\&quot; value 45&quot;</span> <span class="nv">log_message_id</span><span class="o">=</span><span class="s2">&quot;cc2ae784-6861-49ef-a463-9cbe4fa0f5e6&quot;</span> <span class="nv">run_id</span><span class="o">=</span><span class="s2">&quot;9de556c1-7f4d-4702-95af-6d6dbe6b296b&quot;</span> <span class="nv">pipeline</span><span class="o">=</span><span class="s2">&quot;part_eleven_step_one&quot;</span> <span class="nv">solid</span><span class="o">=</span><span class="s2">&quot;return_dict_results&quot;</span> <span class="nv">solid_definition</span><span class="o">=</span><span class="s2">&quot;return_dict_results&quot;</span>
... more log spew
</pre></div>
</div>
<p>The <code class="xref py py-class docutils literal notranslate"><span class="pre">MultipleResults</span></code> class is not the only way to return multiple
results from a solid transform function. You can also yield multiple instances
of the <cite>Result</cite> object. (Note: this is actually the core specification
of the transform function: all other forms are implemented in terms of
the iterator form.)</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@solid</span><span class="p">(</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span>
        <span class="n">OutputDefinition</span><span class="p">(</span><span class="n">runtime_type</span><span class="o">=</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">,</span> <span class="n">name</span><span class="o">=</span><span class="s1">&#39;out_one&#39;</span><span class="p">),</span>
        <span class="n">OutputDefinition</span><span class="p">(</span><span class="n">runtime_type</span><span class="o">=</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">,</span> <span class="n">name</span><span class="o">=</span><span class="s1">&#39;out_two&#39;</span><span class="p">),</span>
    <span class="p">],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">yield_outputs</span><span class="p">(</span><span class="n">_info</span><span class="p">):</span>
    <span class="k">yield</span> <span class="n">Result</span><span class="p">(</span><span class="mi">23</span><span class="p">,</span> <span class="s1">&#39;out_one&#39;</span><span class="p">)</span>
    <span class="k">yield</span> <span class="n">Result</span><span class="p">(</span><span class="mi">45</span><span class="p">,</span> <span class="s1">&#39;out_two&#39;</span><span class="p">)</span>

<span class="k">def</span> <span class="nf">define_part_eleven_step_two</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;part_eleven_step_two&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">yield_outputs</span><span class="p">,</span> <span class="n">log_num</span><span class="p">,</span> <span class="n">log_num_squared</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;log_num&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;num&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;yield_outputs&#39;</span><span class="p">,</span> <span class="s1">&#39;out_one&#39;</span><span class="p">)</span>
            <span class="p">},</span>
            <span class="s1">&#39;log_num_squared&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;num&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;yield_outputs&#39;</span><span class="p">,</span> <span class="s1">&#39;out_two&#39;</span><span class="p">)</span>
            <span class="p">},</span>
        <span class="p">},</span>
    <span class="p">)</span>

<span class="k">if</span> <span class="vm">__name__</span> <span class="o">==</span> <span class="s1">&#39;__main__&#39;</span><span class="p">:</span>
    <span class="n">execute_pipeline</span><span class="p">(</span><span class="n">define_part_eleven_step_two</span><span class="p">())</span>
</pre></div>
</div>
<p>… and you’ll see the same log spew around outputs in this version:</p>
<div class="section" id="conditional-outputs">
<h2>Conditional Outputs<a class="headerlink" href="#conditional-outputs" title="Permalink to this headline">¶</a></h2>
<p>Multiple outputs are the mechanism by which we implement branching or conditional execution.</p>
<p>Let’s modify the first solid above to conditionally emit one output or the other based on config
and then execute that pipeline.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">ConfigDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">,</span> <span class="n">description</span><span class="o">=</span><span class="s1">&#39;Should be either out_one or out_two&#39;</span><span class="p">),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span>
        <span class="n">OutputDefinition</span><span class="p">(</span><span class="n">runtime_type</span><span class="o">=</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">,</span> <span class="n">name</span><span class="o">=</span><span class="s1">&#39;out_one&#39;</span><span class="p">),</span>
        <span class="n">OutputDefinition</span><span class="p">(</span><span class="n">runtime_type</span><span class="o">=</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">,</span> <span class="n">name</span><span class="o">=</span><span class="s1">&#39;out_two&#39;</span><span class="p">),</span>
    <span class="p">],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">conditional</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">if</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span> <span class="o">==</span> <span class="s1">&#39;out_one&#39;</span><span class="p">:</span>
        <span class="k">yield</span> <span class="n">Result</span><span class="p">(</span><span class="mi">23</span><span class="p">,</span> <span class="s1">&#39;out_one&#39;</span><span class="p">)</span>
    <span class="k">elif</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span> <span class="o">==</span> <span class="s1">&#39;out_two&#39;</span><span class="p">:</span>
        <span class="k">yield</span> <span class="n">Result</span><span class="p">(</span><span class="mi">45</span><span class="p">,</span> <span class="s1">&#39;out_two&#39;</span><span class="p">)</span>
    <span class="k">else</span><span class="p">:</span>
        <span class="k">raise</span> <span class="ne">Exception</span><span class="p">(</span><span class="s1">&#39;invalid config&#39;</span><span class="p">)</span>


<span class="k">def</span> <span class="nf">define_part_eleven_step_three</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;part_eleven_step_three&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">conditional</span><span class="p">,</span> <span class="n">log_num</span><span class="p">,</span> <span class="n">log_num_squared</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;log_num&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;num&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;conditional&#39;</span><span class="p">,</span> <span class="s1">&#39;out_one&#39;</span><span class="p">)</span>
            <span class="p">},</span>
            <span class="s1">&#39;log_num_squared&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;num&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;conditional&#39;</span><span class="p">,</span> <span class="s1">&#39;out_two&#39;</span><span class="p">)</span>
            <span class="p">},</span>
        <span class="p">},</span>
    <span class="p">)</span>

<span class="k">if</span> <span class="vm">__name__</span> <span class="o">==</span> <span class="s1">&#39;__main__&#39;</span><span class="p">:</span>
    <span class="n">execute_pipeline</span><span class="p">(</span>
        <span class="n">define_part_eleven_step_three</span><span class="p">(),</span>
        <span class="p">{</span>
            <span class="s1">&#39;solids&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;conditional&#39;</span><span class="p">:</span> <span class="p">{</span>
                    <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="s1">&#39;out_two&#39;</span>
                <span class="p">},</span>
            <span class="p">},</span>
        <span class="p">},</span>
    <span class="p">)</span>
</pre></div>
</div>
<p>Note that we are configuring this solid to <em>only</em> emit out_two which will end up
only triggering log_num_squared. log_num will never be executed.</p>
<div class="highlight-sh notranslate"><div class="highlight"><pre><span></span>$ python part_eleven.py
... log spew
<span class="m">2018</span>-09-16 <span class="m">18</span>:58:32 - dagster - INFO - <span class="nv">orig_message</span><span class="o">=</span><span class="s2">&quot;Solid conditional emitted output \\&quot;out_two\\&quot; value 45&quot;</span> <span class="nv">log_message_id</span><span class="o">=</span><span class="s2">&quot;f6fd78c5-c25e-40ea-95ef-6b80d12155de&quot;</span> <span class="nv">pipeline</span><span class="o">=</span><span class="s2">&quot;part_eleven_step_three&quot;</span> <span class="nv">solid</span><span class="o">=</span><span class="s2">&quot;conditional&quot;</span>
<span class="m">2018</span>-09-16 <span class="m">18</span>:58:32 - dagster - INFO - <span class="nv">orig_message</span><span class="o">=</span><span class="s2">&quot;Solid conditional did not fire outputs {&#39;out_one&#39;}&quot;</span> <span class="nv">log_message_id</span><span class="o">=</span><span class="s2">&quot;d548ea66-cb10-42b8-b150-aed8162cc25c&quot;</span> <span class="nv">pipeline</span><span class="o">=</span><span class="s2">&quot;part_eleven_step_three&quot;</span> <span class="nv">solid</span><span class="o">=</span><span class="s2">&quot;conditional&quot;</span>
... log spew
</pre></div>
</div>
</div>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_ten.html">Expectations</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="part_ten.html" title="previous chapter">Expectations</a></li>
      <li>Next: <a href="part_twelve.html" title="next chapter">User-defined Types</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/part_eleven.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/part_eleven.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 18'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Inputs &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="Configuration" href="config.html" />
    <link rel="prev" title="An actual DAG" href="actual_dag.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="inputs">
<h1>Inputs<a class="headerlink" href="#inputs" title="Permalink to this headline">¶</a></h1>
<p>So far we have only demonstrated pipelines whose solids yield hardcoded values and then flow them
through the pipeline. In order to be useful a pipeline must also interact with its external
environment.</p>
<p>Let’s return to our hello world example. But this time, we’ll make the string
the solid returns be parameterized based on inputs.</p>
<div class="literal-block-wrapper docutils container" id="id1">
<div class="code-block-caption"><span class="caption-text">inputs.py</span><a class="headerlink" href="#id1" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre> 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="kn">from</span> <span class="nn">dagster</span> <span class="k">import</span> <span class="p">(</span>
    <span class="n">InputDefinition</span><span class="p">,</span>
    <span class="n">OutputDefinition</span><span class="p">,</span>
    <span class="n">PipelineDefinition</span><span class="p">,</span>
    <span class="n">execute_pipeline</span><span class="p">,</span>
    <span class="n">lambda_solid</span><span class="p">,</span>
    <span class="n">types</span><span class="p">,</span>
<span class="p">)</span>


<span class="nd">@lambda_solid</span><span class="p">(</span><span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;word&#39;</span><span class="p">)])</span>
<span class="k">def</span> <span class="nf">add_hello_to_word</span><span class="p">(</span><span class="n">word</span><span class="p">):</span>
    <span class="k">return</span> <span class="s1">&#39;Hello, &#39;</span> <span class="o">+</span> <span class="n">word</span> <span class="o">+</span> <span class="s1">&#39;!&#39;</span>


<span class="k">def</span> <span class="nf">define_hello_inputs_pipeline</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span><span class="n">name</span><span class="o">=</span><span class="s1">&#39;hello_inputs&#39;</span><span class="p">,</span> <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">add_hello_to_word</span><span class="p">])</span>


<span class="k">def</span> <span class="nf">execute_with_another_world</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">execute_pipeline</span><span class="p">(</span>
        <span class="n">define_hello_inputs_pipeline</span><span class="p">(),</span>
        <span class="c1"># This entire dictionary is known as the &#39;environment&#39;.</span>
        <span class="c1"># It has many sections.</span>
        <span class="p">{</span>
            <span class="c1"># This is the &#39;solids&#39; section</span>
            <span class="s1">&#39;solids&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="c1"># Configuration for the add_hello_to_word solid</span>
                <span class="s1">&#39;add_hello_to_word&#39;</span><span class="p">:</span> <span class="p">{</span><span class="s1">&#39;inputs&#39;</span><span class="p">:</span> <span class="p">{</span><span class="s1">&#39;word&#39;</span><span class="p">:</span> <span class="s1">&#39;Mars&#39;</span><span class="p">}}</span>
            <span class="p">}</span>
        <span class="p">},</span>
    <span class="p">)</span>


<span class="nd">@lambda_solid</span><span class="p">(</span>
    <span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;word&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">)],</span>
    <span class="n">output</span><span class="o">=</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">),</span>
<span class="p">)</span>
</pre></div>
</td></tr></table></div>
</div>
<p>Note that the input <code class="docutils literal notranslate"><span class="pre">word</span></code> to solid <code class="docutils literal notranslate"><span class="pre">add_hello_to_word</span></code> has no dependency specified. This
means that the operator of the pipeline must specify the input at pipeline execution
time.</p>
<p>Recall that there are three primary ways to execute a pipeline: using the python API, from
the command line, and from dagit. We’ll go through each of these and see how to specify the input
in each case.</p>
<div class="section" id="python-api">
<h2>Python API<a class="headerlink" href="#python-api" title="Permalink to this headline">¶</a></h2>
<p>In the Python API, pipeline configuration is specified in the second argument to
<a class="reference internal" href="../apidocs/execution.html#dagster.execute_pipeline" title="dagster.execute_pipeline"><code class="xref py py-func docutils literal notranslate"><span class="pre">execute_pipeline</span></code></a>, which must be a dict. This dict contains
<em>all</em> of the configuration to execute an entire pipeline. It may have many sections, but we’ll only
use one of them here: per-solid configuration specified under the key <code class="docutils literal notranslate"><span class="pre">solids</span></code>:</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="p">{</span>
    <span class="s1">&#39;solids&#39;</span><span class="p">:</span> <span class="p">{</span>
        <span class="s1">&#39;add_hello_to_word&#39;</span><span class="p">:</span> <span class="p">{</span><span class="s1">&#39;inputs&#39;</span><span class="p">:</span> <span class="p">{</span><span class="s1">&#39;word&#39;</span><span class="p">:</span> <span class="s1">&#39;Mars&#39;</span><span class="p">}}</span>
    <span class="p">}</span>
<span class="p">},</span>
</pre></div>
</div>
<p>The <code class="docutils literal notranslate"><span class="pre">solids</span></code> dict is keyed by solid name, and each solid is configured by a dict that may have
several sections of its own. In this case we are only interested in the <code class="docutils literal notranslate"><span class="pre">inputs</span></code> section, so
that we can specify that value of the input <code class="docutils literal notranslate"><span class="pre">word</span></code>.</p>
<p>The function <code class="docutils literal notranslate"><span class="pre">execute_with_another_world</span></code> demonstrates how one would invoke this pipeline
using the python API:</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="k">def</span> <span class="nf">execute_with_another_world</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">execute_pipeline</span><span class="p">(</span>
        <span class="n">define_hello_inputs_pipeline</span><span class="p">(),</span>
        <span class="p">{</span>
            <span class="s1">&#39;solids&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;add_hello_to_word&#39;</span><span class="p">:</span> <span class="p">{</span><span class="s1">&#39;inputs&#39;</span><span class="p">:</span> <span class="p">{</span><span class="s1">&#39;word&#39;</span><span class="p">:</span> <span class="s1">&#39;Mars&#39;</span><span class="p">}}</span>
            <span class="p">}</span>
        <span class="p">},</span>
    <span class="p">)</span>
</pre></div>
</div>
</div>
<div class="section" id="cli">
<h2>CLI<a class="headerlink" href="#cli" title="Permalink to this headline">¶</a></h2>
<p>Next let’s use the CLI. In order to do that we’ll need to provide the environment
information via a config file. We’ll use the same values as before, but in the form
of YAML rather than python dictionaries:</p>
<div class="literal-block-wrapper docutils container" id="id2">
<div class="code-block-caption"><span class="caption-text">inputs_env.yml</span><a class="headerlink" href="#id2" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre>1
2
3
4</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="n">solids</span><span class="p">:</span>
  <span class="n">add_hello_to_word</span><span class="p">:</span>
    <span class="n">inputs</span><span class="p">:</span>
      <span class="n">word</span><span class="p">:</span> <span class="s2">&quot;Mars&quot;</span>
</pre></div>
</td></tr></table></div>
</div>
<p>And now specify that config file via the <code class="docutils literal notranslate"><span class="pre">-e</span></code> flag.</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagster pipeline execute -f inputs.py <span class="se">\\</span>
-n define_hello_inputs_pipeline -e inputs_env.yml
</pre></div>
</div>
</div>
<div class="section" id="dagit">
<h2>Dagit<a class="headerlink" href="#dagit" title="Permalink to this headline">¶</a></h2>
<p>As always, you can load the pipeline and execute it within dagit.</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagit -f inputs.py -n define_hello_inputs_pipeline
<span class="go">Serving on http://127.0.0.1:3000</span>
</pre></div>
</div>
<p>From the execute console, you can enter your config directly like so:</p>
<img alt="../_images/inputs_figure_one.png" src="../_images/inputs_figure_one.png" />
<p>You’ll notice that the config editor is auto-completing. Because it knows the structure
of the config, the editor can provide rich error information. We can improve the experience of
using the editor by appropriately typing the inputs, making everything less error-prone.</p>
<div class="section" id="typing">
<h3>Typing<a class="headerlink" href="#typing" title="Permalink to this headline">¶</a></h3>
<p>Right now the inputs and outputs of this solid are totally untyped. (Any input or output
without a type is automatically assigned the <code class="docutils literal notranslate"><span class="pre">Any</span></code> type.) This means that mistakes
are often not surfaced until the pipeline is executed.</p>
<p>For example, imagine if our environment for our pipeline was:</p>
<div class="highlight-YAML notranslate"><div class="highlight"><pre><span></span><span class="nt">solids</span><span class="p">:</span>
    <span class="nt">add_hello_to_word</span><span class="p">:</span>
        <span class="nt">inputs</span><span class="p">:</span>
            <span class="nt">word</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">2343</span>
</pre></div>
</div>
<p>If we execute this pipeline with this config, it’ll fail at runtime.</p>
<p>Enter this config in dagit and execute and you’ll see the transform fail:</p>
<img alt="../_images/inputs_figure_two_untyped_execution.png" src="../_images/inputs_figure_two_untyped_execution.png" />
<p>Click on the red dot on the execution step that failed and a detailed stacktrace will pop up.</p>
<img alt="../_images/inputs_figure_three_error_modal.png" src="../_images/inputs_figure_three_error_modal.png" />
<p>It would be better if we could catch this error earlier, when we specify the config. So let’s
make the inputs typed.</p>
<p>A user can apply types to inputs and outputs. In this case we just want to type them as the
built-in <code class="docutils literal notranslate"><span class="pre">String</span></code>.</p>
<div class="literal-block-wrapper docutils container" id="id3">
<div class="code-block-caption"><span class="caption-text">inputs.py</span><a class="headerlink" href="#id3" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="nd">@lambda_solid</span><span class="p">(</span>
    <span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;word&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">)],</span>
    <span class="n">output</span><span class="o">=</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">),</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">add_hello_to_word_typed</span><span class="p">(</span><span class="n">word</span><span class="p">):</span>
    <span class="k">return</span> <span class="s1">&#39;Hello, &#39;</span> <span class="o">+</span> <span class="n">word</span> <span class="o">+</span> <span class="s1">&#39;!&#39;</span>
</pre></div>
</div>
</div>
<p>By using typed input instead we can catch this error prior to execution.</p>
<img alt="../_images/inputs_figure_four_error_prechecked.png" src="../_images/inputs_figure_four_error_prechecked.png" />
<p>We’ve seen how to connect solid inputs and outputs to specify dependencies and the structure of
our DAG, as well as how to provide inputs at runtime through config. Next, we’ll see how we can
use <a class="reference internal" href="config.html"><span class="doc">Configuration</span></a> to further parametrize our solids’ interactions with the
outside world.</p>
</div>
</div>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="actual_dag.html" title="previous chapter">An actual DAG</a></li>
      <li>Next: <a href="config.html" title="next chapter">Configuration</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/inputs.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/inputs.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 19'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>User-defined Types &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="Reusable Solids" href="part_thirteen.html" />
    <link rel="prev" title="Multiple Outputs" href="part_eleven.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="user-defined-types">
<h1>User-defined Types<a class="headerlink" href="#user-defined-types" title="Permalink to this headline">¶</a></h1>
<p>So far we have only used the built-in types the come with dagster to describe
data flowing between different solids. However this only gets one so far, and
is typically only useful for toy pipelines. You are going to want to define
our own custom types to describe your pipeline- and runtime-specific data
structures.</p>
<p>For the first example, we’ll show how to flow a plain python object
through the a pipeline and then describe that object in the type system.
Let’s say we wanted to flow a tuple through a pipeline.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="n">StringTuple</span> <span class="o">=</span> <span class="n">namedtuple</span><span class="p">(</span><span class="s1">&#39;StringTuple&#39;</span><span class="p">,</span> <span class="s1">&#39;str_one str_two&#39;</span><span class="p">)</span>

<span class="nd">@lambda_solid</span>
<span class="k">def</span> <span class="nf">produce_valid_value</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">StringTuple</span><span class="p">(</span><span class="n">str_one</span><span class="o">=</span><span class="s1">&#39;value_one&#39;</span><span class="p">,</span> <span class="n">str_two</span><span class="o">=</span><span class="s1">&#39;value_two&#39;</span><span class="p">)</span>
</pre></div>
</div>
<p>And then we want to consume it. However, we want this to be type-checked
and metadata to be surfaced in tools like dagit.</p>
<p>To do this we’ll introduce a dagster type.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="n">StringTupleType</span> <span class="o">=</span> <span class="n">types</span><span class="o">.</span><span class="n">PythonObjectType</span><span class="p">(</span>
    <span class="s1">&#39;StringTuple&#39;</span><span class="p">,</span>
    <span class="n">python_type</span><span class="o">=</span><span class="n">StringTuple</span><span class="p">,</span>
    <span class="n">description</span><span class="o">=</span><span class="s1">&#39;A tuple of strings.&#39;</span><span class="p">,</span>
<span class="p">)</span>
</pre></div>
</div>
<p>And then annotate relevant functions with it.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@lambda_solid</span><span class="p">(</span><span class="n">output</span><span class="o">=</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">StringTupleType</span><span class="p">))</span>
<span class="k">def</span> <span class="nf">produce_valid_value</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">StringTuple</span><span class="p">(</span><span class="n">str_one</span><span class="o">=</span><span class="s1">&#39;value_one&#39;</span><span class="p">,</span> <span class="n">str_two</span><span class="o">=</span><span class="s1">&#39;value_two&#39;</span><span class="p">)</span>

<span class="nd">@solid</span><span class="p">(</span><span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;string_tuple&#39;</span><span class="p">,</span> <span class="n">StringTupleType</span><span class="p">)])</span>
<span class="k">def</span> <span class="nf">consume_string_tuple</span><span class="p">(</span><span class="n">info</span><span class="p">,</span> <span class="n">string_tuple</span><span class="p">):</span>
    <span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="o">.</span><span class="n">info</span><span class="p">(</span>
        <span class="s1">&#39;Logging value {string_tuple}&#39;</span><span class="o">.</span><span class="n">format</span><span class="p">(</span>
            <span class="n">string_tuple</span><span class="o">=</span><span class="n">string_tuple</span>
        <span class="p">)</span>
    <span class="p">)</span>

<span class="k">def</span> <span class="nf">define_part_twelve_step_one</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;part_twelve_step_one&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">produce_valid_value</span><span class="p">,</span> <span class="n">consume_string_tuple</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;consume_string_tuple&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;string_tuple&#39;</span><span class="p">:</span>
                <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;produce_valid_value&#39;</span><span class="p">)</span>
            <span class="p">}</span>
        <span class="p">},</span>
    <span class="p">)</span>

<span class="k">if</span> <span class="vm">__name__</span> <span class="o">==</span> <span class="s1">&#39;__main__&#39;</span><span class="p">:</span>
    <span class="n">execute_pipeline</span><span class="p">(</span><span class="n">define_part_twelve_step_one</span><span class="p">())</span>
</pre></div>
</div>
<div class="highlight-sh notranslate"><div class="highlight"><pre><span></span>$ python part_twelve.py
... log spew
<span class="m">2018</span>-09-17 <span class="m">06</span>:55:06 - dagster - INFO - <span class="nv">orig_message</span><span class="o">=</span><span class="s2">&quot;Logging value StringTuple(str_one=&#39;value_one&#39;, str_two=&#39;value_two&#39;)&quot;</span> <span class="nv">log_message_id</span><span class="o">=</span><span class="s2">&quot;675f905d-c1f4-4539-af26-c28d23a757be&quot;</span> <span class="nv">pipeline</span><span class="o">=</span><span class="s2">&quot;part_twelve_step_one&quot;</span> <span class="nv">solid</span><span class="o">=</span><span class="s2">&quot;consume_string_tuple&quot;</span>
...
</pre></div>
</div>
<p>Now what if things go wrong? Imagine you made an error and wired up <cite>consume_string_tuple</cite>
to a solid</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@lambda_solid</span>
<span class="k">def</span> <span class="nf">produce_invalid_value</span><span class="p">():</span>
    <span class="k">return</span> <span class="s1">&#39;not_a_tuple&#39;</span>

<span class="k">def</span> <span class="nf">define_part_twelve_step_two</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;part_twelve_step_two&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">produce_invalid_value</span><span class="p">,</span> <span class="n">consume_string_tuple</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;consume_string_tuple&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;string_tuple&#39;</span><span class="p">:</span>
                <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;produce_invalid_value&#39;</span><span class="p">)</span>
            <span class="p">}</span>
        <span class="p">},</span>
    <span class="p">)</span>

<span class="k">if</span> <span class="vm">__name__</span> <span class="o">==</span> <span class="s1">&#39;__main__&#39;</span><span class="p">:</span>
    <span class="n">execute_pipeline</span><span class="p">(</span><span class="n">define_part_twelve_step_two</span><span class="p">())</span>
</pre></div>
</div>
<p>If you run this you’ll get some helpful error messages</p>
<div class="highlight-sh notranslate"><div class="highlight"><pre><span></span>$ python part_twelve.py
... log spew
<span class="m">2018</span>-11-08 <span class="m">11</span>:03:03 - dagster - ERROR - <span class="nv">orig_message</span><span class="o">=</span><span class="s2">&quot;Solid consume_string_tuple input string_tuple received value not_a_tuple which does not pass the typecheck for Dagster type StringTuple. Compute node consume_string_tuple.transform&quot;</span> <span class="nv">log_message_id</span><span class="o">=</span><span class="s2">&quot;0db53fdb-183c-477c-aff9-2ee26bc76636&quot;</span> <span class="nv">run_id</span><span class="o">=</span><span class="s2">&quot;424047dd-e835-4016-b757-18adec0afdfc&quot;</span> <span class="nv">pipeline</span><span class="o">=</span><span class="s2">&quot;part_twelve_step_two&quot;</span>    ... stack trace
dagster.core.errors.DagsterEvaluateValueError: Expected valid value <span class="k">for</span> StringTuple but got <span class="s1">&#39;not_a_tuple&#39;</span>
... more stack trace
dagster.core.errors.DagsterTypeError: Solid consume_string_tuple input string_tuple received value not_a_tuple which does not pass the typecheck <span class="k">for</span> Dagster <span class="nb">type</span> StringTuple. Compute node consume_string_tuple.transform
</pre></div>
</div>
<div class="section" id="custom-types">
<h2>Custom Types<a class="headerlink" href="#custom-types" title="Permalink to this headline">¶</a></h2>
<p>The type system is very flexible, and values can by both type-checked and coerced by user-defined code.</p>
<p>Imagine we wants to be able process social security numbers and ensure that they are well-formed
throughout the whole pipeline.</p>
<p>In order to do this we’ll define a type.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="k">class</span> <span class="nc">SSNString</span><span class="p">(</span><span class="nb">str</span><span class="p">):</span>
    <span class="k">pass</span>

<span class="k">class</span> <span class="nc">SSNStringTypeClass</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">DagsterType</span><span class="p">):</span>
    <span class="k">def</span> <span class="fm">__init__</span><span class="p">(</span><span class="bp">self</span><span class="p">):</span>
        <span class="nb">super</span><span class="p">(</span><span class="n">SSNStringTypeClass</span><span class="p">,</span> <span class="bp">self</span><span class="p">)</span><span class="o">.</span><span class="fm">__init__</span><span class="p">(</span><span class="n">name</span><span class="o">=</span><span class="s1">&#39;SSNString&#39;</span><span class="p">)</span>

    <span class="k">def</span> <span class="nf">coerce_runtime_value</span><span class="p">(</span><span class="bp">self</span><span class="p">,</span> <span class="n">value</span><span class="p">):</span>
        <span class="k">if</span> <span class="nb">isinstance</span><span class="p">(</span><span class="n">value</span><span class="p">,</span> <span class="n">SSNString</span><span class="p">):</span>
            <span class="k">return</span> <span class="n">value</span>

        <span class="k">if</span> <span class="ow">not</span> <span class="nb">isinstance</span><span class="p">(</span><span class="n">value</span><span class="p">,</span> <span class="nb">str</span><span class="p">):</span>
            <span class="k">raise</span> <span class="n">DagsterEvaluateValueError</span><span class="p">(</span>
                <span class="s1">&#39;{value} is not a string. SSNStringType typecheck failed&#39;</span><span class="o">.</span><span class="n">format</span><span class="p">(</span><span class="n">value</span><span class="o">=</span><span class="nb">repr</span><span class="p">(</span><span class="n">value</span><span class="p">))</span>
            <span class="p">)</span>

        <span class="k">if</span> <span class="ow">not</span> <span class="n">re</span><span class="o">.</span><span class="n">match</span><span class="p">(</span><span class="sa">r</span><span class="s1">&#39;^(\\d\\d\\d)-(\\d\\d)-(\\d\\d\\d\\d)$&#39;</span><span class="p">,</span> <span class="n">value</span><span class="p">):</span>
            <span class="k">raise</span> <span class="n">DagsterEvaluateValueError</span><span class="p">(</span>
                <span class="s1">&#39;{value} did not match SSN regex&#39;</span><span class="o">.</span><span class="n">format</span><span class="p">(</span><span class="n">value</span><span class="o">=</span><span class="nb">repr</span><span class="p">(</span><span class="n">value</span><span class="p">))</span>
            <span class="p">)</span>

        <span class="k">return</span> <span class="n">SSNString</span><span class="p">(</span><span class="n">value</span><span class="p">)</span>


<span class="n">SSNStringType</span> <span class="o">=</span> <span class="n">SSNStringTypeClass</span><span class="p">()</span>
</pre></div>
</div>
<p>This type does a couple things. One is that ensures that any string that gets passed to
evaluate_value matches a strict regular expression. You’ll also notice that it coerces
that incoming string type to a type called <cite>SSNString</cite>. This type just trivially inherits
from <code class="docutils literal notranslate"><span class="pre">str</span></code>, but it signifies that the typecheck has already occured. That means if
evaluate_value is called again, the bulk of the typecheck can be short-circuited, saving
repeated processing through the pipeline. (Note: this is slightly silly because the amount
of computation here is trivial, but one can imagine types that require significant
amounts of computation to verify).</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@lambda_solid</span>
<span class="k">def</span> <span class="nf">produce_valid_ssn_string</span><span class="p">():</span>
    <span class="k">return</span> <span class="s1">&#39;394-30-2032&#39;</span>

<span class="nd">@solid</span><span class="p">(</span><span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;ssn&#39;</span><span class="p">,</span> <span class="n">SSNStringType</span><span class="p">)])</span>
<span class="k">def</span> <span class="nf">consume_ssn</span><span class="p">(</span><span class="n">info</span><span class="p">,</span> <span class="n">ssn</span><span class="p">):</span>
    <span class="k">if</span> <span class="ow">not</span> <span class="nb">isinstance</span><span class="p">(</span><span class="n">ssn</span><span class="p">,</span> <span class="n">SSNString</span><span class="p">):</span>
        <span class="k">raise</span> <span class="ne">Exception</span><span class="p">(</span><span class="s1">&#39;This should never be thrown&#39;</span><span class="p">)</span>
    <span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="o">.</span><span class="n">info</span><span class="p">(</span><span class="s1">&#39;ssn: {ssn}&#39;</span><span class="o">.</span><span class="n">format</span><span class="p">(</span><span class="n">ssn</span><span class="o">=</span><span class="n">ssn</span><span class="p">))</span>

<span class="k">def</span> <span class="nf">define_part_twelve_step_three</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;part_twelve_step_three&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">produce_valid_ssn_string</span><span class="p">,</span> <span class="n">consume_ssn</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;consume_ssn&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;ssn&#39;</span><span class="p">:</span>
                <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;produce_valid_ssn_string&#39;</span><span class="p">)</span>
            <span class="p">}</span>
        <span class="p">},</span>
    <span class="p">)</span>

<span class="k">if</span> <span class="vm">__name__</span> <span class="o">==</span> <span class="s1">&#39;__main__&#39;</span><span class="p">:</span>
    <span class="n">execute_pipeline</span><span class="p">(</span><span class="n">define_part_twelve_step_three</span><span class="p">())</span>
</pre></div>
</div>
<p>You’ll note that the exception in <code class="docutils literal notranslate"><span class="pre">consume_ssn</span></code> was not thrown, meaning that the
str was coerced to an SSNString by the dagster type.</p>
</div>
<div class="section" id="future-directions">
<h2>Future Directions<a class="headerlink" href="#future-directions" title="Permalink to this headline">¶</a></h2>
<ol class="arabic simple">
<li>Up-front type checking</li>
<li>Serializations</li>
<li>Hashing</li>
</ol>
</div>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="part_eleven.html" title="previous chapter">Multiple Outputs</a></li>
      <li>Next: <a href="part_thirteen.html" title="next chapter">Reusable Solids</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/part_twelve.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/part_twelve.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 20'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Configuration Schemas &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="Custom Contexts" href="part_nine.html" />
    <link rel="prev" title="Pipeline Execution" href="pipeline_execution.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="configuration-schemas">
<h1>Configuration Schemas<a class="headerlink" href="#configuration-schemas" title="Permalink to this headline">¶</a></h1>
<p>Dagster includes a system for strongly-typed, self-describing configurations schemas. These
descriptions are very helpful when learning how to operate a pipeline, make a rich configuration
editing experience possible, and help to catch configuration errors before pipeline execution.</p>
<p>Let’s see how the configuration schema can prevent errors and improve pipeline documentation.
We’ll replace the config field in our solid definition with a structured, strongly typed schema.</p>
<div class="literal-block-wrapper docutils container" id="id1">
<div class="code-block-caption"><span class="caption-text">configuration_schemas.py</span><a class="headerlink" href="#id1" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre> 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="kn">from</span> <span class="nn">collections</span> <span class="k">import</span> <span class="n">defaultdict</span>

<span class="kn">from</span> <span class="nn">dagster</span> <span class="k">import</span> <span class="p">(</span>
    <span class="n">DependencyDefinition</span><span class="p">,</span>
    <span class="n">InputDefinition</span><span class="p">,</span>
    <span class="n">lambda_solid</span><span class="p">,</span>
    <span class="n">OutputDefinition</span><span class="p">,</span>
    <span class="n">PipelineDefinition</span><span class="p">,</span>
    <span class="n">RepositoryDefinition</span><span class="p">,</span>
    <span class="n">solid</span><span class="p">,</span>
    <span class="n">types</span><span class="p">,</span>
<span class="p">)</span>


<span class="hll"><span class="nd">@solid</span><span class="p">(</span>
</span>    <span class="n">config_field</span><span class="o">=</span><span class="n">types</span><span class="o">.</span><span class="n">Field</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Dict</span><span class="p">({</span><span class="s1">&#39;word&#39;</span><span class="p">:</span> <span class="n">types</span><span class="o">.</span><span class="n">Field</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">)}))</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">double_the_word</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">[</span><span class="s1">&#39;word&#39;</span><span class="p">]</span> <span class="o">*</span> <span class="mi">2</span>


<span class="nd">@lambda_solid</span><span class="p">(</span><span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;word&#39;</span><span class="p">)])</span>
<span class="k">def</span> <span class="nf">count_letters</span><span class="p">(</span><span class="n">word</span><span class="p">):</span>
    <span class="n">counts</span> <span class="o">=</span> <span class="n">defaultdict</span><span class="p">(</span><span class="nb">int</span><span class="p">)</span>
    <span class="k">for</span> <span class="n">letter</span> <span class="ow">in</span> <span class="n">word</span><span class="p">:</span>
        <span class="n">counts</span><span class="p">[</span><span class="n">letter</span><span class="p">]</span> <span class="o">+=</span> <span class="mi">1</span>
    <span class="k">return</span> <span class="nb">dict</span><span class="p">(</span><span class="n">counts</span><span class="p">)</span>


<span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">types</span><span class="o">.</span><span class="n">Field</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Dict</span><span class="p">({</span><span class="s1">&#39;word&#39;</span><span class="p">:</span> <span class="n">types</span><span class="o">.</span><span class="n">Field</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">)})),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">typed_double_the_word</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">[</span><span class="s1">&#39;word&#39;</span><span class="p">]</span> <span class="o">*</span> <span class="mi">2</span>


<span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">types</span><span class="o">.</span><span class="n">Field</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Dict</span><span class="p">({</span><span class="s1">&#39;word&#39;</span><span class="p">:</span> <span class="n">types</span><span class="o">.</span><span class="n">Field</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">)})),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">typed_double_the_word_error</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">[</span><span class="s1">&#39;word&#39;</span><span class="p">]</span> <span class="o">*</span> <span class="mi">2</span>


<span class="k">def</span> <span class="nf">define_demo_configuration_schema_pipeline</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;demo_configuration_schema&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">double_the_word</span><span class="p">,</span> <span class="n">count_letters</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;count_letters&#39;</span><span class="p">:</span> <span class="p">{</span><span class="s1">&#39;word&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;double_the_word&#39;</span><span class="p">)}</span>
        <span class="p">},</span>
    <span class="p">)</span>


<span class="k">def</span> <span class="nf">define_demo_configuration_schema_pipeline</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;demo_configuration_schema&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">double_the_word</span><span class="p">,</span> <span class="n">count_letters</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;count_letters&#39;</span><span class="p">:</span> <span class="p">{</span><span class="s1">&#39;word&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;double_the_word&#39;</span><span class="p">)}</span>
        <span class="p">},</span>
    <span class="p">)</span>


<span class="k">def</span> <span class="nf">define_typed_demo_configuration_schema_pipeline</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;typed_demo_configuration_schema&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">typed_double_the_word</span><span class="p">,</span> <span class="n">count_letters</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;count_letters&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;word&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;typed_double_the_word&#39;</span><span class="p">)</span>
            <span class="p">}</span>
        <span class="p">},</span>
    <span class="p">)</span>


<span class="k">def</span> <span class="nf">define_typed_demo_configuration_schema_error_pipeline</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;typed_demo_configuration_schema_error&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">typed_double_the_word_error</span><span class="p">,</span> <span class="n">count_letters</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;count_letters&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;word&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;typed_double_the_word_error&#39;</span><span class="p">)</span>
            <span class="p">}</span>
        <span class="p">},</span>
    <span class="p">)</span>


<span class="k">def</span> <span class="nf">define_demo_configuration_schema_repo</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">RepositoryDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;demo_configuration_schema_repo&#39;</span><span class="p">,</span>
        <span class="n">pipeline_dict</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;demo_configuration_schema&#39;</span><span class="p">:</span> <span class="n">define_demo_configuration_schema_pipeline</span><span class="p">,</span>
            <span class="s1">&#39;typed_demo_configuration_schema&#39;</span><span class="p">:</span> <span class="n">define_typed_demo_configuration_schema_pipeline</span><span class="p">,</span>
            <span class="s1">&#39;typed_demo_configuration_schema_error&#39;</span><span class="p">:</span> <span class="n">define_typed_demo_configuration_schema_error_pipeline</span><span class="p">,</span>
        <span class="p">},</span>
    <span class="p">)</span>
</pre></div>
</td></tr></table></div>
</div>
<p>The previous env.yml file works as before:</p>
<div class="literal-block-wrapper docutils container" id="id2">
<div class="code-block-caption"><span class="caption-text">configuration_schemas.yml</span><a class="headerlink" href="#id2" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre>1
2
3
4
5
6
7
8
9</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="n">context</span><span class="p">:</span>
  <span class="n">default</span><span class="p">:</span>
    <span class="n">config</span><span class="p">:</span>
      <span class="n">log_level</span><span class="p">:</span> <span class="n">DEBUG</span>

<span class="n">solids</span><span class="p">:</span>
  <span class="n">double_the_word</span><span class="p">:</span>
    <span class="n">config</span><span class="p">:</span>
      <span class="n">word</span><span class="p">:</span> <span class="n">quux</span>
</pre></div>
</td></tr></table></div>
</div>
<p>Now let’s imagine we made a mistake and passed an <code class="docutils literal notranslate"><span class="pre">int</span></code> in our configuration:</p>
<div class="literal-block-wrapper docutils container" id="id3">
<div class="code-block-caption"><span class="caption-text">configuration_schemas_error_1.yml</span><a class="headerlink" href="#id3" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre>1
2
3
4
5
6
7
8
9</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="n">context</span><span class="p">:</span>
  <span class="n">default</span><span class="p">:</span>
    <span class="n">config</span><span class="p">:</span>
      <span class="n">log_level</span><span class="p">:</span> <span class="n">DEBUG</span>

<span class="n">solids</span><span class="p">:</span>
  <span class="n">double_the_word</span><span class="p">:</span>
    <span class="n">config</span><span class="p">:</span>
<span class="hll">      <span class="n">word</span><span class="p">:</span> <span class="mi">1</span>
</span></pre></div>
</td></tr></table></div>
</div>
<p>And then ran it:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagster pipeline execute -f configuration_schemas.py <span class="se">\\</span>
-n define_demo_configuration_schema_pipeline -e configuration_schemas_error_1.yml
<span class="go">...</span>
<span class="go">dagster.core.execution.PipelineConfigEvaluationError: Pipeline &quot;demo_configuration_schema&quot; config errors:</span>
<span class="go">    Error 1: Type failure at path &quot;root:solids:double_the_word:config:word&quot; on type &quot;String&quot;. Got &quot;1&quot;.</span>
</pre></div>
</div>
<p>Now, instead of a runtime failure which might arise deep inside a time-consuming or expensive
pipeline execution, and which might be tedious to trace back to its root cause, we get a clear,
actionable error message before the pipeline is ever executed.</p>
<p>Let’s see what happens if we pass config with the wrong structure:</p>
<div class="literal-block-wrapper docutils container" id="id4">
<div class="code-block-caption"><span class="caption-text">configuration_schemas_error_2.yml</span><a class="headerlink" href="#id4" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre>1
2
3
4
5
6
7
8
9</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="n">context</span><span class="p">:</span>
  <span class="n">default</span><span class="p">:</span>
    <span class="n">config</span><span class="p">:</span>
      <span class="n">log_level</span><span class="p">:</span> <span class="n">DEBUG</span>

<span class="n">solids</span><span class="p">:</span>
  <span class="n">double_the_word_with_typed_config</span><span class="p">:</span>
    <span class="n">config</span><span class="p">:</span>
<span class="hll">      <span class="n">wrong_word</span><span class="p">:</span> <span class="n">quux</span>
</span></pre></div>
</td></tr></table></div>
</div>
<p>And then run the pipeline:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagster pipeline execute -f configuration_schemas.py <span class="se">\\</span>
-n define_demo_configuration_schema_pipeline -e configuration_schemas_error_2.yml
<span class="go">...</span>
<span class="go">dagster.core.execution.PipelineConfigEvaluationError: Pipeline &quot;demo_configuration_schema&quot; config errors:</span>
<span class="go">    Error 1: Undefined field &quot;double_the_word_with_typed_config&quot; at path root:solids</span>
<span class="go">    Error 2: Missing required field &quot;double_the_word&quot; at path root:solids</span>
</pre></div>
</div>
<p>Besides configured values, the type system is also used to evaluate the runtime values that flow
between solids. Types are attached, optionally, both to inputs and to outputs. If a type
is not specified, it defaults to the <a class="reference internal" href="../apidocs/types.html#dagster.core.types.Any" title="dagster.core.types.Any"><code class="xref py py-class docutils literal notranslate"><span class="pre">Any</span></code></a> type.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">types</span><span class="o">.</span><span class="n">Field</span><span class="p">(</span>
        <span class="n">types</span><span class="o">.</span><span class="n">Dict</span><span class="p">({</span><span class="s1">&#39;word&#39;</span><span class="p">:</span> <span class="n">Field</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">)})</span>
    <span class="p">),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">typed_double_word</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">[</span><span class="s1">&#39;word&#39;</span><span class="p">]</span> <span class="o">*</span> <span class="mi">2</span>
</pre></div>
</div>
<p>You’ll see here that now the output is annotated with a type. This both ensures
that the runtime value conforms requirements specified by the type (in this case
an instanceof check on a string) and also provides metadata to view in tools such
as dagit. That the output is a string is now guaranteed by the system. If you
violate this, execution halts.</p>
<p>So imagine we made a coding error (mistyped the output) such as:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">types</span><span class="o">.</span><span class="n">Field</span><span class="p">(</span>
        <span class="n">types</span><span class="o">.</span><span class="n">Dict</span><span class="p">({</span><span class="s1">&#39;word&#39;</span><span class="p">:</span> <span class="n">Field</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">)})</span>
    <span class="p">),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">typed_double_word_mismatch</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">[</span><span class="s1">&#39;word&#39;</span><span class="p">]</span> <span class="o">*</span> <span class="mi">2</span>
</pre></div>
</div>
<p>When we run it, it errors:</p>
<div class="highlight-sh notranslate"><div class="highlight"><pre><span></span>$ dagster pipeline execute part_eight -e env.yml
dagster.core.errors.DagsterInvariantViolationError: Solid typed_double_word_mismatch output name result output quuxquux
            <span class="nb">type</span> failure: Expected valid value <span class="k">for</span> Int but got <span class="s1">&#39;quuxquux&#39;</span>
</pre></div>
</div>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="pipeline_execution.html" title="previous chapter">Pipeline Execution</a></li>
      <li>Next: <a href="part_nine.html" title="next chapter">Custom Contexts</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/configuration_schemas.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/configuration_schemas.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 21'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Reusable Solids &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="Unit-testing Pipelines" href="part_fourteen.html" />
    <link rel="prev" title="User-defined Types" href="part_twelve.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="reusable-solids">
<h1>Reusable Solids<a class="headerlink" href="#reusable-solids" title="Permalink to this headline">¶</a></h1>
<p>So far we have been using solids tailor-made for each pipeline they were resident in, and have
only used a single instance of that solid. However, solids are, at their core, a specialized type
of function. And like functions, they should be reusable and not tied to a particular call site.</p>
<p>Now imagine we a pipeline like the following:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@solid</span><span class="p">(</span><span class="n">config_field</span><span class="o">=</span><span class="n">ConfigDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span> <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)])</span>
<span class="k">def</span> <span class="nf">load_a</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span>


<span class="nd">@solid</span><span class="p">(</span><span class="n">config_field</span><span class="o">=</span><span class="n">ConfigDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span> <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)])</span>
<span class="k">def</span> <span class="nf">load_b</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span>


<span class="nd">@lambda_solid</span><span class="p">(</span>
    <span class="n">inputs</span><span class="o">=</span><span class="p">[</span>
        <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;a&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
        <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;b&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="p">],</span>
    <span class="n">output</span><span class="o">=</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">a_plus_b</span><span class="p">(</span><span class="n">a</span><span class="p">,</span> <span class="n">b</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">a</span> <span class="o">+</span> <span class="n">b</span>


<span class="k">def</span> <span class="nf">define_part_thirteen_step_one</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;thirteen_step_one&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">load_a</span><span class="p">,</span> <span class="n">load_b</span><span class="p">,</span> <span class="n">a_plus_b</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;a_plus_b&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;a&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;load_a&#39;</span><span class="p">),</span>
                <span class="s1">&#39;b&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;load_b&#39;</span><span class="p">),</span>
            <span class="p">}</span>
        <span class="p">}</span>
    <span class="p">)</span>


<span class="k">def</span> <span class="nf">test_part_thirteen_step_one</span><span class="p">():</span>
    <span class="n">pipeline_result</span> <span class="o">=</span> <span class="n">execute_pipeline</span><span class="p">(</span>
        <span class="n">define_part_thirteen_step_one</span><span class="p">(),</span>
        <span class="p">{</span>
            <span class="s1">&#39;solids&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;load_a&#39;</span><span class="p">:</span> <span class="p">{</span>
                    <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="mi">234</span><span class="p">,</span>
                <span class="p">},</span>
                <span class="s1">&#39;load_b&#39;</span><span class="p">:</span> <span class="p">{</span>
                    <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="mi">384</span>
                <span class="p">},</span>
            <span class="p">},</span>
        <span class="p">},</span>
    <span class="p">)</span>

    <span class="k">assert</span> <span class="n">pipeline_result</span><span class="o">.</span><span class="n">success</span>
    <span class="n">solid_result</span> <span class="o">=</span> <span class="n">pipeline_result</span><span class="o">.</span><span class="n">result_for_solid</span><span class="p">(</span><span class="s1">&#39;a_plus_b&#39;</span><span class="p">)</span>
    <span class="k">assert</span> <span class="n">solid_result</span><span class="o">.</span><span class="n">transformed_value</span><span class="p">()</span> <span class="o">==</span> <span class="mi">234</span> <span class="o">+</span> <span class="mi">384</span>
</pre></div>
</div>
<p>You’ll notice that the solids in this pipeline are very generic. There’s no reason why we shouldn’t be able
to reuse them. Indeed load_a and load_b only different by name. What we can do is include multiple
instances of a particular solid in the dependency graph, and alias them. We can make the three specialized
solids in this pipeline two generic solids, and then hook up three instances of them in a dependency
graph:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">ConfigDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">load_number</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span>


<span class="nd">@lambda_solid</span><span class="p">(</span>
    <span class="n">inputs</span><span class="o">=</span><span class="p">[</span>
        <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num1&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
        <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num2&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="p">],</span>
    <span class="n">output</span><span class="o">=</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">adder</span><span class="p">(</span><span class="n">num1</span><span class="p">,</span> <span class="n">num2</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">num1</span> <span class="o">+</span> <span class="n">num2</span>


<span class="k">def</span> <span class="nf">define_part_thirteen_step_two</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;thirteen_step_two&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">load_number</span><span class="p">,</span> <span class="n">adder</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="s1">&#39;load_number&#39;</span><span class="p">,</span> <span class="n">alias</span><span class="o">=</span><span class="s1">&#39;load_a&#39;</span><span class="p">):</span> <span class="p">{},</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="s1">&#39;load_number&#39;</span><span class="p">,</span> <span class="n">alias</span><span class="o">=</span><span class="s1">&#39;load_b&#39;</span><span class="p">):</span> <span class="p">{},</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="s1">&#39;adder&#39;</span><span class="p">,</span> <span class="n">alias</span><span class="o">=</span><span class="s1">&#39;a_plus_b&#39;</span><span class="p">):</span> <span class="p">{</span>
                <span class="s1">&#39;num1&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;load_a&#39;</span><span class="p">),</span>
                <span class="s1">&#39;num2&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;load_b&#39;</span><span class="p">),</span>
            <span class="p">}</span>
        <span class="p">}</span>
    <span class="p">)</span>


<span class="k">def</span> <span class="nf">test_part_thirteen_step_two</span><span class="p">():</span>
    <span class="n">pipeline_result</span> <span class="o">=</span> <span class="n">execute_pipeline</span><span class="p">(</span>
        <span class="n">define_part_thirteen_step_two</span><span class="p">(),</span>
        <span class="p">{</span>
            <span class="s1">&#39;solids&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;load_a&#39;</span><span class="p">:</span> <span class="p">{</span>
                    <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="mi">23</span><span class="p">,</span>
                <span class="p">},</span>
                <span class="s1">&#39;load_b&#39;</span><span class="p">:</span> <span class="p">{</span>
                    <span class="s1">&#39;config&#39;</span><span class="p">:</span> <span class="mi">38</span>
                <span class="p">},</span>
            <span class="p">},</span>
        <span class="p">},</span>
    <span class="p">)</span>

    <span class="k">assert</span> <span class="n">pipeline_result</span><span class="o">.</span><span class="n">success</span>
    <span class="n">solid_result</span> <span class="o">=</span> <span class="n">pipeline_result</span><span class="o">.</span><span class="n">result_for_solid</span><span class="p">(</span><span class="s1">&#39;a_plus_b&#39;</span><span class="p">)</span>
    <span class="k">assert</span> <span class="n">solid_result</span><span class="o">.</span><span class="n">transformed_value</span><span class="p">()</span> <span class="o">==</span> <span class="mi">23</span> <span class="o">+</span> <span class="mi">38</span>
</pre></div>
</div>
<p>You can think of the solids parameter as declaring what solids are “in-scope” for the
purposes of this pipeline, and the dependencies parameter is how they instantiated
and connected together. Within the dependency graph and in config, the alias of the
particular instance is used, rather than the name of the definition.</p>
<p>Load this in dagit and you’ll see that the node are the graph are labeled with
their instance name.</p>
<div class="highlight-sh notranslate"><div class="highlight"><pre><span></span>$ dagit -f part_thirteen.py -n define_part_thirteen_step_two
</pre></div>
</div>
<p>These can obviously get more complicated and involved, with solids being reused
many times:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@lambda_solid</span><span class="p">(</span>
    <span class="n">inputs</span><span class="o">=</span><span class="p">[</span>
        <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num1&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
        <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num2&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="p">],</span>
    <span class="n">output</span><span class="o">=</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">multer</span><span class="p">(</span><span class="n">num1</span><span class="p">,</span> <span class="n">num2</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">num1</span> <span class="o">*</span> <span class="n">num2</span>

<span class="k">def</span> <span class="nf">define_part_thirteen_step_three</span><span class="p">():</span>
    <span class="c1"># (a + b) * (c + d)</span>

    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;tutorial_part_thirteen_step_three&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">load_number</span><span class="p">,</span> <span class="n">adder</span><span class="p">,</span> <span class="n">multer</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="n">load_number</span><span class="o">.</span><span class="n">name</span><span class="p">,</span> <span class="s1">&#39;a&#39;</span><span class="p">):</span> <span class="p">{},</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="n">load_number</span><span class="o">.</span><span class="n">name</span><span class="p">,</span> <span class="s1">&#39;b&#39;</span><span class="p">):</span> <span class="p">{},</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="n">load_number</span><span class="o">.</span><span class="n">name</span><span class="p">,</span> <span class="s1">&#39;c&#39;</span><span class="p">):</span> <span class="p">{},</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="n">load_number</span><span class="o">.</span><span class="n">name</span><span class="p">,</span> <span class="s1">&#39;d&#39;</span><span class="p">):</span> <span class="p">{},</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="n">adder</span><span class="o">.</span><span class="n">name</span><span class="p">,</span> <span class="s1">&#39;a_plus_b&#39;</span><span class="p">):</span> <span class="p">{</span>
                <span class="s1">&#39;num1&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;a&#39;</span><span class="p">),</span>
                <span class="s1">&#39;num2&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;b&#39;</span><span class="p">),</span>
            <span class="p">},</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="n">adder</span><span class="o">.</span><span class="n">name</span><span class="p">,</span> <span class="s1">&#39;c_plus_d&#39;</span><span class="p">):</span> <span class="p">{</span>
                <span class="s1">&#39;num1&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;c&#39;</span><span class="p">),</span>
                <span class="s1">&#39;num2&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;d&#39;</span><span class="p">),</span>
            <span class="p">},</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="n">multer</span><span class="o">.</span><span class="n">name</span><span class="p">,</span> <span class="s1">&#39;final&#39;</span><span class="p">):</span> <span class="p">{</span>
                <span class="s1">&#39;num1&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;a_plus_b&#39;</span><span class="p">),</span>
                <span class="s1">&#39;num2&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;c_plus_d&#39;</span><span class="p">),</span>
            <span class="p">},</span>
        <span class="p">},</span>
    <span class="p">)</span>
</pre></div>
</div>
<p>Now these arithmetic operations are not particularly interesting, but one
can imagine reusable solids doing more useful things like uploading files
to cloud storage, unzipping files, etc.</p>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="part_twelve.html" title="previous chapter">User-defined Types</a></li>
      <li>Next: <a href="part_fourteen.html" title="next chapter">Unit-testing Pipelines</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/part_thirteen.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/part_thirteen.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 22'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Configuration &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="Execution Context" href="execution_context.html" />
    <link rel="prev" title="Inputs" href="inputs.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="configuration">
<h1>Configuration<a class="headerlink" href="#configuration" title="Permalink to this headline">¶</a></h1>
<p>For maximum flexibility, testability, and reusability, we want to avoid hardcoding solids’
(or pipelines’) dependencies on the external world.</p>
<p>We should be able to run the same code in different environments for test, in development, and in
production, and to parametrize our solids’ interactions with the different facilities afforded by
each of those environments.</p>
<p>Then, we can declaratively specify features of our environment without having to rewrite our code.</p>
<p>Conceptually, where <strong>inputs</strong> are inputs to the computation done by a single solid, and might be
linked by a dependency definition to <strong>outputs</strong> of a previous computation in a DAG,
<strong>configuration</strong> should be used to specify <em>how</em> a computation executes.</p>
<p>We’ll illustrate this by configuring our hello world example to speak a couple of different
languages.</p>
<p>This time, we’ll use a more fully-featured API to define our solid –
<a class="reference internal" href="../apidocs/decorators.html#dagster.solid" title="dagster.solid"><code class="xref py py-func docutils literal notranslate"><span class="pre">&#64;solid</span></code></a> instead of <a class="reference internal" href="../apidocs/decorators.html#dagster.lambda_solid" title="dagster.lambda_solid"><code class="xref py py-func docutils literal notranslate"><span class="pre">&#64;lambda_solid</span></code></a>.</p>
<div class="literal-block-wrapper docutils container" id="id1">
<div class="code-block-caption"><span class="caption-text">config.py</span><a class="headerlink" href="#id1" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre> 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="kn">from</span> <span class="nn">dagster</span> <span class="k">import</span> <span class="n">Field</span><span class="p">,</span> <span class="n">PipelineDefinition</span><span class="p">,</span> <span class="n">execute_pipeline</span><span class="p">,</span> <span class="n">solid</span><span class="p">,</span> <span class="n">types</span>


<span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">Field</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">,</span> <span class="n">is_optional</span><span class="o">=</span><span class="kc">True</span><span class="p">,</span> <span class="n">default_value</span><span class="o">=</span><span class="s2">&quot;en-us&quot;</span><span class="p">)</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">configurable_hello</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">if</span> <span class="nb">len</span><span class="p">(</span><span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">)</span> <span class="o">&gt;=</span> <span class="mi">3</span> <span class="ow">and</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">[:</span><span class="mi">3</span><span class="p">]</span> <span class="o">==</span> <span class="s2">&quot;haw&quot;</span><span class="p">:</span>
        <span class="k">return</span> <span class="s2">&quot;Aloha honua!&quot;</span>
    <span class="k">elif</span> <span class="nb">len</span><span class="p">(</span><span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">)</span> <span class="o">&gt;=</span> <span class="mi">2</span> <span class="ow">and</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">[:</span><span class="mi">2</span><span class="p">]</span> <span class="o">==</span> <span class="s2">&quot;cn&quot;</span><span class="p">:</span>
        <span class="k">return</span> <span class="s2">&quot;你好, 世界!&quot;</span>
    <span class="k">else</span><span class="p">:</span>
        <span class="k">return</span> <span class="s2">&quot;Hello, world!&quot;</span>


<span class="k">def</span> <span class="nf">define_configurable_hello_pipeline</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s2">&quot;configurable_hello_pipeline&quot;</span><span class="p">,</span> <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">configurable_hello</span><span class="p">]</span>
    <span class="p">)</span>


<span class="k">def</span> <span class="nf">test_intro_tutorial_part_four</span><span class="p">():</span>
    <span class="n">execute_pipeline</span><span class="p">(</span>
        <span class="n">define_configurable_hello_pipeline</span><span class="p">(),</span>
        <span class="p">{</span><span class="s2">&quot;solids&quot;</span><span class="p">:</span> <span class="p">{</span><span class="s2">&quot;configurable_hello&quot;</span><span class="p">:</span> <span class="p">{</span><span class="s2">&quot;config&quot;</span><span class="p">:</span> <span class="s2">&quot;cn&quot;</span><span class="p">}}},</span>
    <span class="p">)</span>
</pre></div>
</td></tr></table></div>
</div>
<p>We will be exploring the <a class="reference internal" href="../apidocs/decorators.html#dagster.solid" title="dagster.solid"><code class="xref py py-func docutils literal notranslate"><span class="pre">&#64;solid</span></code></a> API in much more detail as this tutorial
proceeds. For now, the only salient difference is that the annotated function takes an additional
first parameter, <code class="docutils literal notranslate"><span class="pre">info</span></code>, which is of type
<a class="reference internal" href="../apidocs/definitions.html#dagster.TransformExecutionInfo" title="dagster.TransformExecutionInfo"><code class="xref py py-class docutils literal notranslate"><span class="pre">TransformExecutionInfo</span></code></a>. The property <code class="docutils literal notranslate"><span class="pre">info.config</span></code>
is the configuration passed into each individual solid.</p>
<p>That configuration is specified in the second argument to
<a class="reference internal" href="../apidocs/execution.html#dagster.execute_pipeline" title="dagster.execute_pipeline"><code class="xref py py-func docutils literal notranslate"><span class="pre">execute_pipeline</span></code></a>, which must be a dict. This dict specifies
<em>all</em> of the configuration to execute an entire pipeline. It may have many sections, but we’re only
using one of them here: per-solid configuration specified under the key <code class="docutils literal notranslate"><span class="pre">solids</span></code>:</p>
<p>The <code class="docutils literal notranslate"><span class="pre">solids</span></code> dict is keyed by solid name, and each of its values in turn defines a <code class="docutils literal notranslate"><span class="pre">config</span></code>
key corresponding to the user-defined configuration schema for each particular solid. In this case,
that’s a single scalar string value.</p>
<p>Run this from the command line utility. In order to do this you must provide
a yaml config file:</p>
<div class="literal-block-wrapper docutils container" id="id2">
<div class="code-block-caption"><span class="caption-text">config_env.yml</span><a class="headerlink" href="#id2" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre>1
2
3</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="n">solids</span><span class="p">:</span>
  <span class="n">configurable_hello</span><span class="p">:</span>
    <span class="n">config</span><span class="p">:</span> <span class="s2">&quot;haw&quot;</span>
</pre></div>
</td></tr></table></div>
</div>
<p>Now you can run this pipeline with this config file like so:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagster pipeline execute -f config.py <span class="se">\\</span>
-n define_configurable_hello_pipeline -e config_env.yml
</pre></div>
</div>
<p>To run this example from dagit, use the following command:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagit -f config.py -n define_configurable_hello_pipeline
</pre></div>
</div>
<p>Just as with configurable inputs, you can edit the configuration on the fly in dagit’s built-in
config editor. Try switching languages and rerunning the pipeline!</p>
<img alt="../_images/config_figure_one.png" src="../_images/config_figure_one.png" />
<p>Next, we’ll learn about another part of the <code class="docutils literal notranslate"><span class="pre">info</span></code> parameter, the
<a class="reference internal" href="execution_context.html"><span class="doc">Execution Context</span></a>, which we’ll use to parametrize features of the pipeline
execution environment that are common to many solids.</p>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="inputs.html">Inputs</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="inputs.html" title="previous chapter">Inputs</a></li>
      <li>Next: <a href="execution_context.html" title="next chapter">Execution Context</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/config.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/config.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 23'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Unit-testing Pipelines &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="Definitions" href="../apidocs/definitions.html" />
    <link rel="prev" title="Reusable Solids" href="part_thirteen.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="unit-testing-pipelines">
<h1>Unit-testing Pipelines<a class="headerlink" href="#unit-testing-pipelines" title="Permalink to this headline">¶</a></h1>
<p>Unit testing data pipelines is, broadly speaking, quite difficult. As a result, it is typically
never done.</p>
<p>One of the mechanisms included in dagster to enable testing has already been discussed: contexts.
The other mechanism is the ability to execute arbitrary subsets of a DAG. (This capability is
useful for other use cases but we will focus on unit testing for now).</p>
<p>Let us start where we left off.</p>
<p>We have the following pipeline:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">ConfigDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">load_number</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span>


<span class="nd">@lambda_solid</span><span class="p">(</span>
    <span class="n">inputs</span><span class="o">=</span><span class="p">[</span>
        <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num1&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
        <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num2&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="p">],</span>
    <span class="n">output</span><span class="o">=</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">adder</span><span class="p">(</span><span class="n">num1</span><span class="p">,</span> <span class="n">num2</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">num1</span> <span class="o">+</span> <span class="n">num2</span>


<span class="nd">@lambda_solid</span><span class="p">(</span>
    <span class="n">inputs</span><span class="o">=</span><span class="p">[</span>
        <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num1&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
        <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num2&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="p">],</span>
    <span class="n">output</span><span class="o">=</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">multer</span><span class="p">(</span><span class="n">num1</span><span class="p">,</span> <span class="n">num2</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">num1</span> <span class="o">*</span> <span class="n">num2</span>


<span class="k">def</span> <span class="nf">define_part_fourteen_step_one</span><span class="p">():</span>
    <span class="c1"># (a + b) * (c + d)</span>

    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;tutorial_part_thirteen_step_one&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">load_number</span><span class="p">,</span> <span class="n">adder</span><span class="p">,</span> <span class="n">multer</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="n">load_number</span><span class="o">.</span><span class="n">name</span><span class="p">,</span> <span class="s1">&#39;a&#39;</span><span class="p">):</span> <span class="p">{},</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="n">load_number</span><span class="o">.</span><span class="n">name</span><span class="p">,</span> <span class="s1">&#39;b&#39;</span><span class="p">):</span> <span class="p">{},</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="n">load_number</span><span class="o">.</span><span class="n">name</span><span class="p">,</span> <span class="s1">&#39;c&#39;</span><span class="p">):</span> <span class="p">{},</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="n">load_number</span><span class="o">.</span><span class="n">name</span><span class="p">,</span> <span class="s1">&#39;d&#39;</span><span class="p">):</span> <span class="p">{},</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="n">adder</span><span class="o">.</span><span class="n">name</span><span class="p">,</span> <span class="s1">&#39;a_plus_b&#39;</span><span class="p">):</span> <span class="p">{</span>
                <span class="s1">&#39;num1&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;a&#39;</span><span class="p">),</span>
                <span class="s1">&#39;num2&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;b&#39;</span><span class="p">),</span>
            <span class="p">},</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="n">adder</span><span class="o">.</span><span class="n">name</span><span class="p">,</span> <span class="s1">&#39;c_plus_d&#39;</span><span class="p">):</span> <span class="p">{</span>
                <span class="s1">&#39;num1&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;c&#39;</span><span class="p">),</span>
                <span class="s1">&#39;num2&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;d&#39;</span><span class="p">),</span>
            <span class="p">},</span>
            <span class="n">SolidInstance</span><span class="p">(</span><span class="n">multer</span><span class="o">.</span><span class="n">name</span><span class="p">,</span> <span class="s1">&#39;final&#39;</span><span class="p">):</span> <span class="p">{</span>
                <span class="s1">&#39;num1&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;a_plus_b&#39;</span><span class="p">),</span>
                <span class="s1">&#39;num2&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;c_plus_d&#39;</span><span class="p">),</span>
            <span class="p">},</span>
        <span class="p">},</span>
    <span class="p">)</span>
</pre></div>
</div>
<p>Let’s say we wanted to test <em>one</em> of these solids in isolation.</p>
<p>We want to do is isolate that solid and execute with inputs we
provide, instead of from solids upstream in the dependency graph.</p>
<p>So let’s do that. Follow along in the comments:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="c1"># The pipeline returned is a new unnamed, pipeline</span>
<span class="c1"># that contains the isolated solid plus the injected solids</span>
<span class="c1"># that will satisfy it inputs</span>
<span class="n">pipeline</span> <span class="o">=</span> <span class="n">PipelineDefinition</span><span class="o">.</span><span class="n">create_single_solid_pipeline</span><span class="p">(</span>
    <span class="c1">#</span>
    <span class="c1"># This takes an existing pipeline</span>
    <span class="c1">#</span>
    <span class="n">define_part_fourteen_step_one</span><span class="p">(),</span>
    <span class="c1">#</span>
    <span class="c1"># Isolates a single solid. In this case &quot;final&quot;</span>
    <span class="c1">#</span>
    <span class="s1">&#39;final&#39;</span><span class="p">,</span>
    <span class="c1">#</span>
    <span class="c1"># Final has two inputs, num1 and num2. You must provide</span>
    <span class="c1"># values for this. So we create solids in memory to provide</span>
    <span class="c1"># values. The solids we are just emit the passed in values</span>
    <span class="c1"># as an output</span>
    <span class="c1">#</span>
    <span class="n">injected_solids</span><span class="o">=</span><span class="p">{</span>
        <span class="s1">&#39;final&#39;</span><span class="p">:</span> <span class="p">{</span>
            <span class="s1">&#39;num1&#39;</span><span class="p">:</span> <span class="n">define_stub_solid</span><span class="p">(</span><span class="s1">&#39;stub_a&#39;</span><span class="p">,</span> <span class="mi">3</span><span class="p">),</span>
            <span class="s1">&#39;num2&#39;</span><span class="p">:</span> <span class="n">define_stub_solid</span><span class="p">(</span><span class="s1">&#39;stub_b&#39;</span><span class="p">,</span> <span class="mi">4</span><span class="p">),</span>
        <span class="p">}</span>
    <span class="p">}</span>
<span class="p">)</span>

<span class="n">result</span> <span class="o">=</span> <span class="n">execute_pipeline</span><span class="p">(</span><span class="n">pipeline</span><span class="p">)</span>

<span class="k">assert</span> <span class="n">result</span><span class="o">.</span><span class="n">success</span>
<span class="k">assert</span> <span class="nb">len</span><span class="p">(</span><span class="n">result</span><span class="o">.</span><span class="n">result_list</span><span class="p">)</span> <span class="o">==</span> <span class="mi">3</span>
<span class="k">assert</span> <span class="n">result</span><span class="o">.</span><span class="n">result_for_solid</span><span class="p">(</span><span class="s1">&#39;stub_a&#39;</span><span class="p">)</span><span class="o">.</span><span class="n">transformed_value</span><span class="p">()</span> <span class="o">==</span> <span class="mi">3</span>
<span class="k">assert</span> <span class="n">result</span><span class="o">.</span><span class="n">result_for_solid</span><span class="p">(</span><span class="s1">&#39;stub_b&#39;</span><span class="p">)</span><span class="o">.</span><span class="n">transformed_value</span><span class="p">()</span> <span class="o">==</span> <span class="mi">4</span>
<span class="k">assert</span> <span class="n">result</span><span class="o">.</span><span class="n">result_for_solid</span><span class="p">(</span><span class="s1">&#39;final&#39;</span><span class="p">)</span><span class="o">.</span><span class="n">transformed_value</span><span class="p">()</span> <span class="o">==</span> <span class="mi">12</span>
</pre></div>
</div>
<p>We can also execute entire arbitrary subdags rather than a single solid.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="k">def</span> <span class="nf">test_a_plus_b_final_subdag</span><span class="p">():</span>
    <span class="n">pipeline</span> <span class="o">=</span> <span class="n">PipelineDefinition</span><span class="o">.</span><span class="n">create_sub_pipeline</span><span class="p">(</span>
        <span class="n">define_part_fourteen_step_one</span><span class="p">(),</span>
        <span class="p">[</span><span class="s1">&#39;a_plus_b&#39;</span><span class="p">,</span> <span class="s1">&#39;final&#39;</span><span class="p">],</span>
        <span class="p">[</span><span class="s1">&#39;final&#39;</span><span class="p">],</span>
        <span class="n">injected_solids</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;a_plus_b&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;num1&#39;</span><span class="p">:</span> <span class="n">define_stub_solid</span><span class="p">(</span><span class="s1">&#39;stub_a&#39;</span><span class="p">,</span> <span class="mi">2</span><span class="p">),</span>
                <span class="s1">&#39;num2&#39;</span><span class="p">:</span> <span class="n">define_stub_solid</span><span class="p">(</span><span class="s1">&#39;stub_b&#39;</span><span class="p">,</span> <span class="mi">4</span><span class="p">),</span>
            <span class="p">},</span>
            <span class="s1">&#39;final&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;num2&#39;</span><span class="p">:</span> <span class="n">define_stub_solid</span><span class="p">(</span><span class="s1">&#39;stub_c_plus_d&#39;</span><span class="p">,</span> <span class="mi">6</span><span class="p">),</span>
            <span class="p">}</span>
        <span class="p">},</span>
    <span class="p">)</span>

    <span class="n">pipeline_result</span> <span class="o">=</span> <span class="n">execute_pipeline</span><span class="p">(</span><span class="n">pipeline</span><span class="p">)</span>

    <span class="k">assert</span> <span class="n">pipeline_result</span><span class="o">.</span><span class="n">result_for_solid</span><span class="p">(</span><span class="s1">&#39;a_plus_b&#39;</span><span class="p">)</span><span class="o">.</span><span class="n">transformed_value</span><span class="p">()</span> <span class="o">==</span> <span class="mi">6</span>
    <span class="k">assert</span> <span class="n">pipeline_result</span><span class="o">.</span><span class="n">result_for_solid</span><span class="p">(</span><span class="s1">&#39;final&#39;</span><span class="p">)</span><span class="o">.</span><span class="n">transformed_value</span><span class="p">()</span> <span class="o">==</span> <span class="mi">36</span>
</pre></div>
</div>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="part_thirteen.html" title="previous chapter">Reusable Solids</a></li>
      <li>Next: <a href="../apidocs/definitions.html" title="next chapter">Definitions</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/part_fourteen.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/part_fourteen.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 24'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Hello, World &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="Hello, DAG" href="hello_dag.html" />
    <link rel="prev" title="Contributing" href="../contributing.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="hello-world">
<h1>Hello, World<a class="headerlink" href="#hello-world" title="Permalink to this headline">¶</a></h1>
<p>See <a class="reference internal" href="../installation.html"><span class="doc">Installation</span></a> for instructions getting dagster – the core library – and dagit –
the web UI tool used to visualize your data pipelines – installed on your platform of choice.</p>
<p>Let’s write our first pipeline and save it as <code class="docutils literal notranslate"><span class="pre">hello_world.py</span></code>.</p>
<div class="literal-block-wrapper docutils container" id="id1">
<div class="code-block-caption"><span class="caption-text">hello_world.py</span><a class="headerlink" href="#id1" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre> 1
 2
 3
 4
 5
 6
 7
 8
 9
10</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="kn">from</span> <span class="nn">dagster</span> <span class="k">import</span> <span class="n">PipelineDefinition</span><span class="p">,</span> <span class="n">execute_pipeline</span><span class="p">,</span> <span class="n">lambda_solid</span>


<span class="nd">@lambda_solid</span>
<span class="k">def</span> <span class="nf">hello_world</span><span class="p">():</span>
    <span class="k">return</span> <span class="s1">&#39;hello&#39;</span>


<span class="k">def</span> <span class="nf">define_hello_world_pipeline</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
</pre></div>
</td></tr></table></div>
</div>
<p>This example introduces three concepts:</p>
<ol class="arabic simple">
<li>A <strong>solid</strong> is a functional unit of computation in a data pipeline. In this example, we use the
decorator <a class="reference internal" href="../apidocs/decorators.html#dagster.lambda_solid" title="dagster.lambda_solid"><code class="xref py py-func docutils literal notranslate"><span class="pre">&#64;lambda_solid</span></code></a> to mark the function <code class="docutils literal notranslate"><span class="pre">hello_world</span></code>
as a solid: a functional unit which takes no inputs and returns the output <code class="docutils literal notranslate"><span class="pre">\'hello\'</span></code> every
time it’s run.</li>
<li>A <strong>pipeline</strong> is a set of solids arranged into a DAG of computation that produces data assets.
In this example, the call to <a class="reference internal" href="../apidocs/definitions.html#dagster.PipelineDefinition" title="dagster.PipelineDefinition"><code class="xref py py-class docutils literal notranslate"><span class="pre">PipelineDefinition</span></code></a> defines
a pipeline with a single solid.</li>
<li>We <strong>execute</strong> the pipeline by running <a class="reference internal" href="../apidocs/execution.html#dagster.execute_pipeline" title="dagster.execute_pipeline"><code class="xref py py-func docutils literal notranslate"><span class="pre">execute_pipeline</span></code></a>.
Dagster will call into each solid in the pipeline, functionally transforming its inputs, if any,
and threading its outputs to solids further on in the DAG.</li>
</ol>
<div class="section" id="pipeline-execution">
<h2>Pipeline Execution<a class="headerlink" href="#pipeline-execution" title="Permalink to this headline">¶</a></h2>
<p>Assuming you’ve saved this pipeline as <code class="docutils literal notranslate"><span class="pre">hello_world.py</span></code>, we can execute it via any of three
different mechanisms:</p>
<ol class="arabic simple">
<li>The CLI utility <cite>dagster</cite></li>
<li>The GUI tool <cite>dagit</cite></li>
<li>Using dagster as a library within your own script.</li>
</ol>
<div class="section" id="cli">
<h3>CLI<a class="headerlink" href="#cli" title="Permalink to this headline">¶</a></h3>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagster pipeline execute -f hello_world.py -n define_hello_world_pipeline
<span class="go">2019-01-08 11:23:57 - dagster - INFO - orig_message=&quot;Beginning execution of pipeline hello_world_pipeline&quot; log_message_id=&quot;5c829421-06c7-49eb-9195-7e828e37eab8&quot; run_id=&quot;dfc8165a-f37e-43f5-a801-b602e4409f74&quot; pipeline=&quot;hello_world_pipeline&quot; event_type=&quot;PIPELINE_START&quot;</span>
<span class="go">2019-01-08 11:23:57 - dagster - INFO - orig_message=&quot;Beginning execution of hello_world.transform&quot; log_message_id=&quot;5878513a-b510-4837-88cb-f77205931abb&quot; run_id=&quot;dfc8165a-f37e-43f5-a801-b602e4409f74&quot; pipeline=&quot;hello_world_pipeline&quot; solid=&quot;hello_world&quot; solid_definition=&quot;hello_world&quot; event_type=&quot;EXECUTION_PLAN_STEP_START&quot; step_key=&quot;hello_world.transform&quot;</span>
<span class="go">2019-01-08 11:23:57 - dagster - INFO - orig_message=&quot;Solid hello_world emitted output \\&quot;result\\&quot; value &#39;hello&#39;&quot; log_message_id=&quot;b27fb70a-744a-46cc-81ba-677247b1b07b&quot; run_id=&quot;dfc8165a-f37e-43f5-a801-b602e4409f74&quot; pipeline=&quot;hello_world_pipeline&quot; solid=&quot;hello_world&quot; solid_definition=&quot;hello_world&quot;</span>
<span class="go">2019-01-08 11:23:57 - dagster - INFO - orig_message=&quot;Execution of hello_world.transform succeeded in 0.9558200836181641&quot; log_message_id=&quot;25faadf5-b5a8-4251-b85c-dea6d00d99f0&quot; run_id=&quot;dfc8165a-f37e-43f5-a801-b602e4409f74&quot; pipeline=&quot;hello_world_pipeline&quot; solid=&quot;hello_world&quot; solid_definition=&quot;hello_world&quot; event_type=&quot;EXECUTION_PLAN_STEP_SUCCESS&quot; millis=0.9558200836181641 step_key=&quot;hello_world.transform&quot;</span>
<span class="go">2019-01-08 11:23:57 - dagster - INFO - orig_message=&quot;Step hello_world.transform emitted &#39;hello&#39; for output result&quot; log_message_id=&quot;604dc47c-fe29-4d71-a531-97ae58fda0f4&quot; run_id=&quot;dfc8165a-f37e-43f5-a801-b602e4409f74&quot; pipeline=&quot;hello_world_pipeline&quot;</span>
<span class="go">2019-01-08 11:23:57 - dagster - INFO - orig_message=&quot;Completing successful execution of pipeline hello_world_pipeline&quot; log_message_id=&quot;1563854b-758f-4ae2-8399-cb75946b0055&quot; run_id=&quot;dfc8165a-f37e-43f5-a801-b602e4409f74&quot; pipeline=&quot;hello_world_pipeline&quot; event_type=&quot;PIPELINE_SUCCESS&quot;</span>
</pre></div>
</div>
<p>There’s a lot of information in these log lines (we’ll get to how you can use, and customize,
them later), but you can see that the third message is:
<code class="docutils literal notranslate"><span class="pre">`Solid</span> <span class="pre">hello_world</span> <span class="pre">emitted</span> <span class="pre">output</span> <span class="pre">\\&quot;result\\&quot;</span> <span class="pre">value</span> <span class="pre">\'hello\'&quot;`</span></code>. Success!</p>
</div>
<div class="section" id="dagit">
<h3>Dagit<a class="headerlink" href="#dagit" title="Permalink to this headline">¶</a></h3>
<p>To visualize your pipeline (which only has one node) in dagit, you can run:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> dagit -f hello_world.py -n define_hello_world_pipeline
<span class="go">Serving on http://127.0.0.1:3000</span>
</pre></div>
</div>
<p>You should be able to navigate to <a class="reference external" href="http://127.0.0.1:3000/hello_world_pipeline/explore">http://127.0.0.1:3000/hello_world_pipeline/explore</a> in your web
browser and view your pipeline.</p>
<img alt="../_images/hello_world_figure_one.png" src="../_images/hello_world_figure_one.png" />
<p>There are lots of ways to execute dagster pipelines. If you navigate to the “Execute”
tab (<a class="reference external" href="http://127.0.0.1:3000/hello_world_pipeline/execute">http://127.0.0.1:3000/hello_world_pipeline/execute</a>), you can execute your pipeline directly
from dagit. Logs will stream into the bottom right pane of the interface, where you can filter them
by log level.</p>
<img alt="../_images/hello_world_figure_two.png" src="../_images/hello_world_figure_two.png" />
</div>
<div class="section" id="library">
<h3>Library<a class="headerlink" href="#library" title="Permalink to this headline">¶</a></h3>
<p>If you’d rather execute your pipelines as a script, you can do that without using the dagster CLI
at all. Just add a few lines to <cite>hello_world.py</cite> (highlighted in yellow):</p>
<div class="literal-block-wrapper docutils container" id="id2">
<div class="code-block-caption"><span class="caption-text">hello_world.py</span><a class="headerlink" href="#id2" title="Permalink to this code">¶</a></div>
<div class="highlight-default notranslate"><table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre> 1
 2
 3
 4
 5
 6
 7
 8
 9
10
11
12
13
14
15
16
17</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="hll"><span class="kn">from</span> <span class="nn">dagster</span> <span class="k">import</span> <span class="n">PipelineDefinition</span><span class="p">,</span> <span class="n">execute_pipeline</span><span class="p">,</span> <span class="n">lambda_solid</span>
</span>

<span class="nd">@lambda_solid</span>
<span class="k">def</span> <span class="nf">hello_world</span><span class="p">():</span>
    <span class="k">return</span> <span class="s1">&#39;hello&#39;</span>


<span class="k">def</span> <span class="nf">define_hello_world_pipeline</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;hello_world_pipeline&#39;</span><span class="p">,</span> <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">hello_world</span><span class="p">]</span>
    <span class="p">)</span>
<span class="hll">
</span><span class="hll">
</span><span class="hll"><span class="k">if</span> <span class="vm">__name__</span> <span class="o">==</span> <span class="s1">&#39;__main__&#39;</span><span class="p">:</span>
</span>    <span class="n">result</span> <span class="o">=</span> <span class="n">execute_pipeline</span><span class="p">(</span><span class="n">define_hello_world_pipeline</span><span class="p">())</span>
    <span class="k">assert</span> <span class="n">result</span><span class="o">.</span><span class="n">success</span>
</pre></div>
</td></tr></table></div>
</div>
<p>Then you can just run:</p>
<div class="highlight-console notranslate"><div class="highlight"><pre><span></span><span class="gp">$</span> python hello_world.py
</pre></div>
</div>
<p>Next, let’s build our first multi-solid DAG in <a class="reference internal" href="hello_dag.html"><span class="doc">Hello, DAG</span></a>!</p>
</div>
</div>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1 current"><a class="current reference internal" href="#">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_nine.html">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="../contributing.html" title="previous chapter">Contributing</a></li>
      <li>Next: <a href="hello_dag.html" title="next chapter">Hello, DAG</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/hello_world.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/hello_world.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 25'] = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="X-UA-Compatible" content="IE=Edge" />
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Custom Contexts &#8212; Dagster  documentation</title>
    <link rel="stylesheet" href="../_static/alabaster.css" type="text/css" />
    <link rel="stylesheet" href="../_static/pygments.css" type="text/css" />
    <script type="text/javascript" id="documentation_options" data-url_root="../" src="../_static/documentation_options.js"></script>
    <script type="text/javascript" src="../_static/jquery.js"></script>
    <script type="text/javascript" src="../_static/underscore.js"></script>
    <script type="text/javascript" src="../_static/doctools.js"></script>
    <link rel="index" title="Index" href="../genindex.html" />
    <link rel="search" title="Search" href="../search.html" />
    <link rel="next" title="Expectations" href="part_ten.html" />
    <link rel="prev" title="Configuration Schemas" href="configuration_schemas.html" />
   
  <link rel="stylesheet" href="../_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <div class="section" id="custom-contexts">
<h1>Custom Contexts<a class="headerlink" href="#custom-contexts" title="Permalink to this headline">¶</a></h1>
<p>So far we have used contexts for configuring logging level only. This barely scratched the surface
of its capabilities.</p>
<p>Testing data pipelines, for a number of reasons, is notoriously difficult. One of the reasons is
that as one moves a data pipeline from local development, to unit testing, to integration testing, to CI/CD,
to production, or to whatever environment you need to operate in, the operating environment can
change dramatically.</p>
<p>In order to handle this, whenever the business logic of a pipeline is interacting with external resources
or dealing with pipeline-wide state generally, the dagster user is expected to interact with these resources
and that state via the context object. Examples would include database connections, connections to cloud services,
interactions with scratch directories on your local filesystem, and so on.</p>
<p>Let’s imagine a scenario where we want to record some custom state in a key-value store for our execution runs.
A production time, this key-value store is a live store (e.g. DynamoDB in amazon) but we do not want to interact
this store for unit-testing. Contexts will be our tool to accomplish this goal.</p>
<p>We’re going to have a simple pipeline that does some rudimentary arithmetic, but that wants to record
the result of its computations in that key value store.</p>
<p>Let’s first set up a simple pipeline. We ingest two numbers (each in their own trivial solid)
and then two downstream solids add and multiple those numbers, respectively.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">ConfigDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">ingest_a</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span>


<span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">ConfigDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">ingest_b</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span>


<span class="nd">@solid</span><span class="p">(</span>
    <span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num_one&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
            <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num_two&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">add_ints</span><span class="p">(</span><span class="n">_info</span><span class="p">,</span> <span class="n">num_one</span><span class="p">,</span> <span class="n">num_two</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">num_one</span> <span class="o">+</span> <span class="n">num_two</span>


<span class="nd">@solid</span><span class="p">(</span>
    <span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num_one&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
            <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num_two&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">mult_ints</span><span class="p">(</span><span class="n">_info</span><span class="p">,</span> <span class="n">num_one</span><span class="p">,</span> <span class="n">num_two</span><span class="p">):</span>
    <span class="k">return</span> <span class="n">num_one</span> <span class="o">*</span> <span class="n">num_two</span>


<span class="k">def</span> <span class="nf">define_part_nine_step_one</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
        <span class="n">name</span><span class="o">=</span><span class="s1">&#39;part_nine&#39;</span><span class="p">,</span>
        <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">ingest_a</span><span class="p">,</span> <span class="n">ingest_b</span><span class="p">,</span> <span class="n">add_ints</span><span class="p">,</span> <span class="n">mult_ints</span><span class="p">],</span>
        <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
            <span class="s1">&#39;add_ints&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;num_one&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;ingest_a&#39;</span><span class="p">),</span>
                <span class="s1">&#39;num_two&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;ingest_b&#39;</span><span class="p">),</span>
            <span class="p">},</span>
            <span class="s1">&#39;mult_ints&#39;</span><span class="p">:</span> <span class="p">{</span>
                <span class="s1">&#39;num_one&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;ingest_a&#39;</span><span class="p">),</span>
                <span class="s1">&#39;num_two&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;ingest_b&#39;</span><span class="p">),</span>
            <span class="p">},</span>
        <span class="p">},</span>
    <span class="p">)</span>
</pre></div>
</div>
<p>Now we configure execution using a env.yml file:</p>
<div class="highlight-yaml notranslate"><div class="highlight"><pre><span></span><span class="nt">context</span><span class="p">:</span>
<span class="nt">default</span><span class="p">:</span>
    <span class="nt">config</span><span class="p">:</span>
    <span class="nt">log_level</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">DEBUG</span>

<span class="nt">solids</span><span class="p">:</span>
<span class="nt">ingest_a</span><span class="p">:</span>
    <span class="nt">config</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">2</span>
<span class="nt">ingest_b</span><span class="p">:</span>
    <span class="nt">config</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">3</span>
</pre></div>
</div>
<p>And you should see some log spew indicating execution.</p>
<p>Now imagine we want to log some of the values passing through these solids
into some sort of key value store in cloud storage.</p>
<p>Let’s say we have a module called <code class="docutils literal notranslate"><span class="pre">cloud</span></code> that allows for interaction
with this key value store. You have to create an instance of a <code class="docutils literal notranslate"><span class="pre">PublicCloudConn</span></code>
class and then pass that to a function <code class="docutils literal notranslate"><span class="pre">set_value_in_cloud_store</span></code> to interact
with the service.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="kn">from</span> <span class="nn">cloud</span> <span class="kn">import</span> <span class="p">(</span><span class="n">PublicCloudConn</span><span class="p">,</span> <span class="n">set_value_in_cloud_store</span><span class="p">)</span>

<span class="c1"># imagine implementations such as the following</span>
<span class="c1"># class PublicCloudConn:</span>
<span class="c1">#     def __init__(self, creds):</span>
<span class="c1">#         self.creds = creds</span>


<span class="c1"># def set_value_in_cloud_store(_conn, _key, _value):</span>
<span class="c1">#     # imagine this doing something</span>
<span class="c1">#     pass</span>

<span class="n">conn</span> <span class="o">=</span> <span class="n">PublicCloudConn</span><span class="p">({</span><span class="s1">&#39;user&#39;</span><span class="p">:</span> <span class="n">some_user</span><span class="s1">&#39;, &#39;</span><span class="k">pass</span><span class="s1">&#39; : &#39;</span><span class="n">some_pwd</span><span class="s1">&#39;})</span>
<span class="n">set_value_in_cloud_store</span><span class="p">(</span><span class="n">conn</span><span class="p">,</span> <span class="s1">&#39;some_key&#39;</span><span class="p">,</span> <span class="s1">&#39;some_value&#39;</span><span class="p">)</span>
</pre></div>
</div>
<p>Naively let’s add this to one of our transforms:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">ConfigDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">ingest_a</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="n">conn</span> <span class="o">=</span> <span class="n">PublicCloudConn</span><span class="p">(</span><span class="s1">&#39;some_user&#39;</span><span class="p">,</span> <span class="s1">&#39;some_pwd&#39;</span><span class="p">)</span>
    <span class="n">set_value_in_cloud_store</span><span class="p">(</span><span class="n">conn</span><span class="p">,</span> <span class="s1">&#39;a&#39;</span><span class="p">,</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">)</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span>
</pre></div>
</div>
<p>As coded above this is a bad idea on any number of dimensions. Foe one, the username/password
combo is hard coded. We could pass it in as a configuration of the solid. However that
is only in scope for that particular solid. So now the configuration would be passed into
each and every solid that needs it. This sucks. The connection would have to be created within
every solid. Either you would have to implement your own connection pooling or take the hit
of a new connection per solid. This also sucks.</p>
<p>More subtlely, what was previously a nice, isolated, testable piece of software is now hard-coded
to interact with some externalized resource and requires an internet connection, access to
a cloud service, and that could intermittently fail, and that would be slow relative to pure
in-memory compute. This code is no longer testable in any sort of reliable way.</p>
<p>This is where the concept of the context shines. What we want to do is attach an object to the
context object – which a single instance of is flowed through the entire execution – that
provides an interface to that cloud store that caches that connection and also provides a
swappable implementation of that store for test isolation. We want code that ends up looking like
this:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">ConfigDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">ingest_a</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="c1"># The store should be an interface to the cloud store</span>
    <span class="c1"># We will explain the ``resources`` property later.</span>
    <span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="o">.</span><span class="n">resources</span><span class="o">.</span><span class="n">store</span><span class="o">.</span><span class="n">record_value</span><span class="p">(</span><span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="p">,</span> <span class="s1">&#39;a&#39;</span><span class="p">,</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">)</span>
    <span class="k">return</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span>
</pre></div>
</div>
<p>The user will be able have complete control the creation of the <code class="docutils literal notranslate"><span class="pre">store</span></code> object attached to
the <code class="docutils literal notranslate"><span class="pre">resources</span></code> object, which allows a pipeline designer to insert seams of testability.</p>
<p>This ends up accomplishing our goal of being able to test this pipeline in multiple environments
with <em>zero changes to the core business logic.</em> The only thing that will vary between environments
is configuration and the context generated because of that configuration.</p>
<p>We need this store object, and two implementations of it. One that talks to the public cloud
service, and one that is an in-memory implementation of this.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="k">class</span> <span class="nc">PublicCloudStore</span><span class="p">:</span>
    <span class="k">def</span> <span class="fm">__init__</span><span class="p">(</span><span class="bp">self</span><span class="p">,</span> <span class="n">credentials</span><span class="p">):</span>
        <span class="bp">self</span><span class="o">.</span><span class="n">conn</span> <span class="o">=</span> <span class="n">PublicCloudConn</span><span class="p">(</span><span class="n">credentials</span><span class="p">)</span>

    <span class="k">def</span> <span class="nf">record_value</span><span class="p">(</span><span class="bp">self</span><span class="p">,</span> <span class="n">context</span><span class="p">,</span> <span class="n">key</span><span class="p">,</span> <span class="n">value</span><span class="p">):</span>
        <span class="n">context</span><span class="o">.</span><span class="n">info</span><span class="p">(</span><span class="s1">&#39;Setting key={key} value={value} in cloud&#39;</span>
            <span class="o">.</span><span class="n">format</span><span class="p">(</span>
                <span class="n">key</span><span class="o">=</span><span class="n">key</span><span class="p">,</span>
                <span class="n">value</span><span class="o">=</span><span class="n">value</span><span class="p">,</span>
            <span class="p">)</span>
        <span class="p">)</span>
        <span class="n">set_value_in_cloud_store</span><span class="p">(</span><span class="bp">self</span><span class="o">.</span><span class="n">conn</span><span class="p">,</span> <span class="n">key</span><span class="p">,</span> <span class="n">value</span><span class="p">)</span>


<span class="k">class</span> <span class="nc">InMemoryStore</span><span class="p">:</span>
    <span class="k">def</span> <span class="fm">__init__</span><span class="p">(</span><span class="bp">self</span><span class="p">):</span>
        <span class="bp">self</span><span class="o">.</span><span class="n">values</span> <span class="o">=</span> <span class="p">{}</span>

    <span class="k">def</span> <span class="nf">record_value</span><span class="p">(</span><span class="bp">self</span><span class="p">,</span> <span class="n">context</span><span class="p">,</span> <span class="n">key</span><span class="p">,</span> <span class="n">value</span><span class="p">):</span>
        <span class="n">context</span><span class="o">.</span><span class="n">info</span><span class="p">(</span><span class="s1">&#39;Setting key={key} value={value} in memory&#39;</span><span class="o">.</span>
            <span class="n">format</span><span class="p">(</span>
                <span class="n">key</span><span class="o">=</span><span class="n">key</span><span class="p">,</span>
                <span class="n">value</span><span class="o">=</span><span class="n">value</span><span class="p">,</span>
            <span class="p">)</span>
        <span class="p">)</span>
        <span class="bp">self</span><span class="o">.</span><span class="n">values</span><span class="p">[</span><span class="n">key</span><span class="p">]</span> <span class="o">=</span> <span class="n">value</span>
</pre></div>
</div>
<p>Now we need to create one of these stores and put them into the context. The pipeline author must
create a <code class="xref py py-class docutils literal notranslate"><span class="pre">PipelineContextDefinition</span></code>.</p>
<p>It two primary attributes:</p>
<p>1) A configuration definition that allows the pipeline author to define what configuration
is needed to create the ExecutionContext.
2) A function that returns an instance of an ExecutionContext. This context is flowed through
the entire execution.</p>
<p>First let’s create the context suitable for local testing:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="n">PartNineResources</span> <span class="o">=</span> <span class="n">namedtuple</span><span class="p">(</span><span class="s1">&#39;PartNineResources&#39;</span><span class="p">,</span> <span class="s1">&#39;store&#39;</span><span class="p">)</span>

<span class="n">PipelineContextDefinition</span><span class="p">(</span>
    <span class="n">context_fn</span><span class="o">=</span><span class="k">lambda</span> <span class="n">_info</span><span class="p">:</span>
        <span class="n">ExecutionContext</span><span class="o">.</span><span class="n">console_logging</span><span class="p">(</span>
            <span class="n">log_level</span><span class="o">=</span><span class="n">DEBUG</span><span class="p">,</span>
            <span class="n">resources</span><span class="o">=</span><span class="n">PartNineResources</span><span class="p">(</span><span class="n">InMemoryStore</span><span class="p">())</span>
        <span class="p">)</span>
<span class="p">)</span>
</pre></div>
</div>
<p>This context requires <em>no</em> configuration so it is not specified. We then
provide a lambda which creates an ExecutionContext. You’ll notice that we pass
in a log_level and a “resources” object. The resources object can be any
python object. What is demonstrated above is a convention. The resources
object that the user creates will be passed through the execution.</p>
<p>So if we return to the implementation of the solids that includes the interaction
with the key-value store, you can see how this will invoke the in-memory store object
which is attached the resources property of the context.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">ConfigDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">ingest_a</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="o">.</span><span class="n">resources</span><span class="o">.</span><span class="n">store</span><span class="o">.</span><span class="n">record_value</span><span class="p">(</span><span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="p">,</span> <span class="s1">&#39;a&#39;</span><span class="p">,</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">)</span>
    <span class="k">return</span> <span class="n">conf</span>

<span class="nd">@solid</span><span class="p">(</span>
    <span class="n">config_field</span><span class="o">=</span><span class="n">ConfigDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">ingest_b</span><span class="p">(</span><span class="n">info</span><span class="p">):</span>
    <span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="o">.</span><span class="n">resources</span><span class="o">.</span><span class="n">store</span><span class="o">.</span><span class="n">record_value</span><span class="p">(</span><span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="p">,</span> <span class="s1">&#39;b&#39;</span><span class="p">,</span> <span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">)</span>
    <span class="k">return</span> <span class="n">conf</span>


<span class="nd">@solid</span><span class="p">(</span>
    <span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num_one&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
            <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num_two&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">add_ints</span><span class="p">(</span><span class="n">info</span><span class="p">,</span> <span class="n">num_one</span><span class="p">,</span> <span class="n">num_two</span><span class="p">):</span>
    <span class="n">result</span> <span class="o">=</span> <span class="n">num_one</span> <span class="o">+</span> <span class="n">num_two</span>
    <span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="o">.</span><span class="n">resources</span><span class="o">.</span><span class="n">store</span><span class="o">.</span><span class="n">record_value</span><span class="p">(</span><span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="p">,</span> <span class="s1">&#39;add&#39;</span><span class="p">,</span> <span class="n">result</span><span class="p">)</span>
    <span class="k">return</span> <span class="n">result</span>


<span class="nd">@solid</span><span class="p">(</span>
    <span class="n">inputs</span><span class="o">=</span><span class="p">[</span><span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num_one&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">),</span>
            <span class="n">InputDefinition</span><span class="p">(</span><span class="s1">&#39;num_two&#39;</span><span class="p">,</span> <span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
    <span class="n">outputs</span><span class="o">=</span><span class="p">[</span><span class="n">OutputDefinition</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Int</span><span class="p">)],</span>
<span class="p">)</span>
<span class="k">def</span> <span class="nf">mult_ints</span><span class="p">(</span><span class="n">info</span><span class="p">,</span> <span class="n">num_one</span><span class="p">,</span> <span class="n">num_two</span><span class="p">):</span>
    <span class="n">result</span> <span class="o">=</span> <span class="n">num_one</span> <span class="o">*</span> <span class="n">num_two</span>
    <span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="o">.</span><span class="n">resources</span><span class="o">.</span><span class="n">store</span><span class="o">.</span><span class="n">record_value</span><span class="p">(</span><span class="n">info</span><span class="o">.</span><span class="n">context</span><span class="p">,</span> <span class="s1">&#39;mult&#39;</span><span class="p">,</span> <span class="n">result</span><span class="p">)</span>
    <span class="k">return</span> <span class="n">result</span>
</pre></div>
</div>
<p>Now we need to declare the pipeline to use this PipelineContextDefinition.
We do so with the following:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="k">return</span> <span class="n">PipelineDefinition</span><span class="p">(</span>
    <span class="n">name</span><span class="o">=</span><span class="s1">&#39;part_nine&#39;</span><span class="p">,</span>
    <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">ingest_a</span><span class="p">,</span> <span class="n">ingest_b</span><span class="p">,</span> <span class="n">add_ints</span><span class="p">,</span> <span class="n">mult_ints</span><span class="p">],</span>
    <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
        <span class="s1">&#39;add_ints&#39;</span><span class="p">:</span> <span class="p">{</span>
            <span class="s1">&#39;num_one&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;ingest_a&#39;</span><span class="p">),</span>
            <span class="s1">&#39;num_two&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;ingest_b&#39;</span><span class="p">),</span>
        <span class="p">},</span>
        <span class="s1">&#39;mult_ints&#39;</span><span class="p">:</span> <span class="p">{</span>
            <span class="s1">&#39;num_one&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;ingest_a&#39;</span><span class="p">),</span>
            <span class="s1">&#39;num_two&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;ingest_b&#39;</span><span class="p">),</span>
        <span class="p">},</span>
    <span class="p">},</span>
    <span class="n">context_definitions</span><span class="o">=</span><span class="p">{</span>
        <span class="s1">&#39;local&#39;</span><span class="p">:</span> <span class="n">PipelineContextDefinition</span><span class="p">(</span>
            <span class="n">context_fn</span><span class="o">=</span><span class="k">lambda</span> <span class="n">_info</span><span class="p">:</span>
                <span class="n">ExecutionContext</span><span class="o">.</span><span class="n">console_logging</span><span class="p">(</span>
                    <span class="n">log_level</span><span class="o">=</span><span class="n">DEBUG</span><span class="p">,</span>
                    <span class="n">resources</span><span class="o">=</span><span class="n">PartNineResources</span><span class="p">(</span><span class="n">InMemoryStore</span><span class="p">())</span>
                <span class="p">),</span>
            <span class="p">)</span>
        <span class="p">),</span>
    <span class="p">}</span>
<span class="p">)</span>
</pre></div>
</div>
<p>You’ll notice that we have “named” the context local. Now when we invoke that context,
we config it with that name.</p>
<div class="highlight-yaml notranslate"><div class="highlight"><pre><span></span><span class="nt">context</span><span class="p">:</span>
    <span class="nt">local</span><span class="p">:</span>

<span class="nt">solids</span><span class="p">:</span>
    <span class="nt">ingest_a</span><span class="p">:</span>
        <span class="nt">config</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">2</span>
    <span class="nt">ingest_b</span><span class="p">:</span>
        <span class="nt">config</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">3</span>
</pre></div>
</div>
<p>Now run the pipeline and you should see logging indicating the execution is occuring.</p>
<p>Now let us add a different context definition that substitutes in the production
version of that store.</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="n">PipelineDefinition</span><span class="p">(</span>
    <span class="n">name</span><span class="o">=</span><span class="s1">&#39;part_nine&#39;</span><span class="p">,</span>
    <span class="n">solids</span><span class="o">=</span><span class="p">[</span><span class="n">ingest_a</span><span class="p">,</span> <span class="n">ingest_b</span><span class="p">,</span> <span class="n">add_ints</span><span class="p">,</span> <span class="n">mult_ints</span><span class="p">],</span>
    <span class="n">dependencies</span><span class="o">=</span><span class="p">{</span>
        <span class="s1">&#39;add_ints&#39;</span><span class="p">:</span> <span class="p">{</span>
            <span class="s1">&#39;num_one&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;ingest_a&#39;</span><span class="p">),</span>
            <span class="s1">&#39;num_two&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;ingest_b&#39;</span><span class="p">),</span>
        <span class="p">},</span>
        <span class="s1">&#39;mult_ints&#39;</span><span class="p">:</span> <span class="p">{</span>
            <span class="s1">&#39;num_one&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;ingest_a&#39;</span><span class="p">),</span>
            <span class="s1">&#39;num_two&#39;</span><span class="p">:</span> <span class="n">DependencyDefinition</span><span class="p">(</span><span class="s1">&#39;ingest_b&#39;</span><span class="p">),</span>
        <span class="p">},</span>
    <span class="p">},</span>
    <span class="n">context_definitions</span><span class="o">=</span><span class="p">{</span>
        <span class="s1">&#39;local&#39;</span><span class="p">:</span> <span class="n">PipelineContextDefinition</span><span class="p">(</span>
            <span class="n">context_fn</span><span class="o">=</span><span class="k">lambda</span> <span class="n">_info</span><span class="p">:</span>
                <span class="n">ExecutionContext</span><span class="o">.</span><span class="n">console_logging</span><span class="p">(</span>
                    <span class="n">log_level</span><span class="o">=</span><span class="n">DEBUG</span><span class="p">,</span>
                    <span class="n">resources</span><span class="o">=</span><span class="n">PartNineResources</span><span class="p">(</span><span class="n">InMemoryStore</span><span class="p">())</span>
                <span class="p">)</span>
        <span class="p">),</span>
        <span class="s1">&#39;cloud&#39;</span><span class="p">:</span> <span class="n">PipelineContextDefinition</span><span class="p">(</span>
            <span class="n">context_fn</span><span class="o">=</span><span class="k">lambda</span> <span class="n">info</span><span class="p">:</span>
                <span class="n">ExecutionContext</span><span class="o">.</span><span class="n">console_logging</span><span class="p">(</span>
                    <span class="n">resources</span><span class="o">=</span><span class="n">PartNineResources</span><span class="p">(</span>
                        <span class="n">PublicCloudStore</span><span class="p">(</span><span class="n">info</span><span class="o">.</span><span class="n">config</span><span class="p">[</span><span class="s1">&#39;credentials&#39;</span><span class="p">],</span>
                    <span class="p">)</span>
                <span class="p">)</span>
            <span class="p">),</span>
            <span class="n">config_field</span><span class="o">=</span><span class="n">types</span><span class="o">.</span><span class="n">Field</span><span class="p">(</span>
                <span class="n">types</span><span class="o">.</span><span class="n">Dict</span><span class="p">({</span>
                    <span class="s1">&#39;credentials&#39;</span><span class="p">:</span> <span class="n">Field</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">Dict</span><span class="p">({</span>
                        <span class="s1">&#39;user&#39;</span> <span class="p">:</span> <span class="n">Field</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">),</span>
                        <span class="s1">&#39;pass&#39;</span> <span class="p">:</span> <span class="n">Field</span><span class="p">(</span><span class="n">types</span><span class="o">.</span><span class="n">String</span><span class="p">),</span>
                    <span class="p">})),</span>
                <span class="p">}),</span>
            <span class="p">),</span>
        <span class="p">)</span>
    <span class="p">}</span>
<span class="p">)</span>
</pre></div>
</div>
<p>Notice the <em>second</em> context definition. It</p>
<ol class="arabic simple">
<li>Accepts configuration, this specifies that in a typed fashion.</li>
<li>Creates a different version of that store, to which it passes configuration.</li>
</ol>
<p>Now when you invoke this pipeline with the following yaml file:</p>
<div class="highlight-yaml notranslate"><div class="highlight"><pre><span></span><span class="nt">context</span><span class="p">:</span>
  <span class="nt">cloud</span><span class="p">:</span>
    <span class="nt">config</span><span class="p">:</span>
      <span class="nt">credentials</span><span class="p">:</span>
        <span class="nt">user</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">some_user</span>
        <span class="nt">pass</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">some_password</span>

<span class="nt">solids</span><span class="p">:</span>
  <span class="nt">ingest_a</span><span class="p">:</span>
    <span class="nt">config</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">2</span>
  <span class="nt">ingest_b</span><span class="p">:</span>
    <span class="nt">config</span><span class="p">:</span> <span class="l l-Scalar l-Scalar-Plain">3</span>
</pre></div>
</div>
<p>It will create the production version of that store. Note that you have
not change the implementation of any solid to do this. Only the configuration
changes.</p>
</div>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h3><a href="../index.html">Table Of Contents</a></h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../principles.html">Principles</a></li>
<li class="toctree-l1"><a class="reference internal" href="../installation.html">Installation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../contributing.html">Contributing</a></li>
</ul>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="hello_world.html">Hello, World</a></li>
<li class="toctree-l1"><a class="reference internal" href="hello_dag.html">Hello, DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="actual_dag.html">An actual DAG</a></li>
<li class="toctree-l1"><a class="reference internal" href="inputs.html">Inputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="config.html">Configuration</a></li>
<li class="toctree-l1"><a class="reference internal" href="execution_context.html">Execution Context</a></li>
<li class="toctree-l1"><a class="reference internal" href="repos.html">Repositories</a></li>
<li class="toctree-l1"><a class="reference internal" href="pipeline_execution.html">Pipeline Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="configuration_schemas.html">Configuration Schemas</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">Custom Contexts</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_ten.html">Expectations</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_eleven.html">Multiple Outputs</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_twelve.html">User-defined Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_thirteen.html">Reusable Solids</a></li>
<li class="toctree-l1"><a class="reference internal" href="part_fourteen.html">Unit-testing Pipelines</a></li>
</ul>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/definitions.html">Definitions</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/decorators.html">Decorators</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/execution.html">Execution</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/errors.html">Errors</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/types.html">Types</a></li>
<li class="toctree-l1"><a class="reference internal" href="../apidocs/utilities.html">Utilities</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="../index.html">Documentation overview</a><ul>
      <li>Previous: <a href="configuration_schemas.html" title="previous chapter">Configuration Schemas</a></li>
      <li>Next: <a href="part_ten.html" title="next chapter">Expectations</a></li>
  </ul></li>
</ul>
</div>
  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="../_sources/intro_tutorial/part_nine.rst.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="../search.html" method="get">
      <input type="text" name="q" />
      <input type="submit" value="Go" />
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
    </div>
</div>
<script type="text/javascript">$(\'#searchbox\').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2018, Elementl, Inc.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.7.5</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.12</a>
      
      |
      <a href="../_sources/intro_tutorial/part_nine.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>'''

snapshots['test_build_all_docs 26'] = '''.. _installation:
Installation
=======================

Dagster is tested on Python 3.6.6, 3.5.6, and 2.7.15. Python 3 is strongly
encouraged -- if you can, you won't regret making the switch!

Installing Python, pip, virtualenv, and yarn
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To check that Python, the pip package manager, and virtualenv (highly
recommended) are already installed, you can run:

.. code-block:: console

    $ python --version
    $ pip --version
    $ virtualenv --version

If these tools aren't present on your system, you can install them as follows:

On Ubuntu:

.. code-block:: console

    $ sudo apt update
    $ sudo apt install python3-dev python3-pip
    $ sudo pip3 install -U virtualenv  # system-wide install

On OSX, using `Homebrew <https://brew.sh/>`_:

.. code-block:: console

    $ brew update
    $ brew install python  # Python 3
    $ sudo pip3 install -U virtualenv  # system-wide install

On Windows (Python 3):
- Install the *Microsoft Visual C++ 2015 Redistributable Update 3*. This
  comes with *Visual Studio 2015* but can be installed separately as follows:
    1. Go to the Visual Studio downloads,
    2. Select *Redistributables and Build Tools*,
    3. Download and install the *Microsoft Visual C++ 2015 Redistributable
       Update 3*.
- Install the 64-bit Python 3 release for Windows (select ``pip`` as an
  optional feature).
- Then run ``pip3 install -U pip virtualenv``

To use the dagit tool, you will also need to
`install yarn <https://yarnpkg.com/lang/en/docs/install/>`_.

Creating a virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
We strongly recommend installing dagster inside a Python virtualenv. If you are
running Anaconda, you should install dagster inside a Conda environment.

To create a virtual environment on Python 3, you can just run:

.. code-block:: console

    $ python3 -m venv /path/to/new/virtual/environment

This will create a new Python environment whose interpreter and libraries
are isolated from those installed in other virtual environments, and
(by default) any libraries installed in a “system” Python installed as part
of your operating system.

On Python 2, you can use a tool like
`virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/>`_
to manage your virtual environments, or just run:

.. code-block:: console

    $ virtualenv /path/to/new/virtual/environment

You'll then need to 'activate' the virtualenvironment, in bash by
running:

.. code-block:: console

    $ source /path/to/new/virtual/environment/bin/activate

(For other shells, see the
`venv documentation <https://docs.python.org/3/library/venv.html#creating-virtual-environments>`_.)

If you are using Anaconda, you can run:

.. code-block:: console

    $ conda create --name myenv

And then, on OSX or Ubuntu:

.. code-block:: console

    $ source activate myenv

Or, on Windows:

.. code-block:: console

    $ activate myenv

Installing the stable version from PyPI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To install dagster and dagit, run:

.. code-block:: console

    $ pip install dagster
    $ pip install dagit

This will install the latest stable version of both packages.

Installing the dev version from source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To install the development version of the software, first clone the project
from Github:

.. code-block:: console

    $ git clone git@github.com:dagster-io/dagster.git

From the root of the repository, you can then run:

.. code-block:: console

    $ pip install -e python_packages/dagster && \\
      pushd python_packages/dagit/webapp && \\
      yarn install && \\
      yarn build && \\
      popd && \\
      pip install -e python_packages/dagit
'''

snapshots['test_build_all_docs 27'] = '''Principles
-----------
Dagster is opinionated about how data pipelines should be built and structured. What do we think
is important?

Functional
^^^^^^^^^^
Data pipelines should be expressed as DAGs (directed acyclic graphs) of functional, idempotent
computations. Individual nodes in the graph consume their inputs, perform some computation, and
yield outputs, either with no side effects or with clealy advertised side effects. Given the
same inputs and configuration, the computation should always produce the same output. If these 
computations have external dependencies, these should be parametrizable, so that the computations
may execute in different environments.

   * See Maxime Beauchemin's Medium article on `Functional Data Engineering <https://bit.ly/2LxDgnr>`_
     for an excellent overview of functional programing in batch computations.

Self-describing
^^^^^^^^^^^^^^^
Data pipelines should be self-describing, with rich metadata and types. Users should be able to
approach an unfamiliar pipeline and use tooling to inspect it and discover its structure,
capabilities, and requirements. Pipeline metadata should be co-located with the pipeline's actual
code: documentation and code should be delivered as a single artifact.

Compute-agnostic
^^^^^^^^^^^^^^^^
Heterogeneity in data pipelines is the norm, rather than the exception. Data pipelines are written
collaboratively by many people in different personas -- data engineers, machine-learning engineers,
data scientists, analysts and so on -- who have different needs and tools, and are particular about
those tools.

Dagster has opinions about best practices for structuring data pipelines. It has no opinions
about what libraries and engines should do actual compute. Dagster pipelines can be made up of
any Python computations, whether they use Pandas, Spark, or call out to SQL or any other DSL or
library deemed appropriate to the task.

Testable
^^^^^^^^
Testing data pipelines is notoriously difficult. Because testing is so difficult, it is often never
done, or done poorly. Dagster pipelines are designed to be tested. Dagster provides explicit support
for pipeline authors to manage and maintain multiple execution environments -- for example, unit
testing, integration testing, and production environments. Dagster can also execute arbitrary
subsets and nodes of pipelines, which is critical for testability (and useful in operational
contexts as well).

Verifiable data quality
^^^^^^^^^^^^^^^^^^^^^^^
Testing code is important in data pipelines, but it is not sufficient. Data quality tests -- run
during every meaningful stage of computation in production -- are critical to reduce the
maintenance burden of data pipelines. Pipeline authors generally do not have control over their
input data, and make many implicit assumptions about that data. Data formats can also change
over time. In order to control this entropy, Dagster encourages users to computationally verify
assumptions (known as expectations) about the data as part of the pipeline process. This way, when
those assumptions break, the breakage can be reported quickly, easily, and with rich metadata
and diagnostic information. These expectations can also serve as contracts between teams.

   * See https://bit.ly/2mxDS1R for a primer on pipeline tests for data quality.

Gradual, optional typing
^^^^^^^^^^^^^^^^^^^^^^^^
Dagster contains a type system to describe the values flowing through the pipeline and the
configuration of the pipeline. As pipelines mature, gradual typing lets nodes in a pipeline
know if they are properly arranged and configured prior to execution, and provides rich
documentation and runtime error checking.
'''

snapshots['test_build_all_docs 28'] = '''Contributing
============

If you are planning to contribute to dagster, you will need to set up a local
development environment.

Local development setup
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Install Python 3.6.
  * You can't use Python 3.7+ yet because of https://github.com/apache/arrow/issues/1125

2. Create and activate a virtualenv
::
    python3 -m venv dagsterenv
    source dagsterenv/bin/activate

3. Install dagster locally and install dev tools
::
    git clone git@github.com:dagster-io/dagster.git
    cd dagster/python_modules
    pip install -e ./dagit
    pip install -e ./dagster
    pip install -r ./dagster/dev-requirements.txt

4. Install dagit webapp dependencies
::
    cd dagster/python_modules/dagit/dagit/webapp
    yarn install

5. Run tests
We use tox to manage test environments for python.
::
    cd dagster/python_modules/dagster
    tox
    cd dagster/python_modules/dagit
    tox

To run JavaScript tests for the dagit frontend, you can run:
::
    cd dagster/python_modules/dagit/dagit/webapp
    yarn test

In webapp development it's handy to run `yarn run jest --watch` to have an
interactive test runner.

Some webapp tests use snapshots--auto-generated results to which the test
render tree is compared. Those tests are supposed to break when you change
something.

Check that the change is sensible and run `yarn run jest -u` to update the
snapshot to the new result. You can also update snapshots interactively
when you are in `--watch` mode.

Running dagit webapp in development
-------------------------------------
For development, run the dagit GraphQL server on a different port than the
webapp, from any directory that contains a repository.yml file. For example:
::
    cd dagster/python_modules/dagster/dagster/dagster_examples
    dagit -p 3333

Run the local development (autoreloading, etc.) version of the webapp.
::
    cd dagster/python_modules/dagit/dagit/webapp
    REACT_APP_GRAPHQL_URI="http://localhost:3333/graphql" yarn start

Releasing
-----------
Projects are released using the Python script at `dagster/bin/publish.py`.

Developing docs
---------------
Running a live html version of the docs can expedite documentation development.
::
    cd python_modules/dagster/docs
    make livehtml
'''

snapshots['test_build_all_docs 29'] = '''.. image:: https://user-images.githubusercontent.com/28738937/44878798-b6e17e00-ac5c-11e8-8d25-2e47e5a53418.png
   :align: center


Welcome to Dagster, an opinionated programming model for data pipelines.

.. toctree::
  :maxdepth: 1
  :name: Documentation

  principles
  installation
  contributing

Intro Tutorial
==============
.. toctree::
  :maxdepth: 1
  :name: Intro Tutorial

  intro_tutorial/hello_world
  intro_tutorial/hello_dag
  intro_tutorial/actual_dag
  intro_tutorial/inputs
  intro_tutorial/config
  intro_tutorial/execution_context
  intro_tutorial/repos
  intro_tutorial/pipeline_execution
  intro_tutorial/configuration_schemas
  intro_tutorial/part_nine
  intro_tutorial/part_ten
  intro_tutorial/part_eleven
  intro_tutorial/part_twelve
  intro_tutorial/part_thirteen
  intro_tutorial/part_fourteen


API Reference
================

.. toctree::
  :maxdepth: 1
  :name: API Reference

  apidocs/definitions
  apidocs/decorators
  apidocs/execution
  apidocs/errors
  apidocs/types
  apidocs/utilities

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
'''

snapshots['test_build_all_docs 30'] = '''Multiple Outputs
----------------

So far all of the examples have been solids that have a single output. However
solids support an arbitrary number of outputs. This allows for downstream
solids to only tie their dependency to a single output. Additionally -- by
allowing for multiple outputs to conditionally fire -- this also ends up
supporting dynamic branching and conditional execution of pipelines.


.. code-block:: python

    @solid(
        outputs=[
            OutputDefinition(runtime_type=types.Int, name='out_one'),
            OutputDefinition(runtime_type=types.Int, name='out_two'),
        ],
    )
    def return_dict_results(_info):
        return MultipleResults.from_dict({
            'out_one': 23,
            'out_two': 45,
        })

    @solid(inputs=[InputDefinition('num', runtime_type=types.Int)])
    def log_num(info, num):
        info.context.info('num {num}'.format(num=num))
        return num

    @solid(inputs=[InputDefinition('num', runtime_type=types.Int)])
    def log_num_squared(info, num):
        info.context.info(
            'num_squared {num_squared}'.format(num_squared=num * num)
        )
        return num * num

Notice how ``return_dict_results`` has two outputs. For the first time
we have provided the name argument to an :py:class:`OutputDefinition`. (It
defaults to ``'result'``, as it does in a :py:class:`DependencyDefinition`)
These names must be unique and results returns by a solid transform function
must be named one of these inputs. (In all previous examples the value returned
by the transform had been implicitly wrapped in a :py:class:`Result` object
with the name ``'result'``.)

So from ``return_dict_results`` we used :py:class:`MultipleResults` to return
all outputs from this transform.

Next let's examine the :py:class:`PipelineDefinition`:

.. code-block:: python

    def define_part_eleven_step_one():
        return PipelineDefinition(
            name='part_eleven_step_one',
            solids=[return_dict_results, log_num, log_num_squared],
            dependencies={
                'log_num': {
                    'num': DependencyDefinition(
                        'return_dict_results',
                        'out_one',
                    ),
                },
                'log_num_squared': {
                    'num': DependencyDefinition(
                        'return_dict_results',
                        'out_two',
                    ),
                },
            },
        )

Just like this tutorial is the first example of an :py:class:`OutputDefinition` with
a name, this is also the first time that a :py:class:`DependencyDefinition` has
specified name, because dependencies point to a particular **output** of a solid,
rather than to the solid itself. In previous examples the name of output has
defaulted to ``'result'``.

With this we can run the pipeline:

.. code-block:: sh

    python step_eleven.py
    ... log spew
    2018-11-08 10:52:06 - dagster - INFO - orig_message="Solid return_dict_results emittedoutput \\"out_one\\" value 23" log_message_id="7d62dcbf-583d-4640-941f-48cda39e79a1" run_id="9de556c1-7f4d-4702-95af-6d6dbe6b296b" pipeline="part_eleven_step_one" solid="return_dict_results" solid_definition="return_dict_results"
    2018-11-08 10:52:06 - dagster - INFO - orig_message="Solid return_dict_results emittedoutput \\"out_two\\" value 45" log_message_id="cc2ae784-6861-49ef-a463-9cbe4fa0f5e6" run_id="9de556c1-7f4d-4702-95af-6d6dbe6b296b" pipeline="part_eleven_step_one" solid="return_dict_results" solid_definition="return_dict_results"
    ... more log spew

The :py:class:`MultipleResults` class is not the only way to return multiple
results from a solid transform function. You can also yield multiple instances
of the `Result` object. (Note: this is actually the core specification
of the transform function: all other forms are implemented in terms of
the iterator form.)

.. code-block:: python

    @solid(
        outputs=[
            OutputDefinition(runtime_type=types.Int, name='out_one'),
            OutputDefinition(runtime_type=types.Int, name='out_two'),
        ],
    )
    def yield_outputs(_info):
        yield Result(23, 'out_one')
        yield Result(45, 'out_two')

    def define_part_eleven_step_two():
        return PipelineDefinition(
            name='part_eleven_step_two',
            solids=[yield_outputs, log_num, log_num_squared],
            dependencies={
                'log_num': {
                    'num': DependencyDefinition('yield_outputs', 'out_one')
                },
                'log_num_squared': {
                    'num': DependencyDefinition('yield_outputs', 'out_two')
                },
            },
        )

    if __name__ == '__main__':
        execute_pipeline(define_part_eleven_step_two())

... and you'll see the same log spew around outputs in this version:

.. code-block:: sh
    $ python part_eleven.py
    2018-11-08 10:54:15 - dagster - INFO - orig_message="Solid yield_outputs emitted output \\"out_one\\" value 23" log_message_id="5e1cc181-b74d-47f8-8d32-bc262d555b73" run_id="4bee891c-e04f-4221-be77-17576abb9da2" pipeline="part_eleven_step_two" solid="yield_outputs" solid_definition="yield_outputs"
    2018-11-08 10:54:15 - dagster - INFO - orig_message="Solid yield_outputs emitted output \\"out_two\\" value 45" log_message_id="8da32946-596d-4783-b7c5-4edbb3a1dbc2" run_id="4bee891c-e04f-4221-be77-17576abb9da2" pipeline="part_eleven_step_two" solid="yield_outputs" solid_definition="yield_outputs"

Conditional Outputs
^^^^^^^^^^^^^^^^^^^

Multiple outputs are the mechanism by which we implement branching or conditional execution.

Let's modify the first solid above to conditionally emit one output or the other based on config
and then execute that pipeline.

.. code-block:: python

    @solid(
        config_field=ConfigDefinition(types.String, description='Should be either out_one or out_two'),
        outputs=[
            OutputDefinition(runtime_type=types.Int, name='out_one'),
            OutputDefinition(runtime_type=types.Int, name='out_two'),
        ],
    )
    def conditional(info):
        if info.config == 'out_one':
            yield Result(23, 'out_one')
        elif info.config == 'out_two':
            yield Result(45, 'out_two')
        else:
            raise Exception('invalid config')


    def define_part_eleven_step_three():
        return PipelineDefinition(
            name='part_eleven_step_three',
            solids=[conditional, log_num, log_num_squared],
            dependencies={
                'log_num': {
                    'num': DependencyDefinition('conditional', 'out_one')
                },
                'log_num_squared': {
                    'num': DependencyDefinition('conditional', 'out_two')
                },
            },
        )

    if __name__ == '__main__':
        execute_pipeline(
            define_part_eleven_step_three(),
            {
                'solids': {
                    'conditional': {
                        'config': 'out_two'
                    },
                },
            },
        ) 

Note that we are configuring this solid to *only* emit out_two which will end up
only triggering log_num_squared. log_num will never be executed.

.. code-block:: sh

    $ python part_eleven.py
    ... log spew
    2018-09-16 18:58:32 - dagster - INFO - orig_message="Solid conditional emitted output \\"out_two\\" value 45" log_message_id="f6fd78c5-c25e-40ea-95ef-6b80d12155de" pipeline="part_eleven_step_three" solid="conditional"
    2018-09-16 18:58:32 - dagster - INFO - orig_message="Solid conditional did not fire outputs {\'out_one\'}" log_message_id="d548ea66-cb10-42b8-b150-aed8162cc25c" pipeline="part_eleven_step_three" solid="conditional"    
    ... log spew
'''

snapshots['test_build_all_docs 31'] = '''Configuration
-------------
For maximum flexibility, testability, and reusability, we want to avoid hardcoding solids'
(or pipelines') dependencies on the external world.

We should be able to run the same code in different environments for test, in development, and in
production, and to parametrize our solids' interactions with the different facilities afforded by
each of those environments.

Then, we can declaratively specify features of our environment without having to rewrite our code.

Conceptually, where **inputs** are inputs to the computation done by a single solid, and might be
linked by a dependency definition to **outputs** of a previous computation in a DAG,
**configuration** should be used to specify *how* a computation executes.

We'll illustrate this by configuring our hello world example to speak a couple of different
languages.

This time, we'll use a more fully-featured API to define our solid -- 
:py:func:`@solid <dagster.solid>` instead of :py:func:`@lambda_solid <dagster.lambda_solid>`.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/config.py
   :linenos:
   :caption: config.py

We will be exploring the :py:func:`@solid <dagster.solid>` API in much more detail as this tutorial
proceeds. For now, the only salient difference is that the annotated function takes an additional
first parameter, ``info``, which is of type
:py:class:`TransformExecutionInfo <dagster.TransformExecutionInfo>`. The property ``info.config``
is the configuration passed into each individual solid.

That configuration is specified in the second argument to
:py:func:`execute_pipeline <dagster.execute_pipeline>`, which must be a dict. This dict specifies
*all* of the configuration to execute an entire pipeline. It may have many sections, but we're only
using one of them here: per-solid configuration specified under the key ``solids``:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/config.py
   :lines: 31
   :dedent: 8

The ``solids`` dict is keyed by solid name, and each of its values in turn defines a ``config``
key corresponding to the user-defined configuration schema for each particular solid. In this case,
that's a single scalar string value.

Run this from the command line utility. In order to do this you must provide
a yaml config file:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/config_env.yml
   :linenos:
   :caption: config_env.yml

Now you can run this pipeline with this config file like so:

.. code-block:: console

   $ dagster pipeline execute -f config.py \\
   -n define_configurable_hello_pipeline -e config_env.yml

To run this example from dagit, use the following command:

.. code-block:: console

   $ dagit -f config.py -n define_configurable_hello_pipeline

Just as with configurable inputs, you can edit the configuration on the fly in dagit's built-in
config editor. Try switching languages and rerunning the pipeline!

.. image:: config_figure_one.png

Next, we'll learn about another part of the ``info`` parameter, the
:doc:`Execution Context <execution_context>`, which we'll use to parametrize features of the pipeline
execution environment that are common to many solids.
'''

snapshots['test_build_all_docs 32'] = '''Execution Context
-----------------
We use **configuration** to set parameters on a per-solid basis. The **execution context** lets
us set parameters for the entire pipeline.

The execution context is exposed to individual solids as the ``context`` property of the ``info``
object. The context is an object of type :py:class:`ExecutionContext <dagster.ExecutionContext>`.
For every execution of a particular pipeline, one instance of this context is created, no matter how
many solids are involved. Runtime state or information that is particular to a single execution,
rather than particular to an individual solid, should be associated with the context.

One of the most basic pipeline-level facilities is logging.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/execution_context.py
   :lines: 1-16
   :caption: execution_context.py

If you run this either on the command line or in dagit, you'll see our new error message pop up
in the logs.

.. code-block:: console

    $ dagster pipeline execute -f execution_context.py -n define_execution_context_pipeline_step_one
    ...
    2018-12-17 16:06:53 - dagster - ERROR - orig_message="An error occurred." log_message_id="89211a12-4f75-4aa0-a1d6-786032641986" run_id="40a9b608-c98f-4200-9f4a-aab70a2cb603" pipeline="<<unnamed>>" solid="solid_two" solid_definition="solid_two"
    ...

Notice that even though the user only logged the message "An error occurred", by routing logging
through the context we are able to provide richer error information -- including the name of the
solid and a timestamp -- in a semi-structured format.

(Note that the order of execution of these two solids is indeterminate -- they don't depend on each
other.)

Let's change the example by adding a name to the pipeline. (Naming things is good practice).

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/execution_context.py
   :lines: 19-22
   :caption: execution_context.py

And then run it:

.. code-block:: console

    $ dagster pipeline execute -f execution_context.py -n define_execution_context_pipeline_step_two
    ...
    2018-12-17 16:06:53 - dagster - ERROR - orig_message="An error occurred." log_message_id="89211a12-4f75-4aa0-a1d6-786032641986" run_id="40a9b608-c98f-4200-9f4a-aab70a2cb603" pipeline="execution_context_pipeline" solid="solid_two" solid_definition="solid_two"
    ...

You'll note that the metadata in the log message now includes the pipeline name,
``execution_context_pipeline``, where before it was ``<<unnamed>>``.

But what about the ``DEBUG`` message in ``solid_one``? The default context provided by dagster
logs error messages to the console only at the ``INFO`` level or above. (In dagit, you can always
filter error messages at any level.) In order to print ``DEBUG`` messages to the console, we'll
use the configuration system again -- this time, to configure the context rather than an individual
solid.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/execution_context.py
   :lines: 25-28
   :caption: execution_context.py

We can use the same config syntax as we've seen before in order to configure the pipeline:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/execution_context.py
   :lines: 32-35
   :dedent: 4

But in generally, we'll prefer to use a yaml file to declaratively specify our config.

Separating config into external files is a nice pattern because it allows users who might not be
comfortable in a general-purpose programming environment like Python to do meaningful work
configuring pipelines in a restricted DSL.

Fragments of config expressed in yaml can also be reused (for instance, pipeline-level config that
is common across many projects) or kept out of source control (for instance, credentials or
information specific to a developer environment) and combined at pipeline execution time.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/execution_context.yml
   :caption: execution_context.yml

If we re-run the pipeline, you'll see a lot more output, now including our custom ``DEBUG`` message.

.. code-block:: console

    $ dagster pipeline execute -f execution_context.py \\
    -n define_execution_context_pipeline_step_three -e execution_context.yaml
    ...
    2018-12-17 17:18:06 - dagster - DEBUG - orig_message="A debug message." log_message_id="497c9d47-571a-44f6-a04c-8f24049b0f66" run_id="5b233906-9b36-4f15-a220-a850a1643b9f" pipeline="execution_context_pipeline" solid="solid_one" solid_definition="solid_one"
    ...

Although logging is a universally useful case for the execution context, this example only touches
on the capabilities of the context. Any pipeline-level facilities that pipeline authors might want
to make configurable for different environments -- for instance, access to file systems, databases,
or compute substrates -- can be configured using the context.

This is how pipelines can be made executable in different operating environments (e.g. unit-testing,
CI/CD, prod, etc) without changing business logic.

Next, we'll see how to declare :doc:`Repositories <repos>`, which let us group pipelines together
so that the dagster tools can manage them.
'''

snapshots['test_build_all_docs 33'] = '''Inputs
------
So far we have only demonstrated pipelines whose solids yield hardcoded values and then flow them
through the pipeline. In order to be useful a pipeline must also interact with its external
environment.

Let's return to our hello world example. But this time, we'll make the string
the solid returns be parameterized based on inputs.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/inputs.py
   :lines: 1-38
   :linenos:
   :caption: inputs.py

Note that the input ``word`` to solid ``add_hello_to_word`` has no dependency specified. This
means that the operator of the pipeline must specify the input at pipeline execution
time.

Recall that there are three primary ways to execute a pipeline: using the python API, from 
the command line, and from dagit. We'll go through each of these and see how to specify the input
in each case.

Python API
~~~~~~~~~~
In the Python API, pipeline configuration is specified in the second argument to
:py:func:`execute_pipeline <dagster.execute_pipeline>`, which must be a dict. This dict contains
*all* of the configuration to execute an entire pipeline. It may have many sections, but we'll only
use one of them here: per-solid configuration specified under the key ``solids``:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/inputs.py
   :lines: 25,27,29-31
   :dedent: 8 

The ``solids`` dict is keyed by solid name, and each solid is configured by a dict that may have
several sections of its own. In this case we are only interested in the ``inputs`` section, so
that we can specify that value of the input ``word``.

The function ``execute_with_another_world`` demonstrates how one would invoke this pipeline
using the python API:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/inputs.py
   :lines: 20-22,25,27,29-32

CLI
~~~

Next let's use the CLI. In order to do that we'll need to provide the environment
information via a config file. We'll use the same values as before, but in the form
of YAML rather than python dictionaries:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/inputs_env.yml
   :linenos:
   :caption: inputs_env.yml

And now specify that config file via the ``-e`` flag.

.. code-block:: console

    $ dagster pipeline execute -f inputs.py \\
    -n define_hello_inputs_pipeline -e inputs_env.yml 

Dagit
~~~~~

As always, you can load the pipeline and execute it within dagit.

.. code-block:: console

   $ dagit -f inputs.py -n define_hello_inputs_pipeline
   Serving on http://127.0.0.1:3000

From the execute console, you can enter your config directly like so:

.. image:: inputs_figure_one.png

You'll notice that the config editor is auto-completing. Because it knows the structure
of the config, the editor can provide rich error information. We can improve the experience of
using the editor by appropriately typing the inputs, making everything less error-prone.

Typing
^^^^^^

Right now the inputs and outputs of this solid are totally untyped. (Any input or output
without a type is automatically assigned the ``Any`` type.) This means that mistakes
are often not surfaced until the pipeline is executed.

For example, imagine if our environment for our pipeline was:

.. code-block:: YAML

    solids:
        add_hello_to_word:
            inputs:
                word: 2343

If we execute this pipeline with this config, it'll fail at runtime.

Enter this config in dagit and execute and you'll see the transform fail:

.. image:: inputs_figure_two_untyped_execution.png

Click on the red dot on the execution step that failed and a detailed stacktrace will pop up.

.. image:: inputs_figure_three_error_modal.png

It would be better if we could catch this error earlier, when we specify the config. So let's
make the inputs typed.

A user can apply types to inputs and outputs. In this case we just want to type them as the
built-in ``String``.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/inputs.py
   :lines: 35-40
   :emphasize-lines: 36-37
   :caption: inputs.py

By using typed input instead we can catch this error prior to execution.

.. image:: inputs_figure_four_error_prechecked.png

We've seen how to connect solid inputs and outputs to specify dependencies and the structure of
our DAG, as well as how to provide inputs at runtime through config. Next, we'll see how we can
use :doc:`Configuration <config>` to further parametrize our solids' interactions with the
outside world.
'''

snapshots['test_build_all_docs 34'] = '''Pipeline Execution
------------------
Just as in the last part of the tutorial, we'll define a pipeline and a repository, and create
a yaml file to tell the CLI tool about the repository.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/pipeline_execution.py
   :linenos:
   :caption: pipeline_execution.py

And now the repository file:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/pipeline_execution_repository.yml
   :linenos:
   :caption: repository.yml

Finally, we'll need to define the pipeline config in a yaml file in order to
execute our pipeline from the command line.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/pipeline_execution_env.yml
   :linenos:
   :caption: env.yml

With these elements in place we can now drive execution from the CLI specifying only the pipeline
name. The tool loads the repository using the `repository.yml` file and looks up the pipeline by
name.

.. code-block:: console

    $ dagster pipeline execute part_seven -e env.yml

Suppose that we want to keep some settings (like our context-level logging config) constant across
a bunch of our pipeline executions, and vary only pipeline-specific settings. It'd be tedious to
copy the broadly-applicable settings into each of our config yamls, and error-prone to try to keep
those copies in sync. So the command line tools allow us to specify more than one yaml file to use
for config.

Let's split up our env.yml into two parts:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/pipeline_execution_env.yml
   :lines: 1-4
   :caption: constant_env.yml

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/pipeline_execution_env.yml
   :lines: 6-9
   :caption: specific_env.yml

Now we can run our pipeline as follows:

.. code-block:: console

    $ dagster pipeline execute part_seven -e constant_env.yml -e specific_env.yml

Order matters when specifying yaml files to use -- values specified in later files will override
values in earlier files, which can be useful. You can also use globs in the CLI arguments to consume
multiple yaml files.

Next, we'll look at defining strongly-typed :doc:`Configuration Schemas <configuration_schemas>`
to guard against bugs and enrich pipeline documentation.
'''

snapshots['test_build_all_docs 35'] = '''User-defined Types
------------------

So far we have only used the built-in types the come with dagster to describe
data flowing between different solids. However this only gets one so far, and
is typically only useful for toy pipelines. You are going to want to define
our own custom types to describe your pipeline- and runtime-specific data
structures.

For the first example, we'll show how to flow a plain python object
through the a pipeline and then describe that object in the type system.
Let's say we wanted to flow a tuple through a pipeline.

.. code-block:: python

    StringTuple = namedtuple('StringTuple', 'str_one str_two')

    @lambda_solid
    def produce_valid_value():
        return StringTuple(str_one='value_one', str_two='value_two')


And then we want to consume it. However, we want this to be type-checked
and metadata to be surfaced in tools like dagit.

To do this we'll introduce a dagster type.

.. code-block:: python

    StringTupleType = types.PythonObjectType(
        'StringTuple',
        python_type=StringTuple,
        description='A tuple of strings.',
    )

And then annotate relevant functions with it.

.. code-block:: python

    @lambda_solid(output=OutputDefinition(StringTupleType))
    def produce_valid_value():
        return StringTuple(str_one='value_one', str_two='value_two')

    @solid(inputs=[InputDefinition('string_tuple', StringTupleType)])
    def consume_string_tuple(info, string_tuple):
        info.context.info(
            'Logging value {string_tuple}'.format(
                string_tuple=string_tuple
            )
        )

    def define_part_twelve_step_one():
        return PipelineDefinition(
            name='part_twelve_step_one',
            solids=[produce_valid_value, consume_string_tuple],
            dependencies={
                'consume_string_tuple': {
                    'string_tuple': 
                    DependencyDefinition('produce_valid_value')
                }
            },
        )

    if __name__ == '__main__':
        execute_pipeline(define_part_twelve_step_one())

.. code-block:: sh

    $ python part_twelve.py
    ... log spew
    2018-09-17 06:55:06 - dagster - INFO - orig_message="Logging value StringTuple(str_one=\'value_one\', str_two=\'value_two\')" log_message_id="675f905d-c1f4-4539-af26-c28d23a757be" pipeline="part_twelve_step_one" solid="consume_string_tuple"
    ...

Now what if things go wrong? Imagine you made an error and wired up `consume_string_tuple`
to a solid

.. code-block:: python

    @lambda_solid
    def produce_invalid_value():
        return 'not_a_tuple'

    def define_part_twelve_step_two():
        return PipelineDefinition(
            name='part_twelve_step_two',
            solids=[produce_invalid_value, consume_string_tuple],
            dependencies={
                'consume_string_tuple': {
                    'string_tuple':
                    DependencyDefinition('produce_invalid_value')
                }
            },
        )

    if __name__ == '__main__':
        execute_pipeline(define_part_twelve_step_two())

If you run this you'll get some helpful error messages

.. code-block:: sh

    $ python part_twelve.py
    ... log spew
    2018-11-08 11:03:03 - dagster - ERROR - orig_message="Solid consume_string_tuple input string_tuple received value not_a_tuple which does not pass the typecheck for Dagster type StringTuple. Compute node consume_string_tuple.transform" log_message_id="0db53fdb-183c-477c-aff9-2ee26bc76636" run_id="424047dd-e835-4016-b757-18adec0afdfc" pipeline="part_twelve_step_two"    ... stack trace
    dagster.core.errors.DagsterEvaluateValueError: Expected valid value for StringTuple but got 'not_a_tuple'
    ... more stack trace
    dagster.core.errors.DagsterTypeError: Solid consume_string_tuple input string_tuple received value not_a_tuple which does not pass the typecheck for Dagster type StringTuple. Compute node consume_string_tuple.transform

Custom Types
^^^^^^^^^^^^

The type system is very flexible, and values can by both type-checked and coerced by user-defined code.

Imagine we wants to be able process social security numbers and ensure that they are well-formed
throughout the whole pipeline.

In order to do this we'll define a type.

.. code-block:: python

    class SSNString(str):
        pass

    class SSNStringTypeClass(types.DagsterType):
        def __init__(self):
            super(SSNStringTypeClass, self).__init__(name='SSNString')

        def coerce_runtime_value(self, value):
            if isinstance(value, SSNString):
                return value

            if not isinstance(value, str):
                raise DagsterEvaluateValueError(
                    '{value} is not a string. SSNStringType typecheck failed'.format(value=repr(value))
                )

            if not re.match(r'^(\\d\\d\\d)-(\\d\\d)-(\\d\\d\\d\\d)$', value):
                raise DagsterEvaluateValueError(
                    '{value} did not match SSN regex'.format(value=repr(value))
                )

            return SSNString(value)


    SSNStringType = SSNStringTypeClass()

This type does a couple things. One is that ensures that any string that gets passed to
evaluate_value matches a strict regular expression. You'll also notice that it coerces
that incoming string type to a type called `SSNString`. This type just trivially inherits
from ``str``, but it signifies that the typecheck has already occured. That means if 
evaluate_value is called again, the bulk of the typecheck can be short-circuited, saving
repeated processing through the pipeline. (Note: this is slightly silly because the amount
of computation here is trivial, but one can imagine types that require significant
amounts of computation to verify). 


.. code-block:: python

    @lambda_solid
    def produce_valid_ssn_string():
        return '394-30-2032'

    @solid(inputs=[InputDefinition('ssn', SSNStringType)])
    def consume_ssn(info, ssn):
        if not isinstance(ssn, SSNString):
            raise Exception('This should never be thrown')
        info.context.info('ssn: {ssn}'.format(ssn=ssn))

    def define_part_twelve_step_three():
        return PipelineDefinition(
            name='part_twelve_step_three',
            solids=[produce_valid_ssn_string, consume_ssn],
            dependencies={
                'consume_ssn': {
                    'ssn':
                    DependencyDefinition('produce_valid_ssn_string')
                }
            },
        )

    if __name__ == '__main__':
        execute_pipeline(define_part_twelve_step_three())

You'll note that the exception in ``consume_ssn`` was not thrown, meaning that the
str was coerced to an SSNString by the dagster type.

Future Directions
^^^^^^^^^^^^^^^^^

1. Up-front type checking
2. Serializations
3. Hashing'''

snapshots['test_build_all_docs 36'] = '''Custom Contexts
---------------

So far we have used contexts for configuring logging level only. This barely scratched the surface
of its capabilities.

Testing data pipelines, for a number of reasons, is notoriously difficult. One of the reasons is
that as one moves a data pipeline from local development, to unit testing, to integration testing, to CI/CD,
to production, or to whatever environment you need to operate in, the operating environment can
change dramatically.

In order to handle this, whenever the business logic of a pipeline is interacting with external resources
or dealing with pipeline-wide state generally, the dagster user is expected to interact with these resources
and that state via the context object. Examples would include database connections, connections to cloud services,
interactions with scratch directories on your local filesystem, and so on.

Let's imagine a scenario where we want to record some custom state in a key-value store for our execution runs.
A production time, this key-value store is a live store (e.g. DynamoDB in amazon) but we do not want to interact
this store for unit-testing. Contexts will be our tool to accomplish this goal.

We're going to have a simple pipeline that does some rudimentary arithmetic, but that wants to record
the result of its computations in that key value store.

Let's first set up a simple pipeline. We ingest two numbers (each in their own trivial solid)
and then two downstream solids add and multiple those numbers, respectively.

.. code-block:: python

    @solid(
        config_field=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def ingest_a(info):
        return info.config


    @solid(
        config_field=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def ingest_b(info):
        return info.config


    @solid(
        inputs=[InputDefinition('num_one', types.Int),
                InputDefinition('num_two', types.Int)],
        outputs=[OutputDefinition(types.Int)],
    )
    def add_ints(_info, num_one, num_two):
        return num_one + num_two


    @solid(
        inputs=[InputDefinition('num_one', types.Int),
                InputDefinition('num_two', types.Int)],
        outputs=[OutputDefinition(types.Int)],
    )
    def mult_ints(_info, num_one, num_two):
        return num_one * num_two
        

    def define_part_nine_step_one():
        return PipelineDefinition(
            name='part_nine',
            solids=[ingest_a, ingest_b, add_ints, mult_ints],
            dependencies={
                'add_ints': {
                    'num_one': DependencyDefinition('ingest_a'),
                    'num_two': DependencyDefinition('ingest_b'),
                },
                'mult_ints': {
                    'num_one': DependencyDefinition('ingest_a'),
                    'num_two': DependencyDefinition('ingest_b'),
                },
            },
        )

Now we configure execution using a env.yml file:

.. code-block:: yaml

    context:
    default:
        config:
        log_level: DEBUG

    solids:
    ingest_a:
        config: 2
    ingest_b: 
        config: 3

And you should see some log spew indicating execution.

Now imagine we want to log some of the values passing through these solids
into some sort of key value store in cloud storage.

Let's say we have a module called ``cloud`` that allows for interaction
with this key value store. You have to create an instance of a ``PublicCloudConn``
class and then pass that to a function ``set_value_in_cloud_store`` to interact
with the service.

.. code-block:: python

    from cloud import (PublicCloudConn, set_value_in_cloud_store)

    # imagine implementations such as the following
    # class PublicCloudConn:
    #     def __init__(self, creds):
    #         self.creds = creds


    # def set_value_in_cloud_store(_conn, _key, _value):
    #     # imagine this doing something
    #     pass

    conn = PublicCloudConn({'user': some_user', 'pass' : 'some_pwd'})
    set_value_in_cloud_store(conn, 'some_key', 'some_value')


Naively let's add this to one of our transforms:

.. code-block:: python

    @solid(
        config_field=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def ingest_a(info):
        conn = PublicCloudConn('some_user', 'some_pwd')
        set_value_in_cloud_store(conn, 'a', info.config)
        return info.config 

As coded above this is a bad idea on any number of dimensions. Foe one, the username/password
combo is hard coded. We could pass it in as a configuration of the solid. However that
is only in scope for that particular solid. So now the configuration would be passed into
each and every solid that needs it. This sucks. The connection would have to be created within
every solid. Either you would have to implement your own connection pooling or take the hit
of a new connection per solid. This also sucks.

More subtlely, what was previously a nice, isolated, testable piece of software is now hard-coded
to interact with some externalized resource and requires an internet connection, access to
a cloud service, and that could intermittently fail, and that would be slow relative to pure
in-memory compute. This code is no longer testable in any sort of reliable way.

This is where the concept of the context shines. What we want to do is attach an object to the
context object -- which a single instance of is flowed through the entire execution -- that
provides an interface to that cloud store that caches that connection and also provides a
swappable implementation of that store for test isolation. We want code that ends up looking like
this:

.. code-block:: python

    @solid(
        config_field=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def ingest_a(info):
        # The store should be an interface to the cloud store 
        # We will explain the ``resources`` property later.
        info.context.resources.store.record_value(info.context, 'a', info.config)
        return info.config 

The user will be able have complete control the creation of the ``store`` object attached to
the ``resources`` object, which allows a pipeline designer to insert seams of testability.

This ends up accomplishing our goal of being able to test this pipeline in multiple environments
with *zero changes to the core business logic.* The only thing that will vary between environments
is configuration and the context generated because of that configuration.

We need this store object, and two implementations of it. One that talks to the public cloud
service, and one that is an in-memory implementation of this.

.. code-block:: python

    class PublicCloudStore:
        def __init__(self, credentials):
            self.conn = PublicCloudConn(credentials)

        def record_value(self, context, key, value):
            context.info('Setting key={key} value={value} in cloud'
                .format(
                    key=key,
                    value=value,
                )
            )
            set_value_in_cloud_store(self.conn, key, value)


    class InMemoryStore:
        def __init__(self):
            self.values = {}

        def record_value(self, context, key, value):
            context.info('Setting key={key} value={value} in memory'.
                format(
                    key=key,
                    value=value,
                )
            )
            self.values[key] = value


Now we need to create one of these stores and put them into the context. The pipeline author must
create a :py:class:`PipelineContextDefinition`.

It two primary attributes:

1) A configuration definition that allows the pipeline author to define what configuration
is needed to create the ExecutionContext.
2) A function that returns an instance of an ExecutionContext. This context is flowed through
the entire execution.

First let's create the context suitable for local testing:

.. code-block:: python

    PartNineResources = namedtuple('PartNineResources', 'store')

    PipelineContextDefinition(
        context_fn=lambda _info:
            ExecutionContext.console_logging(
                log_level=DEBUG,
                resources=PartNineResources(InMemoryStore())
            )
    )

This context requires *no* configuration so it is not specified. We then 
provide a lambda which creates an ExecutionContext. You'll notice that we pass
in a log_level and a "resources" object. The resources object can be any
python object. What is demonstrated above is a convention. The resources
object that the user creates will be passed through the execution.

So if we return to the implementation of the solids that includes the interaction
with the key-value store, you can see how this will invoke the in-memory store object
which is attached the resources property of the context.

.. code-block:: python

    @solid(
        config_field=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def ingest_a(info):
        info.context.resources.store.record_value(info.context, 'a', info.config)
        return conf

    @solid(
        config_field=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def ingest_b(info):
        info.context.resources.store.record_value(info.context, 'b', info.config)
        return conf


    @solid(
        inputs=[InputDefinition('num_one', types.Int),
                InputDefinition('num_two', types.Int)],
        outputs=[OutputDefinition(types.Int)],
    )
    def add_ints(info, num_one, num_two):
        result = num_one + num_two
        info.context.resources.store.record_value(info.context, 'add', result)
        return result


    @solid(
        inputs=[InputDefinition('num_one', types.Int),
                InputDefinition('num_two', types.Int)],
        outputs=[OutputDefinition(types.Int)],
    )
    def mult_ints(info, num_one, num_two):
        result = num_one * num_two
        info.context.resources.store.record_value(info.context, 'mult', result)
        return result

Now we need to declare the pipeline to use this PipelineContextDefinition. 
We do so with the following:

.. code-block:: python

    return PipelineDefinition(
        name='part_nine',
        solids=[ingest_a, ingest_b, add_ints, mult_ints],
        dependencies={
            'add_ints': {
                'num_one': DependencyDefinition('ingest_a'),
                'num_two': DependencyDefinition('ingest_b'),
            },
            'mult_ints': {
                'num_one': DependencyDefinition('ingest_a'),
                'num_two': DependencyDefinition('ingest_b'),
            },
        },
        context_definitions={
            'local': PipelineContextDefinition(
                context_fn=lambda _info:
                    ExecutionContext.console_logging(
                        log_level=DEBUG,
                        resources=PartNineResources(InMemoryStore())
                    ),
                )
            ),
        }
    )

You\'ll notice that we have "named" the context local. Now when we invoke that context,
we config it with that name.

.. code-block:: yaml

    context:
        local:

    solids:
        ingest_a:
            config: 2
        ingest_b:
            config: 3

Now run the pipeline and you should see logging indicating the execution is occuring.

Now let us add a different context definition that substitutes in the production
version of that store.

.. code-block:: python

    PipelineDefinition(
        name='part_nine',
        solids=[ingest_a, ingest_b, add_ints, mult_ints],
        dependencies={
            'add_ints': {
                'num_one': DependencyDefinition('ingest_a'),
                'num_two': DependencyDefinition('ingest_b'),
            },
            'mult_ints': {
                'num_one': DependencyDefinition('ingest_a'),
                'num_two': DependencyDefinition('ingest_b'),
            },
        },
        context_definitions={
            'local': PipelineContextDefinition(
                context_fn=lambda _info:
                    ExecutionContext.console_logging(
                        log_level=DEBUG,
                        resources=PartNineResources(InMemoryStore())
                    )
            ),
            'cloud': PipelineContextDefinition(
                context_fn=lambda info:
                    ExecutionContext.console_logging(
                        resources=PartNineResources(
                            PublicCloudStore(info.config['credentials'],
                        )
                    )
                ),
                config_field=types.Field(
                    types.Dict({
                        'credentials': Field(types.Dict({
                            'user' : Field(types.String),
                            'pass' : Field(types.String),
                        })),
                    }),
                ),
            )
        }
    )

Notice the *second* context definition. It

1) Accepts configuration, this specifies that in a typed fashion.
2) Creates a different version of that store, to which it passes configuration.

Now when you invoke this pipeline with the following yaml file:

.. code-block:: yaml

    context:
      cloud:
        config:
          credentials:
            user: some_user
            pass: some_password

    solids:
      ingest_a:
        config: 2
      ingest_b: 
        config: 3

It will create the production version of that store. Note that you have
not change the implementation of any solid to do this. Only the configuration
changes.
'''

snapshots['test_build_all_docs 37'] = '''Expectations
============

Dagster has a first-class concept to capture data quality tests. We call these
data quality tests expectations.

Data pipelines have the property that they typically do not control
what data they ingest. Unlike a traditional application where you can
prevent users from entering malformed data, data pipelines do not have
that option. When unexpected data enters a pipeline and causes a software
error, typically the only recourse is to update your code. 

Lying within the code of data pipelines are a whole host of implicit
assumptions about the nature of the data. One way to frame the goal of
expectations is to say that they make those implict assumption explicit.
And by making these a first class concept they can be described with metadata,
inspected, and configured to run in different ways.

Let us return to a slightly simplified version of the data pipeline from part nine.

.. code-block:: python

    @solid(
        config_field=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def ingest_a(info):
        return info.config


    @solid(
        config_field=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def ingest_b(info):
        return info.config

    @solid(
        inputs=[InputDefinition('num_one', types.Int),
                InputDefinition('num_two', types.Int)],
        outputs=[OutputDefinition(types.Int)],
    )
    def add_ints(_info, num_one, num_two):
        return num_one + num_two


    def define_part_ten_step_one():
        return PipelineDefinition(
            name='part_ten_step_one',
            solids=[ingest_a, ingest_b, add_ints],
            dependencies={
                'add_ints': {
                    'num_one': DependencyDefinition('ingest_a'),
                    'num_two': DependencyDefinition('ingest_b'),
                },
            },
        )

Imagine that we had assumptions baked into the code of this pipeline such that the code only
worked on positive numbers, and we wanted to communicate that requirement to the user
in clear terms. We'll add an expectation in order to do this.


.. code-block:: python

    @solid(
        config_field=ConfigDefinition(types.Int),
        outputs=[
            OutputDefinition(
                types.Int,
                expectations=[
                    ExpectationDefinition(
                        name="check_positive",
                        expectation_fn=lambda _info, value: ExpectationResult(success=value > 0)
                    ),
                ],
            ),
        ],
    )
    def ingest_a(info):
        return info.config


You'll notice that we added an ExpectationDefinition to the output of ingest_a. Expectations
can be attached to inputs or outputs and operate on the value of that input or output.

Expectations perform arbitrary computation on that value and then return an ExpectationResult.
The user communicates whether or not the expectation succeeded via this return value.

If you run this pipeline, you'll notice some logging that indicates that the expectation
was processed:

.. code-block:: python

    execute_pipeline(
        define_part_ten_step_one(), 
        {
            'context': {
                'default': {
                    'config': {
                        'log_level': 'DEBUG',
                    }
                }
            },
            'solids': {
                'ingest_a': {
                    'config': 2,
                },
                'ingest_b': {
                    'config': 3,
                },
            }
        },
    )

And run it...

.. code-block:: sh

    $ python part_ten.py
    ... log spew
    2018-09-14 13:13:13 - dagster - DEBUG - orig_message="Expectation ingest_a.result.expectation.check_positive succeeded on 2." log_message_id="938ab7fa-c955-408a-9f44-66b0b6ecdcad" pipeline="part_ten_step_one" solid="ingest_a" output="result" expectation="check_positive" 
    ... more log spew 

Now let's make this fail. Currently the default behavior is to throw an error and halt execution
when an expectation fails. So:

.. code-block:: python

    execute_pipeline(
        define_part_ten_step_one(), 
        {
            'context': {
                'default': {
                    'config': {
                        'log_level': 'DEBUG',
                    }
                }
            },
            'solids': {
                'ingest_a': {
                    'config': -5,
                },
                'ingest_b': {
                    'config': 3,
                },
            }
        },
    )

And then:

.. code-block:: sh

    $ python part_ten.py
    ... bunch of log spew
    dagster.core.errors.DagsterExpectationFailedError: DagsterExpectationFailedError(solid=add_ints, output=result, expectation=check_positivevalue=-2)

We can also tell execute_pipeline to not throw on error:

.. code-block:: python

    execute_pipeline(
        define_part_ten_step_one(), 
        {
            'context': {
                'default': {
                    'config': {
                        'log_level': 'DEBUG',
                    }
                }
            },
            'solids': {
                'ingest_a': {
                    'config': -5,
                },
                'ingest_b': {
                    'config': 3,
                },
            }
        },
        throw_on_error=False,
    )

.. code-block:: sh

    $ python part_ten.py
    ... log spew
    2018-11-08 10:38:28 - dagster - DEBUG - orig_message="Expectation add_ints.result.expectation.check_positive failed on -2." log_message_id="9ca21f5c-0578-4b3f-80c2-d129552525a4" run_id="c12bdc2d-c008-47db-8b76-e257262eab79" pipeline="part_ten_step_one" solid="add_ints" output="result" expectation="check_positive"

Because the system is explictly aware of these expectations they are viewable in tools like dagit.
It can also configure the execution of these expectations. The capabilities of this aspect of the
system are currently quite immature, but we expect to develop these more in the future. The only
feature right now is the ability to skip expectations entirely. This is useful in a case where
expectations are expensive and you have a time-critical job you must. In that case you can
configure the pipeline to skip expectations entirely.


.. code-block:: python

    execute_pipeline(
        define_part_ten_step_one(), 
        {
            'context': {
                'default': {
                    'config': {
                        'log_level': 'DEBUG',
                    }
                }
            },
            'solids': {
                'ingest_a': {
                    'config': 2,
                },
                'ingest_b': {
                    'config': 3,
                },
            },
            'expectations': {
                'evaluate': False,
            },
        },
    )

.. code-block:: sh

    $ python part_ten.py
    ... expectations will not in the log spew 

We plan on adding more sophisticated capabilties to this in the future.
'''

snapshots['test_build_all_docs 38'] = '''Hello, World
------------
See :doc:`../installation` for instructions getting dagster -- the core library -- and dagit --  
the web UI tool used to visualize your data pipelines -- installed on your platform of choice.

Let's write our first pipeline and save it as ``hello_world.py``.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/hello_world.py
   :linenos:
   :lines: 1-10
   :caption: hello_world.py

This example introduces three concepts:

1.  A **solid** is a functional unit of computation in a data pipeline. In this example, we use the
    decorator :py:func:`@lambda_solid <dagster.lambda_solid>` to mark the function ``hello_world``
    as a solid: a functional unit which takes no inputs and returns the output ``'hello'`` every
    time it's run.

2.  A **pipeline** is a set of solids arranged into a DAG of computation that produces data assets.
    In this example, the call to :py:class:`PipelineDefinition <dagster.PipelineDefinition>` defines
    a pipeline with a single solid.

3.  We **execute** the pipeline by running :py:func:`execute_pipeline <dagster.execute_pipeline>`.
    Dagster will call into each solid in the pipeline, functionally transforming its inputs, if any,
    and threading its outputs to solids further on in the DAG.

Pipeline Execution
^^^^^^^^^^^^^^^^^^

Assuming you've saved this pipeline as ``hello_world.py``, we can execute it via any of three
different mechanisms:

1. The CLI utility `dagster`
2. The GUI tool `dagit`
3. Using dagster as a library within your own script.

CLI
~~~

.. code-block:: console

    $ dagster pipeline execute -f hello_world.py -n define_hello_world_pipeline
    2019-01-08 11:23:57 - dagster - INFO - orig_message="Beginning execution of pipeline hello_world_pipeline" log_message_id="5c829421-06c7-49eb-9195-7e828e37eab8" run_id="dfc8165a-f37e-43f5-a801-b602e4409f74" pipeline="hello_world_pipeline" event_type="PIPELINE_START"
    2019-01-08 11:23:57 - dagster - INFO - orig_message="Beginning execution of hello_world.transform" log_message_id="5878513a-b510-4837-88cb-f77205931abb" run_id="dfc8165a-f37e-43f5-a801-b602e4409f74" pipeline="hello_world_pipeline" solid="hello_world" solid_definition="hello_world" event_type="EXECUTION_PLAN_STEP_START" step_key="hello_world.transform"
    2019-01-08 11:23:57 - dagster - INFO - orig_message="Solid hello_world emitted output \\"result\\" value \'hello\'" log_message_id="b27fb70a-744a-46cc-81ba-677247b1b07b" run_id="dfc8165a-f37e-43f5-a801-b602e4409f74" pipeline="hello_world_pipeline" solid="hello_world" solid_definition="hello_world"
    2019-01-08 11:23:57 - dagster - INFO - orig_message="Execution of hello_world.transform succeeded in 0.9558200836181641" log_message_id="25faadf5-b5a8-4251-b85c-dea6d00d99f0" run_id="dfc8165a-f37e-43f5-a801-b602e4409f74" pipeline="hello_world_pipeline" solid="hello_world" solid_definition="hello_world" event_type="EXECUTION_PLAN_STEP_SUCCESS" millis=0.9558200836181641 step_key="hello_world.transform"
    2019-01-08 11:23:57 - dagster - INFO - orig_message="Step hello_world.transform emitted \'hello\' for output result" log_message_id="604dc47c-fe29-4d71-a531-97ae58fda0f4" run_id="dfc8165a-f37e-43f5-a801-b602e4409f74" pipeline="hello_world_pipeline"
    2019-01-08 11:23:57 - dagster - INFO - orig_message="Completing successful execution of pipeline hello_world_pipeline" log_message_id="1563854b-758f-4ae2-8399-cb75946b0055" run_id="dfc8165a-f37e-43f5-a801-b602e4409f74" pipeline="hello_world_pipeline" event_type="PIPELINE_SUCCESS"

There's a lot of information in these log lines (we'll get to how you can use, and customize,
them later), but you can see that the third message is:
```Solid hello_world emitted output \\"result\\" value \'hello\'"```. Success!

Dagit
~~~~~

To visualize your pipeline (which only has one node) in dagit, you can run:

.. code-block:: console

   $ dagit -f hello_world.py -n define_hello_world_pipeline
   Serving on http://127.0.0.1:3000

You should be able to navigate to http://127.0.0.1:3000/hello_world_pipeline/explore in your web
browser and view your pipeline.

.. image:: hello_world_figure_one.png

There are lots of ways to execute dagster pipelines. If you navigate to the "Execute"
tab (http://127.0.0.1:3000/hello_world_pipeline/execute), you can execute your pipeline directly
from dagit. Logs will stream into the bottom right pane of the interface, where you can filter them
by log level.

.. image:: hello_world_figure_two.png

Library
~~~~~~~

If you'd rather execute your pipelines as a script, you can do that without using the dagster CLI
at all. Just add a few lines to `hello_world.py` (highlighted in yellow):

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/hello_world.py
   :linenos:
   :caption: hello_world.py
   :emphasize-lines: 1,13-15

Then you can just run:

.. code-block:: console

    $ python hello_world.py

Next, let's build our first multi-solid DAG in :doc:`Hello, DAG <hello_dag>`!
'''

snapshots['test_build_all_docs 39'] = '''Unit-testing Pipelines
----------------------

Unit testing data pipelines is, broadly speaking, quite difficult. As a result, it is typically
never done.

One of the mechanisms included in dagster to enable testing has already been discussed: contexts.
The other mechanism is the ability to execute arbitrary subsets of a DAG. (This capability is
useful for other use cases but we will focus on unit testing for now).

Let us start where we left off.

We have the following pipeline:

.. code-block:: python

    @solid(
        config_field=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def load_number(info):
        return info.config


    @lambda_solid(
        inputs=[
            InputDefinition('num1', types.Int),
            InputDefinition('num2', types.Int),
        ],
        output=OutputDefinition(types.Int),
    )
    def adder(num1, num2):
        return num1 + num2


    @lambda_solid(
        inputs=[
            InputDefinition('num1', types.Int),
            InputDefinition('num2', types.Int),
        ],
        output=OutputDefinition(types.Int),
    )
    def multer(num1, num2):
        return num1 * num2


    def define_part_fourteen_step_one():
        # (a + b) * (c + d)

        return PipelineDefinition(
            name='tutorial_part_thirteen_step_one',
            solids=[load_number, adder, multer],
            dependencies={
                SolidInstance(load_number.name, 'a'): {},
                SolidInstance(load_number.name, 'b'): {},
                SolidInstance(load_number.name, 'c'): {},
                SolidInstance(load_number.name, 'd'): {},
                SolidInstance(adder.name, 'a_plus_b'): {
                    'num1': DependencyDefinition('a'),
                    'num2': DependencyDefinition('b'),
                },
                SolidInstance(adder.name, 'c_plus_d'): {
                    'num1': DependencyDefinition('c'),
                    'num2': DependencyDefinition('d'),
                },
                SolidInstance(multer.name, 'final'): {
                    'num1': DependencyDefinition('a_plus_b'),
                    'num2': DependencyDefinition('c_plus_d'),
                },
            },
        )

Let's say we wanted to test *one* of these solids in isolation.

We want to do is isolate that solid and execute with inputs we
provide, instead of from solids upstream in the dependency graph.

So let's do that. Follow along in the comments:

.. code-block:: python

    # The pipeline returned is a new unnamed, pipeline
    # that contains the isolated solid plus the injected solids
    # that will satisfy it inputs
    pipeline = PipelineDefinition.create_single_solid_pipeline(
        #
        # This takes an existing pipeline
        #
        define_part_fourteen_step_one(),
        #
        # Isolates a single solid. In this case "final"
        #
        'final',
        #
        # Final has two inputs, num1 and num2. You must provide
        # values for this. So we create solids in memory to provide
        # values. The solids we are just emit the passed in values
        # as an output
        #
        injected_solids={
            'final': {
                'num1': define_stub_solid('stub_a', 3),
                'num2': define_stub_solid('stub_b', 4),
            }
        }
    )

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.result_list) == 3
    assert result.result_for_solid('stub_a').transformed_value() == 3
    assert result.result_for_solid('stub_b').transformed_value() == 4
    assert result.result_for_solid('final').transformed_value() == 12

We can also execute entire arbitrary subdags rather than a single solid.


.. code-block:: python

    def test_a_plus_b_final_subdag():
        pipeline = PipelineDefinition.create_sub_pipeline(
            define_part_fourteen_step_one(),
            ['a_plus_b', 'final'],
            ['final'],
            injected_solids={
                'a_plus_b': {
                    'num1': define_stub_solid('stub_a', 2),
                    'num2': define_stub_solid('stub_b', 4),
                },
                'final': {
                    'num2': define_stub_solid('stub_c_plus_d', 6),
                }
            },
        )

        pipeline_result = execute_pipeline(pipeline)

        assert pipeline_result.result_for_solid('a_plus_b').transformed_value() == 6
        assert pipeline_result.result_for_solid('final').transformed_value() == 36
'''

snapshots['test_build_all_docs 40'] = '''Reusable Solids
---------------

So far we have been using solids tailor-made for each pipeline they were resident in, and have
only used a single instance of that solid. However, solids are, at their core, a specialized type
of function. And like functions, they should be reusable and not tied to a particular call site.

Now imagine we a pipeline like the following:

.. code-block:: python

    @solid(config_field=ConfigDefinition(types.Int), outputs=[OutputDefinition(types.Int)])
    def load_a(info):
        return info.config


    @solid(config_field=ConfigDefinition(types.Int), outputs=[OutputDefinition(types.Int)])
    def load_b(info):
        return info.config


    @lambda_solid(
        inputs=[
            InputDefinition('a', types.Int),
            InputDefinition('b', types.Int),
        ],
        output=OutputDefinition(types.Int),
    )
    def a_plus_b(a, b):
        return a + b


    def define_part_thirteen_step_one():
        return PipelineDefinition(
            name='thirteen_step_one',
            solids=[load_a, load_b, a_plus_b],
            dependencies={
                'a_plus_b': {
                    'a': DependencyDefinition('load_a'),
                    'b': DependencyDefinition('load_b'),
                }
            }
        )


    def test_part_thirteen_step_one():
        pipeline_result = execute_pipeline(
            define_part_thirteen_step_one(),
            {
                'solids': {
                    'load_a': {
                        'config': 234,
                    },
                    'load_b': {
                        'config': 384
                    },
                },
            },
        )

        assert pipeline_result.success
        solid_result = pipeline_result.result_for_solid('a_plus_b')
        assert solid_result.transformed_value() == 234 + 384


You'll notice that the solids in this pipeline are very generic. There's no reason why we shouldn't be able
to reuse them. Indeed load_a and load_b only different by name. What we can do is include multiple
instances of a particular solid in the dependency graph, and alias them. We can make the three specialized
solids in this pipeline two generic solids, and then hook up three instances of them in a dependency
graph:

.. code-block:: python

    @solid(
        config_field=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def load_number(info):
        return info.config


    @lambda_solid(
        inputs=[
            InputDefinition('num1', types.Int),
            InputDefinition('num2', types.Int),
        ],
        output=OutputDefinition(types.Int),
    )
    def adder(num1, num2):
        return num1 + num2


    def define_part_thirteen_step_two():
        return PipelineDefinition(
            name='thirteen_step_two',
            solids=[load_number, adder],
            dependencies={
                SolidInstance('load_number', alias='load_a'): {},
                SolidInstance('load_number', alias='load_b'): {},
                SolidInstance('adder', alias='a_plus_b'): {
                    'num1': DependencyDefinition('load_a'),
                    'num2': DependencyDefinition('load_b'),
                }
            }
        )


    def test_part_thirteen_step_two():
        pipeline_result = execute_pipeline(
            define_part_thirteen_step_two(),
            {
                'solids': {
                    'load_a': {
                        'config': 23,
                    },
                    'load_b': {
                        'config': 38
                    },
                },
            },
        )

        assert pipeline_result.success
        solid_result = pipeline_result.result_for_solid('a_plus_b')
        assert solid_result.transformed_value() == 23 + 38


You can think of the solids parameter as declaring what solids are "in-scope" for the
purposes of this pipeline, and the dependencies parameter is how they instantiated
and connected together. Within the dependency graph and in config, the alias of the
particular instance is used, rather than the name of the definition.

Load this in dagit and you'll see that the node are the graph are labeled with
their instance name.

.. code-block:: sh

        $ dagit -f part_thirteen.py -n define_part_thirteen_step_two 

These can obviously get more complicated and involved, with solids being reused
many times:

.. code-block:: python

    @lambda_solid(
        inputs=[
            InputDefinition('num1', types.Int),
            InputDefinition('num2', types.Int),
        ],
        output=OutputDefinition(types.Int),
    )
    def multer(num1, num2):
        return num1 * num2

    def define_part_thirteen_step_three():
        # (a + b) * (c + d)

        return PipelineDefinition(
            name='tutorial_part_thirteen_step_three',
            solids=[load_number, adder, multer],
            dependencies={
                SolidInstance(load_number.name, 'a'): {},
                SolidInstance(load_number.name, 'b'): {},
                SolidInstance(load_number.name, 'c'): {},
                SolidInstance(load_number.name, 'd'): {},
                SolidInstance(adder.name, 'a_plus_b'): {
                    'num1': DependencyDefinition('a'),
                    'num2': DependencyDefinition('b'),
                },
                SolidInstance(adder.name, 'c_plus_d'): {
                    'num1': DependencyDefinition('c'),
                    'num2': DependencyDefinition('d'),
                },
                SolidInstance(multer.name, 'final'): {
                    'num1': DependencyDefinition('a_plus_b'),
                    'num2': DependencyDefinition('c_plus_d'),
                },
            },
        )

Now these arithmetic operations are not particularly interesting, but one
can imagine reusable solids doing more useful things like uploading files
to cloud storage, unzipping files, etc.
'''

snapshots['test_build_all_docs 41'] = '''Repositories
------------
Dagster is a not just a programming model for pipelines, it is also a platform for
tool-building. You've already met the dagster and dagit CLI tools, which let you programmatically
run and visualize pipelines.

In previous examples we have specified a file (``-f``) and named a pipeline definition function
(``-n``) in order to tell the CLI tools how to load a pipeline, e.g.:

.. code-block:: console

   $ dagit -f hello_world.py -n define_hello_world_pipeline
   $ dagster pipeline execute -f hello_world.py -n define_hello_world_pipeline

But most of the time, especially when working on long-running projects with other people, we will
want to be able to target many pipelines at once with our tools. 

A **repository** is a collection of pipelines at which dagster tools may be pointed.

Repostories are declared using a new API,
:py:func:`RepositoryDefinition <dagster.RepositoryDefinition>`:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/repos.py
   :linenos:
   :caption: repos.py

If you save this file as ``repos.py``, you can then run the command line tools on it. Try running:

.. code-block:: console

    $ dagster pipeline list -f repos.py -n define_repo
    Repository demo_repo
    ************************
    Pipeline: repo_demo_pipeline
    Solids: (Execution Order)
        hello_world

Typing the name of the file and function defining the repository gets tiresome and repetitive, so
let's create a declarative config file with this information to make using the command line tools
easier. Save this file as ``repository.yml``. This is the default name for a repository config file,
although you can tell the CLI tools to use any file you like.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/repos_1.yml
   :linenos:
   :caption: repository.yml

Now you should be able to list the pipelines in this repo without all the typing:

.. code-block:: console

    $ dagster pipeline list
    Repository demo_repo
    ************************
    Pipeline: repo_demo_pipeline
    Solids: (Execution Order)
        hello_world


You can also specify a module instead of a file in the repository.yml file.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/repos_2.yml
   :linenos:
   :caption: repository.yml

Dagit
^^^^^
Dagit uses the same pattern as the other dagster CLI tools. If you've defined a repository.yml file,
just run dagit with no arguments, and you can visualize and execute all the pipelines in your
repository:

.. code-block:: console

    $ dagit
    Serving on http://localhost:3000

.. image:: repos_figure_one.png

In the next part of the tutorial, we'll get to know :doc:`Pipeline Execution <pipeline_execution>`
a little better, and learn how to execute pipelines in a repository from the command line by name,
with swappable config.
'''

snapshots['test_build_all_docs 42'] = '''Hello, DAG
----------
One of the core capabitilies of dagster is the ability to express data pipelines as arbitrary
directed acyclic graphs (DAGs) of solids.

We'll define a very simple two-solid pipeline whose first solid returns a hardcoded string,
and whose second solid concatenates two copies of its input. The output of the pipeline should be
two concatenated copies of the hardcoded string.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/hello_dag.py
   :linenos:
   :caption: hello_dag.py

This pipeline introduces a few new concepts.

1.  Solids can have **inputs** defined by instances of
    :py:class:`InputDefinition <dagster.InputDefinition>`. Inputs allow us to connect solids to
    each other, and give dagster information about solids' dependencies on each other (and, as
    we'll see later, optionally let dagster check the types of the inputs at runtime).

2.  Solids' **dependencies** on each other are expressed by instances of 
    :py:class:`DependencyDefinition <dagster.DependencyDefinition>`.
    You'll notice the new argument to :py:class:`PipelineDefinition <dagster.PipelineDefinition>`
    called ``dependencies``, which is a dict that defines the connections between solids in a
    pipeline's DAG.

    .. literalinclude::  ../../dagster/tutorials/intro_tutorial/hello_dag.py
       :lines: 22-26
       :dedent: 8

    The first layer of keys in this dict are the *names* of solids in the pipeline. The second layer
    of keys are the *names* of the inputs to each solid. Each input in the DAG must be provided a
    :py:class:`DependencyDefinition <dagster.DependencyDefinition>`. (Don't worry -- if you forget
    to specify an input, a helpful error message will tell you what you missed.)
    
    In this case the dictionary encodes the fact that the input ``arg_one`` of solid ``solid_two``
    should flow from the output of ``solid_one``.

Let's visualize the DAG we've just defined in dagit.

.. code-block:: console

   $ dagit -f hello_dag.py -n define_hello_dag_pipeline

Navigate to http://127.0.0.1:3000/hello_dag_pipeline/explore or choose the hello_dag_pipeline
from the dropdown:

.. image:: hello_dag_figure_one.png

One of the distinguishing features of dagster that separates it from many workflow engines is that
dependencies connect *inputs* and *outputs* rather than just *tasks*. An author of a dagster
pipeline defines the flow of execution by defining the flow of *data* within that
execution. This is core to the the programming model of dagster, where each step in the pipeline
-- the solid -- is a *functional* unit of computation. 

Now run the pipeline we've just defined, either from dagit or from the command line:

.. code-block:: console

\t$ dagster pipeline execute -f hello_dag.py -n define_hello_dag_pipeline

In the next section, :doc:`An actual DAG <actual_dag>`, we'll build our first DAG with interesting
topology and see how dagster determines the execution order of a pipeline.
'''

snapshots['test_build_all_docs 43'] = '''An actual DAG
-------------

Next we will build a slightly more topologically complex DAG that demonstrates how dagster
determines the execution order of solids in a pipeline:

.. image:: actual_dag_figure_one.png

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/actual_dag.py
   :linenos:
   :caption: actual_dag.py

Again, it is worth noting how we are connecting *inputs* and *outputs* rather than just *tasks*.
Point your attention to the ``solid_d`` entry in the dependencies dictionary: we declare
dependencies on a per-input basis.

When you execute this example, you'll see that ``solid_a`` executes first, then ``solid_b`` and
``solid_c`` -- in any order -- and ``solid_d`` executes last, after ``solid_b`` and ``solid_c``
have both executed.

In more sophisticated execution environments, ``solid_b`` and ``solid_c`` could execute not just
in any order, but at the same time, since their inputs don't depend on each other's outputs --
but both would still have to execute after ``solid_a`` (because they depend on its output to
satisfy their inputs) and before ``solid_d`` (because their outputs in turn are depended on by
the input of ``solid_d``).

Try it in dagit or from the command line:

.. code-block:: console

   $ dagster pipeline execute -f actual_dag.py -n define_diamond_dag_pipeline

What's the output of this DAG?

We've seen how to wire solids together into DAGs. Now let's look more deeply at their
:doc:`Inputs <inputs>`, and start to explore how solids can interact with their external
environment.
'''

snapshots['test_build_all_docs 44'] = '''Configuration Schemas
---------------------

Dagster includes a system for strongly-typed, self-describing configurations schemas. These
descriptions are very helpful when learning how to operate a pipeline, make a rich configuration
editing experience possible, and help to catch configuration errors before pipeline execution. 

Let's see how the configuration schema can prevent errors and improve pipeline documentation.
We'll replace the config field in our solid definition with a structured, strongly typed schema.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/configuration_schemas.py
   :linenos:
   :caption: configuration_schemas.py
   :emphasize-lines: 15

The previous env.yml file works as before:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/configuration_schemas.yml
   :linenos:
   :caption: configuration_schemas.yml

Now let's imagine we made a mistake and passed an ``int`` in our configuration:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/configuration_schemas_error_1.yml
   :linenos:
   :emphasize-lines: 9 
   :caption: configuration_schemas_error_1.yml

And then ran it:

.. code-block:: console

    $ dagster pipeline execute -f configuration_schemas.py \\
    -n define_demo_configuration_schema_pipeline -e configuration_schemas_error_1.yml
    ...
    dagster.core.execution.PipelineConfigEvaluationError: Pipeline "demo_configuration_schema" config errors:
        Error 1: Type failure at path "root:solids:double_the_word:config:word" on type "String". Got "1".

Now, instead of a runtime failure which might arise deep inside a time-consuming or expensive
pipeline execution, and which might be tedious to trace back to its root cause, we get a clear,
actionable error message before the pipeline is ever executed.

Let's see what happens if we pass config with the wrong structure:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/configuration_schemas_error_2.yml
   :linenos:
   :emphasize-lines: 9 
   :caption: configuration_schemas_error_2.yml

And then run the pipeline:

.. code-block:: console

    $ dagster pipeline execute -f configuration_schemas.py \\
    -n define_demo_configuration_schema_pipeline -e configuration_schemas_error_2.yml
    ...
    dagster.core.execution.PipelineConfigEvaluationError: Pipeline "demo_configuration_schema" config errors:
        Error 1: Undefined field "double_the_word_with_typed_config" at path root:solids
        Error 2: Missing required field "double_the_word" at path root:solids

Besides configured values, the type system is also used to evaluate the runtime values that flow
between solids. Types are attached, optionally, both to inputs and to outputs. If a type
is not specified, it defaults to the :py:class:`Any <dagster.core.types.Any>` type.

.. code-block:: python

    @solid(
        config_field=types.Field(
            types.Dict({'word': Field(types.String)})
        ),
        outputs=[OutputDefinition(types.String)],
    )
    def typed_double_word(info):
        return info.config['word'] * 2

You'll see here that now the output is annotated with a type. This both ensures
that the runtime value conforms requirements specified by the type (in this case
an instanceof check on a string) and also provides metadata to view in tools such
as dagit. That the output is a string is now guaranteed by the system. If you
violate this, execution halts.

So imagine we made a coding error (mistyped the output) such as:

.. code-block:: python

    @solid(
        config_field=types.Field(
            types.Dict({'word': Field(types.String)})
        ),
        outputs=[OutputDefinition(types.Int)],
    )
    def typed_double_word_mismatch(info):
        return info.config['word'] * 2

When we run it, it errors:

.. code-block:: sh

    $ dagster pipeline execute part_eight -e env.yml
    dagster.core.errors.DagsterInvariantViolationError: Solid typed_double_word_mismatch output name result output quuxquux
                type failure: Expected valid value for Int but got 'quuxquux'
'''

snapshots['test_build_all_docs 45'] = '''Execution
=========

.. currentmodule:: dagster

Executing pipelines and solids.

.. autofunction:: execute_pipeline

.. autofunction:: execute_pipeline_iterator

.. autoclass:: ExecutionContext
   :members:

.. autoexception:: PipelineConfigEvaluationError

.. autoclass:: PipelineExecutionResult
   :members:

.. autoclass:: ReentrantInfo
   :members:

.. autoclass:: SolidExecutionResult
   :members:
'''

snapshots['test_build_all_docs 46'] = '''Definitions
===========================

.. currentmodule:: dagster

Core API to define Solids and Pipelines.

.. autoclass:: ContextCreationExecutionInfo
    :members:

.. autoclass:: DependencyDefinition
    :members:

.. autoclass:: ExpectationDefinition
    :members:

.. autoclass:: ExpectationExecutionInfo
    :members:

.. autoclass:: ExpectationResult
    :members:

.. autoclass:: Field
    :members:

.. autoclass:: InputDefinition
    :members:

.. autoclass:: OutputDefinition
    :members:

.. autoclass:: PipelineContextDefinition
    :members:

.. autoclass:: PipelineDefinition
    :members:

.. autoclass:: RepositoryDefinition
    :members:

.. autoclass:: ResourceDefinition
    :members:

.. autoclass:: Result
    :members:

.. autoclass:: SolidDefinition
    :members:

.. autoclass:: SolidInstance
    :members:

.. autoclass:: TransformExecutionInfo
   :members:'''

snapshots['test_build_all_docs 47'] = '''Utilities
=========

.. currentmodule:: dagster

.. autofunction:: define_stub_solid

.. autofunction:: execute_solid
'''

snapshots['test_build_all_docs 48'] = '''Types
=========

.. module:: dagster.core.types

Dagster type system.

Type definitions
-----------------

.. autoclass:: PythonObjectType

.. autoclass:: Any

.. autofunction:: Nullable

.. autofunction:: List

.. autoclass:: String

.. autoclass:: Path

.. autoclass:: Int

.. autoclass:: Bool
'''

snapshots['test_build_all_docs 49'] = '''Decorators
===========================

.. currentmodule:: dagster

A more concise way to define solids.

.. autofunction:: lambda_solid

.. autofunction:: solid

.. autoclass:: MultipleResults
    :members:
'''

snapshots['test_build_all_docs 50'] = '''Errors
=========

.. currentmodule:: dagster

Core dagster error classes.

.. autoexception:: DagsterExpectationFailedError

.. autoexception:: DagsterInvalidDefinitionError

.. autoexception:: DagsterInvariantViolationError

.. autoexception:: DagsterRuntimeCoercionError

.. autoexception:: DagsterTypeError

.. autoexception:: DagsterUserCodeExecutionError
'''
