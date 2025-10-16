---
title: Profiling hanging or slow code with py-spy
description: Debug slow or hanging Dagster code with py-spy.
sidebar_position: 200
---

If your Dagster code is hanging or taking longer than you expect to execute, we recommend using [py-spy](https://github.com/benfred/py-spy) to profile your code.

For hanging code, `py-spy dump` can give you a dump of each thread, which usually makes it immediately clear where the hang is happening.

For slow code, `py-spy record` can produce a file that gives you a flame graph of where the process is spending the most time. (We recommend `py-spy record -f speedscope --idle` to produce [speedscope](https://github.com/jlfwong/speedscope) profiles, and to include idle CPU time in the results.)

:::info Permissions required to run `py-spy`

`py-spy` usually requires elevated permissions in order to run.

For example, to run `py-spy` locally to understand why definitions are taking a long time to import:

```
sudo py-spy record -f speedscope --idle -- dagster definitions validate
```

:::

## Generating a `py-spy` dump for a hanging run in Kubernetes

1. Configure your Dagster deployment so that each run pod is using a security context that can run `py-spy`. Note that this gives the pod elevated permissions, so check with your cluster admins to make sure this is an acceptable change to make temporarily.

<Tabs>
    <TabItem value="oss" label="Dagster OSS">
        If you're using the Dagster Open Source Helm chart, you can configure the run launcher to launch each run with

        ```
        runLauncher:
        type: K8sRunLauncher
        config:
            k8sRunLauncher:
            runK8sConfig:
                containerConfig:
                securityContext:
                    capabilities:
                    add:
                        - SYS_PTRACE
        ```

        For more information on applying this type of configuration to your Kubernetes pod in Dagster OSS, see [Customizing your Kubernetes deployment](/deployment/oss/deployment-options/kubernetes/customizing-your-deployment#instance-level-kubernetes-configuration).
    </TabItem>
    <TabItem value="hybrid" label="Dagster+ Hybrid with Kubernetes agent">
        For example, you can set the following in your `dagster_cloud.yaml` file for your code location if you're running a Kubernetes agent to make both your code servers and run pods able to work with py-spy:

        ```
        # dagster_cloud.yaml
        locations:
        - location_name: cloud-examples
            image: dagster/dagster-cloud-examples:latest
            code_source:
            package_name: dagster_cloud_examples
            container_context:
            k8s:
                server_k8s_config: # Raw kubernetes config for code servers launched by the agent
                container_config:
                    securityContext:
                    capabilities:
                        add:
                        - SYS_PTRACE
                run_k8s_config: # Raw kubernetes config for runs launched by the agent
                container_config:
                    securityContext:
                    capabilities:
                        add:
                        - SYS_PTRACE
        ```

        For more information on applying this type of customization to your Kubernetes pod in Dagster+, see the [Kubernetes agent configuration reference](/deployment/dagster-plus/hybrid/kubernetes/configuration).
    </TabItem>

</Tabs>

:::info

For more information on running `py-spy` in Kubernetes, see [this `py-spy` guide](https://github.com/benfred/py-spy#how-do-i-run-py-spy-in-kubernetes).

:::

2.  Launch a run and wait until it hangs.
3.  Check the event logs for the run to find the run pod, then `kubectl exec` into the pod to run `py-spy`:

    ```
    kubectl exec -it <pod name here> /bin/bash
    ```

4.  Install `py-spy`, then run it:

    ```
    pip install py-spy
    py-spy dump --pid 1
    ```

    This should output a dump of what each thread in the process is doing.
