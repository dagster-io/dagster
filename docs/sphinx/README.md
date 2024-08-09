# Dagster API Documentation

This directory contains the Sphinx documentation for the Dagster API.
The core API documentation is created in `index.rst` and the files in `sections/api/apidocs`.

There are currently two workflows for generating the API documentation:

- The existing workflow uses tox to generate JSON output that is read by our NextJS
site. Running tox or `make json` will generate JSON output
- The new workflow uses Sphinx to generate HTML output. You can run `make html`
to generate HTML output, and view the static site by opening `build/html/index.html`.

## Development

Run `make install` to install the necessary dependencies for building the documentation.

You can run `make watch` to watch for changes to the API documentation and automatically rebuild the documentation.
Note: some changes might not be reflected immediately, for example style-sheets. 
You can run `make clean` and `make html` to force a full rebuild.
