# dagit-screenshot

This is a command-line tool for the capture and management of Dagit
screenshots. It is intended to be used to automate the production of
screenshots for the Dagster docs site.

## Installation

This package depends on the Python `selenium` for browser automation, which in
turn depends on a system package `chromedriver`. On macOS, this should install
`dagit-screenshot`:

```
$ brew install chromedriver
$ xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver  # May not need to run this
$ pip install -e dagit-screenshot
```

## Usage

The core function of `dagit-screenshot` is to generate Dagit screenshot image
files from "screenshot spec" records. A screenshot spec is a JSON/YAML object
with fields specifying parameters that can be used to quasi-automatically
generate a screenshot. Specs live in a "screenshot database", which is just a
directory containing a hierarchy of YAML files, each containing multiple
screenshot specs.

Specs have the following fields. Only the `id` field requires explicit specification for all specs:

- `id`: Relative identifier for the spec, unique within the defining YAML file. The full ID of the spec is formed by joining the (extensionless) path to the defining YAML file with the relative ID. For the special name `index.yaml`, the `index` part is dropped. For example, a spec with `id` field "baz.png" stored in either `screenshots/foo/bar.yaml` or `screenshots/foo/bar/index.yaml` has the full ID `foo/bar/baz.png`. The full ID can be treated as a relative path that, when further qualified with an output root directory, specifies the path to an image file. The default output root is `next/public/images`, so by default the spec with ID `foo/bar/baz.png` corresponds to an image in `next/public/images/foo/bar/baz.png`.
- `route (optional)` Dagit route (i.e. path part of the URL) that will be loaded before taking a screenshot. Defaults to `/`.
- `workspace` (optional): path (relative to the repo root) to a python or workspace YAML file that defines the workspace that should be loaded before attempting screenshot capture. The script will pass the path to `dagit --python-file` or `dagit --workspace` (depending on file type) to load a set of Dagster definitions. This is required for screenshots generated from a local Dagit instance, can should be omitted for screenshots generated from a remote Dagit (e.g. at `demo.elementl.show`).
- `base_url (optional)`: Base url (protocol and host) of a Dagit instance to be targeted for a screenshot. Can point to a local or remote host. Defaults to `http://localhost:3000`.
- `vetted (optional)`: boolean indicating whether the current screenshot in the repo was generated using the spec.
- `steps` (optional): manual steps that the person generating the screenshot should carry out before the screenshot is taken.
- `width` (optional): width in pixels of the browser window in which the screenshot will be taken.
- `height` (optional): height in pixels of the browser window in which the screenshot will be taken.

The command line application `dagit-screenshot` is used to manage the specs.
Install `dagit-screenshot` into your environment with `pip install -e
dagit-screenshot`-- this will make the `dagit-screenshot` executable available
on your path. 

To generate the screenshot for a spec, run `dagit-screenshot capture <id>`.
This will attempt to render the specified Dagit view using the browser
automation tool [Selenium](https://www.selenium.dev). If no `steps` are
specified in the target spec, the screenshot will be automatically captured. If
`steps` were specified, after the initial Dagit view has rendered, the user
will be prompted to execute the steps and then press a key to trigger
screenshot capture. Screenshots are written by default to the output path
`next/public/images/<id>`. Note that successfully executing `dagit-screenshot
capture` will overwrite any existing image at the output path.

In addition to the core functionality of capturing screenshots, there are also
`dagit-screenshot audit` and `dagit-screenshot show`. You can learn more about
these commands by running `dagit-screenshot --help`.
