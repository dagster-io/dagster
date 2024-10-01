# Dagster University

This directory contains the content for Dagster University, located at https://courses.dagster.io. The site is built with [NextJS](https://nextjs.org/) and [Markdoc](https://markdoc.dev/).

---

## Setup

First, clone this repo and install the dependencies required:

```bash
npm install
# or
yarn install
```

To serve the site locally in development mode (hot-reloading), run:

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

---

## Authoring

Course content lives in `/dagster-university/pages`. Each course has:

- A category page, located in the directory root, ex: `/../../dagster-essentials.md`. Links to individual lessons are added to these pages to make it easier to navigate the site locally.
- A dedicated subdirectory, ex: `/../../dagster-essentials`, which contains a folder for each lesson in the course.

### Lesson content

Learn best by example? Check out this PR to see how to [add a new lesson to a course](https://github.com/dagster-io/dagster/pull/20096).

### Formatting with Markdown

We use [Markdoc](https://markdoc.dev/), a flavor of Markdown, to author our content. This flavor of Markdown is similar to that used on GitHub, but with some additional capabilities. Refer to the [Markdoc syntax documentation](https://markdoc.dev/docs/syntax) for more information.

#### Tables

Commonmark tables are supported, but you can also use list formatting to construct tables. For example:

```markdown
## commonmark table

| Name  | ID | Description                |
|-------|----|----------------------------|
| Daggy | 1  | The most educated octopus. |
```

Becomes the following in Markdoc syntax:

```markdown
## markdoc table 

{% table %}
* Name
* ID
* Description
---
* Daggy
* 1
* The most educated octopus.
{% /table %}
```

Refer to the [Markdoc table documentation](https://markdoc.dev/docs/tags#table) for more information and examples.

---

## Getting help

- Join the [Dagster Slack](https://dagster.io/community) community and ask a question in our `#dagster-university` channel
- Find solutions and patterns in our [GitHub discussions](https://github.com/dagster-io/dagster/discussions)
- Check out the [Dagster Docs](https://docs.dagster.io/)