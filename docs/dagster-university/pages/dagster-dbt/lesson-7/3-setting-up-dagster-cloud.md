---
title: "Lesson 7: Setting up Dagster+"
module: 'dbt_dagster'
lesson: '7'
---

# Setting up Dagster+

Now that the project is set up and ready in GitHub, it’s time to move to Dagster+. To keep things simple, we’ll use a [Serverless deployment](https://docs.dagster.io/dagster-plus/deployment/serverless) to deploy our project. This option offloads managing the required infrastructure to Dagster Labs.

1. Sign up for a new [Dagster+ trial account](https://dagster.cloud/signup). Even if you already have an account, create a new one for this course. **Note:**  When you sign up for a new account, you’ll automatically begin a free trial. You won’t be charged for anything after the trial unless you enter a credit card.
2. Complete the signup flow by creating an organization and finishing your user profile.
3. When prompted to select a deployment type, click **Serverless.**
4. The next step is to add our project to Dagster+! Click the **Import a Dagster project** option and do the following:
    1. In the **Git scope** field, select the GitHub account or organization that contains your project repository.
       
       {% callout %}
       > 💡 **Don’t see the right account/organization?** You may need to install the Dagster+ GitHub app first. To do this, click **+ Add account or organization.** You’ll be redirected to GitHub to complete the setup, and then automatically sent back to Dagster+ when finished. If you’re installing within your company’s GitHub organization, you may need your company’s GitHub admin to approve the app.
       {% /callout %}
        
    2. In the **Repository** field, select the repository containing your Dagster project.
    3. Click **Deploy. Note that the deployment can take a few minutes.** Feel free to go grab a snack while you’re waiting!

---

## What happens when Dagster+ deploys code?

When Dagster deploys the code, a few things happen:

- Dagster creates a new code location for the repository in Dagster+ in the `prod` deployment
- Dagster adds two GitHub Action files to the repository:
    - `.github/workflows/deploy.yml` - This file sets up Continuous Deployment (CD) for the repository. We won’t talk through all the steps here, but a high-level summary is that every time a change is made to the `main` branch of your repository, this GitHub Action will build your Dagster project and deploy it to Dagster+.
    - `.github/workflows/branch_deployments.yml` - This file enables the use of [Branch Deployments](https://docs.dagster.io/dagster-cloud/managing-deployments/branch-deployments), a Dagster+ feature that automatically creates staging environments for your Dagster code with every pull request. We won’t work with Branch Deployments during this lesson, but we highly recommend trying them out!

---

## Checking deployment status

It looks like the deployment was completed, but it failed. If we look in the GitHub Action logs for the job, we’ll see the following error in the **Python Executable Deploy** step:

```yaml
Error: Some locations failed to load after being synced by the agent:
Error loading dagster_university: {'__typename': 'PythonError', 'message': "FileNotFoundError: [Errno 2] No such file or directory: '/venvs/3eca07cc1eb5/lib/python3.8/site-packages/working_directory/root/analytics/target/manifest.json'\n" ...
```

Your deployment failed because Dagster could not find a dbt manifest file. In the next section of this lesson, we’ll walk you through fixing this.
