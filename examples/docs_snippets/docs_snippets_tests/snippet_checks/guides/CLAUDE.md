# Testing Snippet Tests

All snippet tests should be tested by navigating to:

```
cd $DAGSTER_GIT_REPO_DIR/examples/docs_snippets
```

Then running via tox:

```
tox -e docs_snapshot_update -- <path to test>
```
