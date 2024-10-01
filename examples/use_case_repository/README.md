## Use Case Repository

This repository contains a collection of use cases that demonstrate various applications and implementations using Dagster.

### Purpose

The use cases in this repository serve two main purposes:

1. They're used to populate the list of available use cases on the Dagster.io website.
2. They provide practical examples for developers and data engineers working with Dagster.

### Integration with Dagster.io

The use cases are automatically fetched from the master branch of this repository during the build process of the Dagster.io website. This ensures that the website always displays the most up-to-date examples. In `dagster-website/scripts/fetchUseCases.js` you can find the code that fetches the use cases from this repository and updates the website.

The script fetches from the master branch of this repository, so you will need to push your changes to the master branch to see them on the website.

### File Structure

Each use case consists of two main components:

1. A Markdown (.md) file: Contains the descriptive content and documentation, along with code snippets.
2. A Python (.py) file: Contains the actual implementation code as a single file.

Both files are utilized on the Dagster.io website. However, only the Python files are subject to automated testing.

The TEMPLATE.md file is used to create new use cases. The actual template lives on our external
Scout platform.

### Important Note

When updating a use case, please make sure to modify both the Markdown and Python files to maintain consistency between the documentation and the implementation.

### Local Preview

To preview your changes locally before committing, you can start a local webserver by running the following command in your terminal:

```
make webserver
```
