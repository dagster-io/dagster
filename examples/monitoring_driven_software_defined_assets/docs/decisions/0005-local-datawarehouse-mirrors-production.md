# 4. A local/test datawarehouse (based on SQLite3) mirrors production 

* **Status**: Decided <br/>
* **Date**: 2021-11-19 <br/>
* **Deciders**: David Laing <br/>

## Context

A "development" instance of the production datawarehouse is needed to facilitate development and testing of code logic.  

This should be optimised for:

1. Speed -  Interaction with this data warehouse should be optimised for speed (potentially at the expense of data volume) 
2. Isolation - every developer / test suite should get its own instance of the datawarehouse.  
   It should be quick & easy to set up/teardown a new instance of the development datawarehouse.
3. Curated data edge cases - the data should be selected to exercise all the potential data edge cases

## Decision

Interactions with the data warehouse technology (eg: Amazon Athena, Apache Impala etc.) will be encapsulated by 
an implementation of the `_BaseDatawarehouseResource()` abstract base class.

The `SQLiteDatawarehouseResource()` implementation is optimised for the development use case.
