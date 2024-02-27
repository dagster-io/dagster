---
title: "Lesson 7: Creating the manifest with GitHub Actions"
module: 'dbt_dagster'
lesson: '7'
---

# Creating the manifest with GitHub Actions

To recap, our deployment failed in the last section because Dagster couldn’t find a dbt manifest file, which it needs to turn dbt models into Dagster assets. This is because we built this file by running `dbt parse` during local development. You ran this manually in Lesson 3 and improved the experience in Lesson 4. However, Dagster Cloud’s out-of-the-box `deploy.yml` GitHub Action isn’t aware that you’re also trying to deploy a dbt project with Dagster.

To get our deployment working, we need to add a step to our GitHub Actions workflow that runs the dbt commands required to generate the `manifest.json`. Specifically, we need to run `dbt deps` and `dbt parse` in the dbt project, just like you did during local development.

1. In your Dagster project, locate the `.github/workflows` directory.
2. Open the `deploy.yml` file.
3. Locate the `Checkout for Python Executable Deploy` step, which should be on or near line 38.
4. After this step, add the following:
    
    ```bash
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
