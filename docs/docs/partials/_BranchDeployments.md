## Accessing branch deployments

Once configured, branch deployments can be accessed:

<Tabs>
  <TabItem value="From a GitHub pull request">

Every pull request in the repository contains a **View in Cloud** link, which will open a branch deployment - or a preview of the changes - in Dagster+.

![View in Cloud preview link highlighted in a GitHub pull request](/images/dagster-plus/features/branch-deployments/github-cloud-preview-link.png)

  </TabItem>
  <TabItem value="In Dagster+">

:::note

To access a branch deployment in Dagster+, you need permissions that grant you [access to branch deployments](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions#user-permissions-reference) and the code location associated with the branch deployment.

:::

You can also access branch deployments directly in Dagster+ from the **deployment switcher**:

![Highlighted branch deployment in the Dagster+ deployment switcher](/images/dagster-plus/full-deployments/deployment-switcher.png)

  </TabItem>
</Tabs>

## Changing the base deployment

The base deployment has two main purposes:

- It sets which [full deployment](/deployment/dagster-plus/deploying-code/full-deployments) is used to propagate Dagster+ managed environment variables that are scoped for branch deployments.
- It is used in the UI to [track changes](/deployment/dagster-plus/deploying-code/branch-deployments/change-tracking) to the branch deployment from its parent full deployment.

The default base for branch deployments is `prod`. To configure a different full deployment as the base, create a branch deployment using the dagster-cloud CLI (see step 3.1 above) and specify the deployment with the optional `--base-deployment-name` parameter.

## Best practices

To ensure the best experience when using branch deployments, we recommend:

- **Configuring jobs based on environment**. Dagster automatically sets [environment variables](/deployment/dagster-plus/management/environment-variables/built-in) containing deployment metadata, allowing you to parameterize jobs based on the executing environment. Use these variables in your jobs to configure things like connection credentials, databases, and so on. This practice will allow you to use branch deployments without impacting production data.
- **Creating jobs to automate output cleanup.** As branch deployments don't automatically remove the output they create, you may want to create an additional Dagster job to perform the cleanup.

## Next steps

- Learn more about [branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments)
- Learn how to [track changes on a branch deployment](/deployment/dagster-plus/deploying-code/branch-deployments/change-tracking)
