---
title: "Lesson 1: What's an orchestrator?"
module: 'dagster_essentials'
lesson: '1'
---

# What's an orchestrator?

An orchestrator is a tool that can manage and coordinate complex workflows and data pipelines. The field of orchestrators has continued to evolve with data engineering. For example, an orchestrator may be adopted when:

- Data from an ERP (Enterprise Resource Planning) system needs to be brought into a data warehouse daily for downstream BI reporting. Instead of triggering the refresh daily, an orchestrator can schedule this to run automatically.
- A video streaming platform wants to retrain its recommendation algorithm every time new content is added to the platform and does not want to retrain the algorithm every time the content is added manually
- A financial platform wants to update stock prices every five minutes, and it would be difficult to have someone trigger the pipeline refresh at that frequency manually

The first orchestrators were made to solve a simple problem: _I need to run some scripts as a sequence of steps at specific times_. Each step must wait for the step before it to finish before it starts. As time passed and the ceiling of what was possible in data engineering increased, people needed more out of their orchestrators.

Nowadays, modern orchestrators are used to create robustness and resiliency. When something breaks, orchestrators enable practitioners to understand where, when, and why it broke. Users expect orchestrators to let them monitor their workflows to understand individual steps and entire sequences of steps. At a glance, users can see what succeeded or had an error, how long each step took to run, and how a step connects to other steps. By empowering users with this information, data engineering becomes easier as people are able to develop data pipelines faster and troubleshoot issues more efficiently.

The first orchestrators removed the need for humans to run scripts manually at specific times. Today’s orchestrators continue to automate and reduce the need for human intervention. Orchestrators can retry a step when they fail, send a notification if something fails, prevent multiple steps from querying a database at the same time, or do a different step based on the result of the step before it.

There are multiple different types of orchestrators. Orchestrators can be general-purpose to accommodate for many types of workflows, or they can be made for specific types of workflows that deal with infrastructure, microservices, or data pipelines.
