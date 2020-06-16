## Development

To develop the Sphinx docs:

    make livehtml

To check for broken links, run the local server (`make livehtml`), then run:

    wget --spider -r -nd -nv -nc http://127.0.0.1:8000

You can also use [linkchecker](https://github.com/linkchecker/linkchecker/tree/htmlparser-beautifulsoup), which is much slower but friendlier.

linkchecker http://127.0.0.1:8000

## Deployment (nextjs)

### Before Deploying

- Make sure you have set the following env variables: `NEXT_ALGOLIA_APP_ID`, `NEXT_ALGOLIA_API_KEY`, `NEXT_ALGOLIA_ADMIN_KEY`.

### Instructions

1. In `docs` directory, run:

```
NODE_ENV=production make buildnext
```

2. Update version links in `next/src/pages/versions/index.mdx`, run:

```
cd next
yarn update-version <new_version> # e.g. `yarn update-version 0.7.12`
```

3. Build the static doc site by running `make root_build` in the `docs` directory. It will generate a folder called `out` in the `docs` directory.

4. Then switch to the internal repo `dagster-docs`:

   1. Keep the `netlify.toml` file at root and the directories of the older versions
   2. Move all other files to a new folder and name it the current version, e.g. `0.7.12`. So you will see that we keep the older versions in separate folders.
   3. Copy over everything in `docs/out` to the root directory.
   4. (Optional) You can run a local http server from the root to locally verify the doc site before push.

5. Push changes in `dagster-docs`

```
git add .
git commit -m "0.7.12"
git push
```
