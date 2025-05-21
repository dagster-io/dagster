---
title: 'Managing multiple projects and teams with Dagster+ Hybrid'
description: Manage multiple projects with Dagster+ Hybrid deployments.
sidebar_position: 300
---

In this guide, we'll cover some strategies for managing multiple projects/code bases and teams in a Dagster+ account.

You can see a working example of a Dagster project that has multiple code locations in our [cloud-examples/multi-location-project repo](https://github.com/dagster-io/cloud-examples/tree/main/multi-location-project).

## Separating code bases

:::note

In this section, repository refers to a version control system, such as Git or Mercurial.

:::

If you want to manage complexity or divide your work into areas of responsibility, consider isolating your code bases into multiple projects with:

- Multiple directories in a single repository, or
- Multiple repositories

Refer to the following table for more information, including the pros and cons of each approach.

| Approach                                        | How it works                                                                                                                                                                                                    | Pros                                                                                                                                                                                                             | Cons                                                                                                                                                                                                      |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Multiple directories in a single repository** | You can use a single repository to manage multiple projects by placing each project in a separate directory. Depending on your VCS, you may be able to set code owners to restrict who can modify each project. | <ul><li>Simple to implement</li><li>Facilitates code sharing between projects</li></ul>                                                                                                                          | <ul><li>All projects share the same CI/CD pipeline and cannot be deployed independently</li><li>Shared dependencies between projects may cause conflicts and require coordination between teams</li></ul> |
| **Multiple repositories**                       | For stronger isolation, you can use multiple repositories to manage multiple projects.                                                                                                                          | <ul><li>Stronger isolation between projects and teams</li><li>Each project has its own CI/CD pipeline and be deployed independently</li><li>Dependencies between projects can be managed independently</li></ul> | Code sharing between projects require additional coordination to publish and reuse packages between projects.                                                                                             |

### Deployment configuration

Whether you use a single repository or multiple, you can use a [`dagster_cloud.yaml` file](/dagster-plus/deployment/code-locations/dagster-cloud-yaml) to define the code locations to deploy. For each repository, follow the [steps appropriate to your CI/CD provider](/dagster-plus/features/ci-cd/configuring-ci-cd) and include only the code locations that are relevant to the repository in your CI/CD workflow.

#### Example with GitHub CI/CD on Hybrid deployment

1. **For each repository**, use the CI/CD workflow provided in [Dagster+ Hybrid quickstart repository](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart/blob/main/.github/workflows/dagster-cloud-deploy.yml).

2. **For each project in the repository**, configure a code location in the [`dagster_cloud.yaml` file](/dagster-plus/deployment/code-locations/dagster-cloud-yaml):

   ```yaml
   # dagster_cloud.yml

   locations:
     - location_name: project_a
       code_source:
         package_name: project_a
       build:
         # ...
     - location_name: project_b
       code_source:
         package_name: project_b
       build:
         # ...
   ```

3. In the repository's `dagster-cloud-deploy.yml` file, modify the CI/CD workflow to deploy all code locations for the repository:

   ```yaml
   # .github/workflows/dagster-cloud-deploy.yml

   jobs:
     dagster-cloud-deploy:
       # ...
       steps:
         - name: Update build session with image tag for "project_a" code location
           id: ci-set-build-output-project-a
           if: steps.prerun.outputs.result != 'skip'
           uses: dagster-io/dagster-cloud-action/actions/utils/dagster-cloud-cli@v0.1
           with:
             command: 'ci set-build-output --location-name=project_a --image-tag=$IMAGE_TAG'

         - name: Update build session with image tag for "project_b" code location
           id: ci-set-build-output-project-b
           if: steps.prerun.outputs.result != 'skip'
           uses: dagster-io/dagster-cloud-action/actions/utils/dagster-cloud-cli@v0.1
           with:
             command: 'ci set-build-output --location-name=project_b --image-tag=$IMAGE_TAG'
         # ...
   ```

## Isolating execution context between projects

Separating execution context between projects can have several motivations:

- Facilitating separation of duty between teams to prevent access to sensitive data
- Differing compute environments and requirements, such as different architecture, cloud provider, etc.
- Reducing impact on other projects. For example, a project with a large number of runs can impact the performance of other projects.

In order from least to most isolated, there are three levels of isolation:

- [Code location](#code-location-isolation)
- [Agent](#agent-isolation)
- [Deployment](#deployment-isolation)

### Code location isolation

If you have no specific requirements for isolation beyond the ability to deploy and run multiple projects, you can use a single agent and deployment to manage all your projects as individual code locations.

![Diagram of isolation at the code location level](/images/dagster-plus/deployment/management/managing-deployments/isolation-level-code-locations.png)

<table
  className="table"
  style={{
    width: '100%',
  }}>
  <thead>
    <tr>
      <th
        style={{
          width: '50%',
        }}>
        Pros
      </th>
      <th>Cons</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <ul
          style={{
            marginTop: '0px',
          }}>
          <li
            style={{
              marginTop: '0px',
            }}>
            Simplest and most cost-effective solution
          </li>
          <li>User access control can be set at the code location level</li>
          <li>Single glass pane to view all assets</li>
        </ul>
      </td>
      <td>
        <ul
          style={{
            marginTop: '0px',
          }}>
          <li
            style={{
              marginTop: '0px',
            }}>
            No isolation between execution environments
          </li>
        </ul>
      </td>
    </tr>
  </tbody>
</table>

### Agent isolation

:::note

Agent queues are a Dagster+ Pro feature available on hybrid deployment.

:::

Using the [agent routing feature](/dagster-plus/deployment/deployment-types/hybrid/multiple#routing-requests-to-specific-agents), you can effectively isolate execution environments between projects by using a separate agent for each project.

Motivations for utilizing this approach could include:

- Different compute requirements, such as different cloud providers or architectures
- Optimizing for locality or access, such as running the data processing closer or in environment with access to the storage locations

![Diagram of isolation at the agent level](/images/dagster-plus/deployment/management/managing-deployments/isolation-level-agents.png)

<table
  className="table"
  style={{
    width: '100%',
  }}>
  <thead>
    <tr>
      <th
        style={{
          width: '50%',
        }}>
        Pros
      </th>
      <th>Cons</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <ul
          style={{
            marginTop: '0px',
          }}>
          <li
            style={{
              marginTop: '0px',
            }}>
            Isolation between execution environments
          </li>
          <li>User access control can be set at the code location level</li>
          <li>Single glass pane to view all assets</li>
        </ul>
      </td>
      <td>Extra work to set up additional agents and agent queues</td>
    </tr>
  </tbody>
</table>

### Deployment isolation

:::note

Multiple deployments are only available in Dagster+ Pro.

:::

Of the approaches outlined in this guide, multiple deployments are the most isolated solution. The typical motivation for this isolation level is to separate production and non-production environments. It may be considered to satisfy other organization specific requirements.

![Diagram of isolation at the Dagster+ deployment level](/images/dagster-plus/deployment/management/managing-deployments/isolation-level-deployments.png)

<table
  className="table"
  style={{
    width: '100%',
  }}>
  <thead>
    <tr>
      <th
        style={{
          width: '50%',
        }}>
        Pros
      </th>
      <th>Cons</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <ul
          style={{
            marginTop: '0px',
          }}>
          <li
            style={{
              marginTop: '0px',
            }}>
            Isolation between assets and execution environments
          </li>
          <li>User access control can be set at the code location and deployment level</li>
        </ul>
      </td>
      <td>No single glass pane to view all assets (requires switching between multiple deployments in the UI)</td>
    </tr>
  </tbody>
</table>
