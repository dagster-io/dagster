---
title: "Customizing automation conditions"
sidebar_position: 10
---

[Declarative Automation](/guides/automate/declarative-automation/) includes pre-built conditions to handle common use cases, such as executing on a periodic schedule or whenever an upstream dependency updates, but the core system is extremely flexible and can be tailored to your specific needs.

Each <PyObject section="assets" module="dagster" object="AutomationCondition" /> consists of a set of operands and operators that you can combine to suit your needs. For a full list of these operands, operators, and composition conditions, see "[Automation condition operands and operators](automation-condition-operands-and-operators)".

import DocCardList from '@theme/DocCardList';

<DocCardList />