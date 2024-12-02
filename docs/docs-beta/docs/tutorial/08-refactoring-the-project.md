---
title: Refactoring the Project
description: Refactor the completed project into a structure that is more organized and scalable. 
last_update:
  author: Alex Noonan
---

# Refactoring code

Many engineers generally leave something alone once its working as expected. But the first time you do something is rarely the best implementation of a use case and all projects benefit from incremental improvements.

## Splitting up folder structure

Right now the project is contained within one defintions file. This has gotten kinda unwieldy and if we were to add more to the project it would only get more disorganized. So we're going to create seperate files for all the different Dagster primitives 
- Assets
- schedules
- sensors

## Adjusting defintions object

Now that we have seperate folders we need to adjust how the different elements are adding to definitions since they are in seperate files 

1. Imports
2. Definitions 


## test that it all works

-- look up that cli command to load definitions


## Thats it!

## Reccomended next steps

- slack
- Dagster University courses
- Start a free trail