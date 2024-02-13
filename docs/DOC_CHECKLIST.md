# Documentation pull request checklist

This checklist outlines some of the most common issues that come up during documentation pull request reviews.

Before submitting a PR for review, please check that your changes follow the guidelines listed here. Please ping Erin (@erinkcochran87) with questions.

---

## Headings

- Pages should only have one H1 heading, ex: `# Some heading`
- Use sentence case
- Shouldn’t include any extra formatting, including backticks, bold, components/tags, and emojis:
    - **Could-be-better:**
      ```markdown
      # `dagster-dbt` tutorial
      ```
    - **Better!:**
      ```markdown
      # dagster-dbt tutorial
      ```
- Level two headings (`## Some heading`) should be preceded by a horizontal rule:

   ```markdown
   # Page title

   Some copy

   ---    # horizontal rule

   ## Some heading
   ```

---

## Formatting

- UI components - buttons, tabs, labels, etc - should use **bold formatting. Ex: “The Materialize all** button”, “The **Reload** button”
- The following should use `code formatting`:
    - **Column and table names**, ex: “The `users` table”
    - **Keys/parameters and values**, ex: “The `In` parameter”,
    - **Names of libraries and packages**, ex: “The `dagster-dbt` library”
- Code examples should:
    - Live in `.py` files and not inline
    - Be enclosed in fenced backticks **and** include a language. This ensures syntax highlighting/CSS is correctly applied.
        - **Could-be-better:**
            
            ````markdown
            # Example without language:
            
            ```
            dagster dev
            ```
            
            # Example without backticks:
            
               dagster dev
            ````
            
        - **Better!:**
            
            ````markdown
            ```shell      # sometimes you'll just need to pick the closest option
            dagster dev
            ```
            ````

---

## Miscellaneous

- The first time a service/app/etc is mentioned, the company/platform/etc. must be included.
    - **Could-be-better:** “The BigQuery dataset”
    - **Better!:** “The Google BigQuery dataset”
- Names of companies, software, apps, etc. should be formatted exactly as the company/software/app/etc. uses them. The exception is if the name is being used as a literal value.
    - **Could-be-better:** "Your airflow instance..."
    - **Better!:** "Your Airflow instance..."

---

## Adding, deleting, and moving pages

When adding new pages **or** moving them around:

- Update the sidenav (`/docs/content/_navigation.json`)
- Add the page(s) to the correct category page. Ex: If adding a new guide, add it to `/docs/content/guides.mdx`

   You might also need to add it to a section page, like in **Guides.** Ex: `/docs/content/guides/best-practices.mdx`. In the near future we should have dynamic lists and won’t need to do this.
- **If deleting or moving a page**, add a redirect in `/docs/next/util/redirectUrls.json`
