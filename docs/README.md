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
- Make sure you do a full `make dev_install`

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
# If you haven't already, check out the doc scraper repo, which builds the search index against
# the live site.  If you are not running from a fresh checkout, make sure you've picked up any
# new changes.
git clone https://github.com/dagster-io/docsearch-scraper.git
cd docsearch-scraper
pipenv install
pipenv shell

# This command will update the search index against the live site.
# If this is your first time running this, you will be prompted to set up your `.env` file with the
# appropriate values for `APPLICATION_ID`, and `API_KEY` (see `.env.example`).  These should be
# the same as NEXT_ALGOLIA_APP_ID and NEXT_ALGOLIA_ADMIN_KEY, respectively.
./docsearch docker:run config.json
```
