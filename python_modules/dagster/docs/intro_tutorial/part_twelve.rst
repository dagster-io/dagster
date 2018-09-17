Custom Types
------------

So far we have only used the built-in types the come with dagster
to describe data flowing between different solids. However this
only gets one so far, and is typically only useful for toy
pipelines. You are going to want to define our own custom types
to describe your pipeline- and runtime-specific data structures.

The most common operation will be to simply do a typecheck against
a particular python type.

TODO: complete this tutorial