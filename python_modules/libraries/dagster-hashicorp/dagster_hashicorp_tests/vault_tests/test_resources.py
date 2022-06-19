from dagster_hashicorp.vault.resources import vault_resource
from dagster_hashicorp.vault.secrets import (
    ApproleAuth,
    KubernetesAuth,
    TokenAuth,
    UserpassAuth,
    Vault,
)

from dagster import build_init_resource_context
from dagster.core.test_utils import environ


def test_vault_resource_token():
    v_resource = vault_resource(
        build_init_resource_context(
            config={
                "auth_type": {"token": {"token": "s.token"}},
                "url": "localhost:8200",
                "mount_point": "secret",
            }
        )
    )

    assert type(v_resource) is Vault
    assert isinstance(v_resource.auth_type, TokenAuth)
    assert v_resource.auth_type.token == "s.token"
    assert v_resource.mount_point == "secret"
    assert v_resource.kv_engine_version == 2
    assert v_resource.verify is True


def test_vault_resource_token_diff_config():
    v_resource = vault_resource(
        build_init_resource_context(
            config={
                "auth_type": {"token": {"token": "s.token"}},
                "url": "localhost:8200",
                "mount_point": "foo",
                "kv_engine_version": 1,
                "verify": False,
            }
        )
    )

    assert type(v_resource) is Vault
    assert isinstance(v_resource.auth_type, TokenAuth)
    assert v_resource.auth_type.token == "s.token"
    assert v_resource.mount_point == "foo"
    assert v_resource.kv_engine_version == 1
    assert v_resource.verify is False


def test_vault_resource_userpass():
    v_resource = vault_resource(
        build_init_resource_context(
            config={
                "auth_type": {"userpass": {"username": "user", "password": "pass"}},
                "url": "localhost:8200",
                "mount_point": "secret",
            }
        )
    )

    assert type(v_resource) is Vault
    assert isinstance(v_resource.auth_type, UserpassAuth)
    assert v_resource.auth_type.username == "user"
    assert v_resource.auth_type.password == "pass"


def test_vault_resource_approle():
    v_resource = vault_resource(
        build_init_resource_context(
            config={
                "auth_type": {"approle": {"role_id": "role", "secret_id": "foo"}},
                "url": "localhost:8200",
                "mount_point": "secret",
            }
        )
    )

    assert type(v_resource) is Vault
    assert isinstance(v_resource.auth_type, ApproleAuth)
    assert v_resource.auth_type.role_id == "role"
    assert v_resource.auth_type.secret_id == "foo"


def test_vault_resource_resource():
    v_resource = vault_resource(
        build_init_resource_context(
            config={
                "auth_type": {"kubernetes": {"role": "role"}},
                "url": "localhost:8200",
                "mount_point": "secret",
            }
        )
    )

    assert type(v_resource) is Vault
    assert isinstance(v_resource.auth_type, KubernetesAuth)
    assert v_resource.auth_type.role == "role"


def test_vault_resource_from_env_token():
    with environ(
        {"VAULT_TOKEN": "s.token", "VAULT_ADDR": "localhost:8200", "VAULT_MOUNT_POINT": "secret"}
    ):
        v_resource = vault_resource(
            build_init_resource_context(
                config={
                    "auth_type": {"token": {"token": {"env": "VAULT_TOKEN"}}},
                    "url": {"env": "VAULT_ADDR"},
                    "mount_point": {"env": "VAULT_MOUNT_POINT"},
                }
            )
        )

        assert type(v_resource) is Vault
        assert isinstance(v_resource.auth_type, TokenAuth)
        assert v_resource.auth_type.token == "s.token"
        assert v_resource.mount_point == "secret"
        assert v_resource.kv_engine_version == 2
        assert v_resource.verify is True


def test_vault_resource_from_env_token_diff_config():
    with environ(
        {
            "VAULT_TOKEN": "s.token",
            "VAULT_ADDR": "localhost:8200",
            "VAULT_MOUNT_POINT": "secret",
            "VAULT_KV_VER": "1",
            "VAULT_VERIFY": "",
        }
    ):
        v_resource = vault_resource(
            build_init_resource_context(
                config={
                    "auth_type": {"token": {"token": {"env": "VAULT_TOKEN"}}},
                    "url": {"env": "VAULT_ADDR"},
                    "mount_point": {"env": "VAULT_MOUNT_POINT"},
                    "kv_engine_version": {"env": "VAULT_KV_VER"},
                    "verify": {"env": "VAULT_VERIFY"},
                }
            )
        )

        assert type(v_resource) is Vault
        assert isinstance(v_resource.auth_type, TokenAuth)
        assert v_resource.auth_type.token == "s.token"
        assert v_resource.mount_point == "secret"
        assert v_resource.kv_engine_version == 1
        assert v_resource.verify is False
