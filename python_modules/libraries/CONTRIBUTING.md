# Contributing Libraries
Welcome! We appreciate your interest in contributing to Dagster Integrations.
This guide outlines the steps for community members who wish to contribute to integrations to the project.

## Dagster Libraries
Dagster Libraries are integrations that can be installed separately from the main Dagster package, and provide additional functionality with external tools, services, and APIs.

Dagster Libraries may be maintained by either the **Dagster Team** or by **Dagster Community** members. Dagster libraries will include a `integration.yaml` in each subfolder, which define, among other things, the maintainer of each package.

## integration.yaml
The `integration.yaml` file must include the following:

```
name: The name of the library, which may be different than the package name
suspended: bool, if true, this integration is excluded from tests and is a candidate for removal in the future.
owner: Name of the person or company who supports this package. Dagster-supported packages will have 'Dagster' as the owner.
maintainer_type: Either dagster or community.
maintainer_email: The email address of who maintains this package.
```

## Issue Reporting
For issues or bugs with the Dagster-maintained packages, please report it in the [issue tracker](https://github.com/dagster-io/dagster/issues).
Make sure to follow the issue template and provide as much detail as possible in your report.

For issues with Community-supported packages, you may report issues to the `maintainer_email` listed in the `integration.yaml` file.

## Contributing Code
When contributing code, it's recommended to follow these steps:
1. Fork the Dagster Integrations repository to your GitHub account.
2. Create a new branch based on the `main` branch.
3. Make your code changes, ensuring to follow [Dagster's coding conventions and style guidelines](https://docs.dagster.io/community/contributing#contributing).
4. Include a `integration.yaml` file for new integrations. See the [integration.yaml](integration.yaml) section
5. Push your branch to your forked repository.
6. Create a pull request against the upstream `master` branch.

## Community Support
If you have any questions or need assistance with contributing to Dagster
Integrations, feel free to reach out to the project's community for support.
Join the [community Slack workspace](https://dagster.slack.com) to connect with us.
