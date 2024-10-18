---
title: "What's Dagster+?"
displayed_sidebar: 'dagsterPlus'
sidebar_position: 1
---

# What's Dagster+?

Dagster+ is a managed orchestration platform built on top of Dagster's open source engine.

Dagster+ is built to be the most performant, reliable, and cost effective way for data engineering teams to run Dagster in production. Dagster+ is also great for students, researchers, or individuals who want to explore Dagster with minimal overhead.

Dagster+ comes in two flavors: a fully [Serverless](/dagster-plus/deployment/serverless) offering and a [Hybrid](/dagster-plus/deployment/hybrid) offering. In both cases, Dagster+ does the hard work of managing your data orchestration control plane. Compared to a [Dagster open source deployment](/guides/), Dagster+ manages:

- Dagster's web UI at https://dagster.plus
- Metadata stores for data cataloging and cost insights
- Backend services for orchestration, alerting, and more

Dagster+ Serverless is fully managed and your Dagster code executes in our environment. In Dagster+ Hybrid, you run an execution environment that connects to the Dagster+ control plane.

In addition to managed infrastructure, Dagster+ also adds core capabilities on top of Dagster open source to enable teams building data platforms:

- [Insights](/dagster-plus/insights), a powerful tool for identifying trends in your data platform overtime, optimizing cost, and answering questions like "Why does it feel like our pipelines are taking longer this month?".
- [Alerts](/dagster-plus/deployment/alerts) to a variety of services like Slack, PagerDuty, and email to notify your team of failed runs, data quality issues, and violated SLAs.
- Authentication, [Role Based Access Control](/dagster-plus/access/rbac), and [Audit Logs](/dagster-plus/access/rbac/audit-logs) which help teams implement data mesh strategies while remaining compliant.
- [Data Catalog](/dagster-plus/data-catalog), a powerful search-first experience that builds off of Dagster's best-in-class lineage graph to include searching for assets, metadata, column lineage, and more.
- [Branch Deployments](/dagster-plus/deployment/branch-deployments)

Ready to [get started](/dagster-plus/getting-started)?

## Other resources

- Learn more about Dagster+ [pricing and plan types](https://dagster.io/pricing) or [contact the Dagster team](https://dagster.io/contact)
- Dagster+ includes support, [click here](https://dagster.io/support) to learn more.
- Dagster+ is HIPAA compliant, SOC 2 Type II certified, and meets GDPR requirements. Learn more about Dagster+[ security](https://dagster.io/security).
- Migrate [from a Dagster open source deployment to Dagster+](/guides/self-hosted-to-dagster-plus)
- Dagster+ [status page](https://dagstercloud.statuspage.io/)
