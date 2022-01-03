# 5. Assets track data warnings

* **Status**: Proposed <br/>
* **Date**: 2021-11-30 <br/>
* **Deciders**: David Laing <br/>

## Context

Upstream Data Lake Assets often contain data rows that - whilst not strictly wrong - are suspicious and need to be reported to upstream data 
providers for further investigation.

Examples include:

1. Unexpected identifiers (eg, a customer id in an unexpected format)
2. Unusually large or small quantities

## Decision

Each Asset row will have a `meta__warnings` column containing a semi-colon separated list of detected data warnings

Each Asset partition has a count of all warnings in the partition.  

## Consequences

The Asset partition warning count can be tracked over time as a measure of whether the data asset quality is changing.

![Warnings shown for Assets](images/asset_warnings.png)
