---
title: "Lesson 7: Pushing the project to GitHub"
module: 'dbt_dagster'
lesson: '7'
---

# Pushing the project to GitHub

We’ll be using GitHub in this lesson because Dagster+ has a native integration with GitHub to quickly get deployment set up. This functionality can be easily replicated if your company uses a different version control provider, but we’ll standardize on using GitHub for now. Whether you use the command line or an app like GitHub Desktop is up to you.

1. Because you cloned this project, it’ll already have a git history and context. Let’s delete that by running `rm -rf .git`.
2. Create a new repository on GitHub.
3. Push the code from your project into this GitHub repository’s `main` branch.

{% callout %}
> 💡 **Important!** Make sure the `.env` file in your project isn’t included in your commit! The starter project for this course should have it listed in `.gitignore`, but it’s wise to double-check before accidentally committing sensitive files.
{% /callout %}
