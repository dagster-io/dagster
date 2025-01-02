# Dagster Support Bot Rag Application

## Data Source
1. Dagster Github Repository Issues
2. Dagster Github Repository Discussions
3. Dagster Docs Website
 

## Environment variables

For the pipeline to be able to pull releases information from Github, you'll need inform it of your Github credentials, via environment variables:
OPENAI_API_KEY=

DOCS_SITEMAP=
PINECONE_API_KEY=
PINECONE_ENV=

    GITHUB_TOKEN - [instructions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) on how to make one
