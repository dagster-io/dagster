---
title: Feature engineering
description: Feature Engineering Book Categories
last_update:
  author: Dennis Hume
sidebar_position: 30
---

With the data loaded, we can think of how we might want to train our model. One possible use case is to create a model that can tell categorize books based on their details.

The Goodreads data does not include categories exactly, but has something similar in `popular_shelves`. These are free text tags that users can associate with books. Looking at a book, you can see how often certain shelves are used:

```sql
select popular_shelves from graphic_novels limit 5;
```

```
[{'count': 228, 'name': to-read}, {'count': 2, 'name': graphic-novels}, {'count': 1, 'name': ff-re-…`
[{'count': 2, 'name': bd}, {'count': 2, 'name': to-read}, {'count': 1, 'name': french-author}, {'co…`
[{'count': 493, 'name': to-read}, {'count': 113, 'name': graphic-novels}, {'count': 102, 'name': co…`
[{'count': 222, 'name': to-read}, {'count': 9, 'name': currently-reading}, {'count': 3, 'name': mil…`
[{'count': 20, 'name': to-read}, {'count': 8, 'name': comics}, {'count': 4, 'name': graphic-novel},…`
```

Parsing the data out by unpacking and aggregating this field, we can see the most popular shelves:

```sql
select
	shelf.name as category,
	sum(cast(shelf.count as integer)) as category_count
from (
    select
        unnest(popular_shelves) as shelf
    from graphic_novels
)
group by 1
order by 2 desc
limit 15;
```

| category | category_count |
| --- | --- |
| to-read | 87252 |
| comics | 76283 |
| graphic-novels | 67923 |
| graphic-novel | 58219 |
| currently-reading | 57252 |
| fiction | 50014 |
| owned | 48936 |
| favorites | 47256 |
| comic | 46948 |
| comics-graphic-novels | 38433 |
| fantasy | 37003 |
| comic-books | 36638 |
| default | 35292 |
| books-i-own | 34620 |
| library | 31378 |

A lot of these shelves would be hard to use for modeling (such as `owned` or `default`). But genres such as `fantasy` could be interesting. If we continued looking through shelves, these are the most popular genres:

```python
CATEGORIES = [
    "fantasy", "horror", "humor", "adventure",
    "action", "romance", "ya", "superheroes",
    "comedy", "mystery", "supernatural", "drama",
]
```

Using these categories, we can construct a table of the most common genres and select the single best genre for each book (assuming it was shelved that way at least three times). We can then wrap that query in an asset and materialize it as a table alongside our other DuckDB tables:

<CodeExample path="docs_projects/project_llm_fine_tune/project_llm_fine_tune/assets.py" language="python" startAfter="start_book_category" endBefore="end_book_category"/>

## Enrichment table

With our `book_category` asset created, we can combine that with the `author` and `graphic_novel` assets to create our final data set we will use for modeling. Here we will both create the table within DuckDB and select its contents into a DataFrame, which we can pass to our next series of assets:

<CodeExample path="docs_projects/project_llm_fine_tune/project_llm_fine_tune/assets.py" language="python" startAfter="start_enriched_graphic_novels" endBefore="end_enriched_graphic_novels"/>

## Next steps

- Continue this example with [file creation](file-creation)