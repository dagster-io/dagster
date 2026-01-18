from dagster_cloud_cli.config import DagsterCloudConfigDefaultsMerger
from dagster_cloud_cli.config.models import load_dagster_cloud_yaml

DAGSTER_CLOUD_YAML_NO_DEFAULTS = """
locations:
  - location_name: foo
    code_source:
      package_name: foo
    build:
      directory: foo
    working_directory: foo
    image: foo
    container_context:
      k8s:
        env_vars:
          - foo=bar
"""

K8S_DAGSTER_CLOUD_YAML = """
defaults:
  image: global-image
  build:
    directory: global-directory
    registry: my-registry.io/my-org
  container_context:
    k8s:
      env_config_map:
        - global_config_map
      env_vars:
        - global=global
      resources:
        requests:
          cpu: "1"
          memory: "1Gi"
      server_k8s_config:
        container_config:
          args:
            - hello
            - world
      volumes:
        - name: global-volume
          emptyDir:
            sizeLimit: 500Mi
      volume_mounts:
        - name: global-volume
          mount_path: /global
locations:
  - location_name: foo
    code_source:
      package_name: foo
    build:
      directory: foo
    working_directory: foo
    image: foo
    container_context:
      k8s:
        env_config_map:
          - global_config_map
          - my_config_map
        env_vars:
          - foo=foo
          - name_ref
        volume_mounts:
          - name: global-volume
            mount_path: /foo
  - location_name: bar
    code_source:
      module_name: bar
    build:
      directory: bar
    working_directory: bar
    image: bar
    container_context:
      k8s:
        env_vars:
          - bar=bar
          - global=overridden
        resources:
          requests:
            cpu: "2"
        server_k8s_config:
          container_config:
            args:
              - hello
              - steve            
"""


ECS_DAGSTER_CLOUD_YAML = """
defaults:
  image: global-image
  build:
    directory: global-directory
    registry: my-registry.io/my-org
  container_context:
    ecs:
      env_vars:
        - global=global
      run_resources:
        cpu: 1024
        memory: 4096
      run_ecs_tags:
        - key: global
          value: global
      run_sidecar_containers:
        - name: datadog
          image: public.ecr.aws/datadog/datadog:latest    
      secrets:
        - name: global
          valueFrom: "arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:token::"    
      server_resources:
        cpu: 256
        memory: 512
        replica_count: 1
      server_ecs_tags:
        - key: global
          value: global
      volumes:
        - name: global-volume
          efsVolumeConfiguration:
            fileSystemId: fs-1234
            rootDirectory: /path/to/global/data
      mount_points:
        - name: global-volume
          mount_path: /global
locations:
  - location_name: foo
    code_source:
      package_name: foo
    image: foo
    container_context:
      ecs:
        env_vars:
          - foo=foo
        run_resources:
            cpu: 2048
            memory: 8192
        run_ecs_tags:
          - key: global
            value: local
        secrets:
          - name: local
            valueFrom: "arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:footoken::"   
        server_ecs_tags:
          - key: foo
            value: foo
        run_sidecar_containers:
          - name: redis
            image: public.ecr.aws/redis/redis:latest
        volumes:
          - name: global-volume
            efsVolumeConfiguration:
              fileSystemId: fs-1234
              rootDirectory: /path/to/foo/data
          - name: local-volume
            efsVolumeConfiguration:
              fileSystemId: fs-5678
              rootDirectory: /path/to/local/data
"""


def test_merge_no_defaults():
    source_config = load_dagster_cloud_yaml(DAGSTER_CLOUD_YAML_NO_DEFAULTS)
    processed_config = DagsterCloudConfigDefaultsMerger().process(source_config)
    assert processed_config.locations[0] == source_config.locations[0]


def test_k8s_merge():
    source_config = load_dagster_cloud_yaml(K8S_DAGSTER_CLOUD_YAML)

    processed_config = DagsterCloudConfigDefaultsMerger().process(source_config)

    assert len(processed_config.locations) == 2
    foo, bar = processed_config.locations
    assert foo.location_name == "foo" and bar.location_name == "bar"
    assert foo.image == "foo" and bar.image == "bar", "scalars should be overridden"

    assert foo.build and foo.build.model_dump() == {
        "directory": "foo",
        "registry": "my-registry.io/my-org",
    }, "dict should be deep merged"
    assert foo.container_context and bar.container_context
    assert foo.container_context["k8s"]["resources"]["requests"]["cpu"] == "1"
    assert bar.container_context["k8s"]["resources"]["requests"]["cpu"] == "2"

    assert set(foo.container_context["k8s"]["env_config_map"]) == {
        "global_config_map",
        "my_config_map",
    }, "env_config_map should be merged and deduplicated"

    assert set(foo.container_context["k8s"]["env_vars"]) == {
        "global=global",
        "foo=foo",
        "name_ref",
    }, "env vars should be merged by name and unique"

    assert set(bar.container_context["k8s"]["env_vars"]) == {
        "bar=bar",
        "global=overridden",
    }, "env vars should be merged by name and unique"

    assert foo.container_context["k8s"]["volumes"] == [
        {"name": "global-volume", "emptyDir": {"sizeLimit": "500Mi"}},
    ], "volumes should be merged by name and unique"

    assert foo.container_context["k8s"]["volume_mounts"] == [
        {"name": "global-volume", "mount_path": "/foo"},
    ], "volume_mounts should be merged by name and unique"

    assert foo.container_context["k8s"]["server_k8s_config"]["container_config"]["args"] == [
        "hello",
        "world",
    ], "args should be replaced"

    assert bar.container_context["k8s"]["server_k8s_config"]["container_config"]["args"] == [
        "hello",
        "steve",
    ], "args should be replaced"


def test_ecs_merge():
    source_config = load_dagster_cloud_yaml(ECS_DAGSTER_CLOUD_YAML)

    processed_config = DagsterCloudConfigDefaultsMerger().process(source_config)

    assert len(processed_config.locations) == 1
    foo = processed_config.locations[0]
    assert foo.location_name == "foo"

    assert foo.build and foo.build.model_dump() == {
        "directory": "global-directory",
        "registry": "my-registry.io/my-org",
    }, "dict should be deep merged"

    assert foo.container_context and foo.container_context["ecs"]
    assert foo.container_context["ecs"]["run_resources"]["cpu"] == 2048
    assert foo.container_context["ecs"]["run_resources"]["memory"] == 8192

    assert set(foo.container_context["ecs"]["env_vars"]) == {
        "global=global",
        "foo=foo",
    }, "env vars should be merged by name and unique"

    assert foo.container_context["ecs"]["run_ecs_tags"] == [
        {"key": "global", "value": "local"},
    ], "run_ecs_tags should be merged by key and unique"

    assert foo.container_context["ecs"]["server_ecs_tags"] == [
        {"key": "global", "value": "global"},
        {"key": "foo", "value": "foo"},
    ], "server_ecs_tags should be merged by key and unique"

    assert len(foo.container_context["ecs"]["run_sidecar_containers"]) == 2
    assert len(foo.container_context["ecs"]["secrets"]) == 2

    assert foo.container_context["ecs"]["volumes"] == [
        {
            "name": "global-volume",
            "efsVolumeConfiguration": {
                "fileSystemId": "fs-1234",
                "rootDirectory": "/path/to/foo/data",
            },
        },
        {
            "name": "local-volume",
            "efsVolumeConfiguration": {
                "fileSystemId": "fs-5678",
                "rootDirectory": "/path/to/local/data",
            },
        },
    ], "volumes should be merged by name and unique"

    assert foo.container_context["ecs"]["mount_points"] == [
        {"name": "global-volume", "mount_path": "/global"},
    ], "mount_points should be merged by name and unique"
