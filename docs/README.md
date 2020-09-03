## Development

To work on the docs:

```
cd docs/next
yarn dev
```

If you make a change to an .rst file, make sure you run the following:

    make buildnext

## Deployment

### Before Deploying

- Make sure you have set the following env variables: `NEXT_ALGOLIA_APP_ID`, `NEXT_ALGOLIA_API_KEY`, `NEXT_ALGOLIA_ADMIN_KEY`.

### Instructions

To build and push docs for a new version (e.g. 0.8.5), in `docs` directory, run:

```
pip install -e python_modules/automation
dagster-docs build -v 0.8.5
```

Then, go to the following directory and run `git push`:

```
cd /tmp/dagster-docs
git push
```

You should also have a new commit in your dagster repository. Run `git push` here as well. 

```
cd $DAGSTER_REPO
git push
```

Once you have _confirmed_ that the new version of the site is up at `docs.dagster.io` (may take up to 5 min), clone the following repo and run:

```
git clone https://github.com/dagster-io/docsearch-scraper.git
cd docsearch-scraper
pipenv install
pipenv shell
./docsearch docker:run config.json
```
