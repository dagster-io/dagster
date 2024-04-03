---
title: "Lesson 7: Creating the manifest during deployment"
module: 'dbt_dagster'
lesson: '7'
---

# Creating the manifest during deployment

To recap, our deployment failed in the last section because Dagster couldn’t find a dbt manifest file, which it needs to turn dbt models into Dagster assets. This is because we built this file by running `dbt parse` during local development. You ran this manually in Lesson 3 and improved the experience in Lesson 4. However, you'll also need to build your dbt manifest file during deployment, which will require a couple additional steps. We recommend adopting CI/CD to automate this process.

Building your manifest for your production deployment will will be needed for both open source and Dagster Cloud deployments. In this case, Dagster Cloud’s out-of-the-box `deploy.yml` GitHub Action isn’t aware that you’re also trying to deploy a dbt project with Dagster.

Since your CI/CD will be running in a fresh environment, you'll need to install dbt and run `dbt deps` before building your manifest with `dbt parse`.

To get our deployment working, we need to add a step to our GitHub Actions workflow that runs the dbt commands required to generate the `manifest.json`. Specifically, we need to run `dbt deps` and `dbt parse` in the dbt project, just like you did during local development.

1. In your Dagster project, locate the `.github/workflows` directory.
2. Open the `deploy.yml` file.
3. Locate the `Checkout for Python Executable Deploy` step, which should be on or near line 38.
4. After this step, add the following:
    
    ```yaml
    - name: Parse dbt project and package with Dagster project
      if: steps.prerun.outputs.result == 'pex-deploy'
      run: |
        pip install pip --upgrade
        pip install dbt-duckdb
        cd project-repo/analytics
        dbt deps
        dbt parse
      shell: bash
    ```
    
5. Save and commit the changes. Make sure to push them to the remote!

Once the new step is pushed to the remote, GitHub will automatically try to run a new job using the updated workflow.

At this point, your dbt project will be successfully deployed onto Dagster Cloud and you should be able to see your models in the asset graph!

{% table %}

- Successful deployment
- dbt assets in the Asset graph

---

- ![Successful deployment screen in Dagster Cloud](/images/dagster-dbt/lesson-7/successful-cloud-setup.png)
- ![dbt models in the Asset graph in Dagster Cloud](/images/dagster-dbt/lesson-7/asset-graph.png)

{% /table %}

{% callout %}
💡 **Experiencing issues?** There are two ways to deploy Dagster Cloud Serverless and we only made changes to deploy dbt with the default option, called Fast Deploys with PEX (Python Executable). If you receive an erro message to turn off Fast Deploys, GitHub Actions will skip the steps to build your dbt project. We recommend staying with Fast Deploys, if possible. If your project works locally, then the most likely issue is that the path where Dagster is looking for your manifest in production is different than that of the course. This can be solved by tinkering with where you're writing the manifest. If you'd like more support, you can reach out to the Dagster community on [Slack](https://dagster.io/slack) in the `#dagster-university` channel.
{% /callout %}
