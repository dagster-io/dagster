---
title: 'Lesson 8: Overview'
module: 'dagster_essentials'
lesson: '8'
---

# Overview

In the previous lesson, you learned about schedules and running your pipelines regularly. Going back to the cookie analogy, imagine that your cookie business is blossoming, and you’ve started taking orders in advance. Making every cookie right as each order came in would create problems. For example, an order for today is more urgent than an order for next week. Meanwhile, on some days, you would receive 100 orders, but you may receive zero orders on other days.

Therefore, you batch your orders by the day they’re expected to be picked up. Every morning, you look at the orders to be fulfilled that day and only make the cookies for those orders.

By looking at each day at a time, you are **partitioning** the orders. In this lesson, you’ll learn why to partition your data assets and how to do it in Dagster by partitioning the taxi trip data.
