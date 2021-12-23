# 8. Start with the tests that monitor asset quality

* **Status**: Proposed <br/>
* **Date**: 2021-12-23 <br/>
* **Deciders**: David Laing <br/>

## Context

People care about the data Assets that our data jobs produce, not the jobs themselves.

Whether a Dagster job execution passes or fails is irrelevant - what matters is that the Assets produced meet quality expectations like

1. Freshness - is the data up-to-date?
2. Correctness - is the schema correct?
3. Warning count - are the number of detected data defects at an acceptable level?

Writing tests to define & measure each of these quality measures first helps guide which data job logic we should write.

Running those tests on a schedule serves as a monitoring system for our data assets.

## Decision

WIP
