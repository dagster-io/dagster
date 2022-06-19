from dagster import BoolSource, Field, IntSource, Selector, StringSource, resource

from .secrets import ApproleAuth, KubernetesAuth, TokenAuth, UserpassAuth, Vault

VAULT_SOURCE_CONFIG = {
    "auth_type": Field(
        Selector(
            {
                "token": {
                    "token": Field(StringSource, is_required=False),
                    "token_path": Field(StringSource, is_required=False),
                },
                "userpass": {
                    "username": Field(StringSource, is_required=True),
                    "password": Field(StringSource, is_required=True),
                },
                "approle": {
                    "role_id": Field(StringSource, is_required=True),
                    "secret_id": Field(StringSource, is_required=True),
                },
                "kubernetes": {
                    "role": Field(StringSource, is_required=True),
                    "jwt_path": Field(
                        StringSource,
                        is_required=False,
                        default_value="/var/run/secrets/kubernetes.io/serviceaccount/token",
                    ),
                },
            }
        ),
        description="A instance of auth type.",
        is_required=True,
    ),
    "url": Field(
        StringSource,
        description="URL to Vault.",
        is_required=True,
    ),
    "mount_point": Field(
        StringSource,
        description="The “path” the method/backend was mounted on authentication.",
        is_required=False,
    ),
    "kv_engine_version": Field(
        IntSource,
        description="The version of the engine",
        is_required=False,
        default_value=2,
    ),
    "verify": Field(
        BoolSource,
        description="A value boolean to indicate whether TLS verification "
        "should be performed when sending requests to Vault.",
        is_required=False,
        default_value=True,
    ),
}


def vault_resource_factory(context):
    auth_type_select = context.resource_config["auth_type"]

    auth_type = None
    if "token" in auth_type_select:
        auth_type = TokenAuth(
            token=auth_type_select["token"].get("token"),
            token_path=auth_type_select["token"].get("token_path"),
        )
    elif "userpass" in auth_type_select:
        auth_type = UserpassAuth(
            username=auth_type_select["userpass"]["username"],
            password=auth_type_select["userpass"]["password"],
        )
    elif "approle" in auth_type_select:
        auth_type = ApproleAuth(
            role_id=auth_type_select["approle"]["role_id"],
            secret_id=auth_type_select["approle"]["secret_id"],
        )
    elif "kubernetes" in auth_type_select:
        auth_type = KubernetesAuth(
            role=auth_type_select["kubernetes"]["role"],
            jwt_path=auth_type_select["kubernetes"]["jwt_path"],
        )

    return Vault(
        auth_type=auth_type,
        url=context.resource_config["url"],
        mount_point=context.resource_config["mount_point"],
        kv_engine_version=context.resource_config["kv_engine_version"],
        verify=context.resource_config["verify"],
    )


@resource(VAULT_SOURCE_CONFIG)
def vault_resource(context):
    """Resource that gives access to HashiCorp Vault.

    The returned resource object is a wrapper on the Vault.

    Example:

        .. code-block:: python

            from dagster import build_op_context, job, op
            from dagster_hashicorp.vault import vault_resource

            @op(required_resource_keys={"vault"})
            def example_vault_op(context):
                return context.resources.vault.get_secret(
                    secret_path="secret/data/foo/bar"
                )

            @job(resource_defs={"vault": vault_resource})
            def example_job():
                example_vault_op()

            example_job.execute_in_process(
                run_config={
                    "resources": {
                        "vault": {
                            "config": {
                                "url": "localhost:8200",
                                "auth_type": {"token": {"token": "s.token"}},
                            }
                        }
                    }
                }
            )

    Note that your ops must also declare that they require this resource with
    `required_resource_keys`, or it will not be initialized for the execution of their compute
    functions.

    You may configure this resource as follows:

    .. code-block:: YAML

        resources:
          vault:
            config:
              auth_type:
                token:
                  token: "s.009900099000"
                  # Optional[str]: The vault token.
                  token_path: "/path/to/token"
                  # Optional[str]: The file with the vault token.
                userpass:
                  username: "foo"
                  # str: The vault username.
                  password: "bar"
                  # str: The vault password.
                approle:
                  role_id: "foo"
                  # str: The vault role ID.
                  secret_id: "bar"
                  # str: The vault secret ID.
                kubernetes:
                  role_id: "foo"
                  # str: The vault kubernetes role name.
                  jwt_path: "/path/to/token"
                  # str: The path to file with JWT token.
                  # Default: /var/run/secrets/kubernetes.io/serviceaccount/token
              url: "https://localhout:8200"
              # str: The Vault URL ddress
              mount_point: "secret"
              # Optional[str]: The “path” the backend was mounted on authentication.
              kv_engine_version: 2
              # Optional[str]: "The version of the engine". Default is 2.
              verify: 2
              # Optional[str]: A value boolean to indicate whether TLS verification
              # should be performed when sending requests to Vault.

    """
    return vault_resource_factory(context)
