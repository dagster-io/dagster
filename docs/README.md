To develop the Sphinx docs:

    make livehtml

To build for Gatsby:

    make gatsby

To check for broken links, run the local server (`make livehtml`), then run:

    wget --spider -r -nd -nv -nc http://127.0.0.1:8000

You can also use [linkchecker](https://github.com/linkchecker/linkchecker/tree/htmlparser-beautifulsoup),
which is much slower but friendlier.

linkchecker http://127.0.0.1:8000

To deploy to Netlify, copy `versions/`, `*.js`, `*.json`, `scripts/`, and `src/`
over to the dagster-docs repo, then commit and push. Assuming your repos live
under `~/docs`:

    pushd ~/dev/dagster/docs/gatsby
    yarn sphinx -v latest
    gatsby build
    cp -R ./versions ~/dev/dagster-docs
    cp -R ./*.js ~/dev/dagster-docs
    cp -R ./*.json ~/dev/dagster-docs
    cp -R ./scripts ~/dev/dagster-docs
    cp -R ./src ~/dev/dagster-docs
    pushd ~/dev/dagster-docs
    git add .
    git commit -m 'Push all'
    git push
    popd
    popd
