import InstallUv from '@site/docs/partials/\_InstallUv.md';

<Tabs groupId="package-manager">
    <TabItem value="uv" label="uv">
        :::note Install uv
        <InstallUv />
        :::

        Ensure you have `dg` [installed globally](/guides/labs/dg) as a `uv` tool:

        <CliInvocationExample contents="uv tool install dagster-dg" />

        Now run the below command. Say yes to the prompt to run `uv sync` after scaffolding:

        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-a-uv-scaffold.txt" />

        The `dg init` command builds a project at `jaffle-platform`. Running `uv sync` after scaffolding creates a virtual environment and installs the dependencies listed in `pyproject.toml`, along with `jaffle-platform` itself as an [editable install](https://setuptools.pypa.io/en/latest/userguide/development_mode.html). Now let's enter the directory and activate the virtual environment:

        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-b-uv-scaffold.txt" />
    </TabItem>
    <TabItem value="pip" label="pip">
        Because `pip` does not support global installations, you will install `dg` inside your project virtual environment.
        We'll create and enter our project directory, initialize and activate a virtual environment, and install the `dagster-dg` package into it:
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-a-pip-scaffold.txt" />
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-b-pip-scaffold.txt" />
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-c-pip-scaffold.txt" />
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-d-pip-scaffold.txt" />
        The `dg` executable is now available via the activated virtual environment. Let's run `dg init .` to scaffold a new project. The `.` tells `dg` to scaffold the project in the current directory.
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-e-pip-scaffold.txt" />
        Finally, install the newly created project package into the virtual environment as an [editable install](https://setuptools.pypa.io/en/latest/userguide/development_mode.html):
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-f-pip-scaffold.txt" />
    </TabItem>

</Tabs>
