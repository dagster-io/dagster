## Development

To work on the docs:

```
cd docs/next
yarn dev
```

To develop the Sphinx docs:

    make livehtml

To check for broken links, run the local server (`make livehtml`), then run:

    wget --spider -r -nd -nv -nc http://127.0.0.1:8000

You can also use [linkchecker](https://github.com/linkchecker/linkchecker/tree/htmlparser-beautifulsoup), which is much slower but friendlier.

linkchecker http://127.0.0.1:8000

## Deployment

### Before Deploying

- Make sure you have set the following env variables: `NEXT_ALGOLIA_APP_ID`, `NEXT_ALGOLIA_API_KEY`, `NEXT_ALGOLIA_ADMIN_KEY`.

### Instructions

To build and push docs for a new version (e.g. 0.8.5), in `docs` directory, run:

```
docs/build.py -v 0.8.5
```
