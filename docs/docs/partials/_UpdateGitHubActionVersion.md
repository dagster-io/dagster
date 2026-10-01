:::tip

We recommend periodically (every 6 months or so) updating the version of the Dagster GitHub Actions in your workflow files. These actions use version tags that follow the Dagster release convention (e.g., `@v1.11.13`). You can find the [most recent Dagster release](https://github.com/dagster-io/dagster/releases) on GitHub.

:::

:::note Pinning actions to a full-length commit SHA

Some organizations require third-party actions to be pinned to a full-length commit SHA (see [GitHub's secure use policy](https://docs.github.com/en/actions/reference/security/secure-use#using-third-party-actions)). This policy applies recursively, so it also covers the third-party actions (for example `actions/checkout` and `docker/build-push-action`) that the Dagster+ actions reference internally.

Use `dagster-io/dagster-cloud-action` **v1.13.11 or later** if your organization enforces this policy. Every third-party action referenced internally by the Dagster+ actions is pinned to a full-length commit SHA as of [v1.13.11](https://github.com/dagster-io/dagster-cloud-action/releases/tag/v1.13.11). Earlier versions reference those actions by version tag, which causes workflows to fail when the policy is enforced, even if you already pin the Dagster+ action itself to a full-length SHA:

```yaml
- name: Pre-run checks
  id: prerun
  uses: dagster-io/dagster-cloud-action/actions/utils/prerun@<full-length-commit-sha> # v1.13.11
```

:::
