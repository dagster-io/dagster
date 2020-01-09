import responses
from dagster_github import github_resource
from dagster import ModeDefinition, execute_solid, solid

@responses.activate
def test_github_resource_get_installations():
    @solid(required_resource_keys={'github'})
    def github_solid(context):
        assert context.resources.github
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                'https://api.github.com/app/installations',
                status=200,
                json={},
            )
            context.resources.github.get_installations()

    result = execute_solid(
        github_solid,
        environment_dict={
            'resources': {'github': {'config': {
                    "github_app_id": 123,
                    # Do not be alarmed, this is a fake key
                    "github_app_private_rsa_key": """
-----BEGIN RSA PRIVATE KEY-----
MIICXAIBAAKBgQCqGKukO1De7zhZj6+H0qtjTkVxwTCpvKe4eCZ0FPqri0cb2JZfXJ/DgYSF6vUp
wmJG8wVQZKjeGcjDOL5UlsuusFncCzWBQ7RKNUSesmQRMSGkVb1/3j+skZ6UtW+5u09lHNsj6tQ5
1s1SPrCBkedbNf0Tp0GbMJDyR4e9T04ZZwIDAQABAoGAFijko56+qGyN8M0RVyaRAXz++xTqHBLh
3tx4VgMtrQ+WEgCjhoTwo23KMBAuJGSYnRmoBZM3lMfTKevIkAidPExvYCdm5dYq3XToLkkLv5L2
pIIVOFMDG+KESnAFV7l2c+cnzRMW0+b6f8mR1CJzZuxVLL6Q02fvLi55/mbSYxECQQDeAw6fiIQX
GukBI4eMZZt4nscy2o12KyYner3VpoeE+Np2q+Z3pvAMd/aNzQ/W9WaI+NRfcxUJrmfPwIGm63il
AkEAxCL5HQb2bQr4ByorcMWm/hEP2MZzROV73yF41hPsRC9m66KrheO9HPTJuo3/9s5p+sqGxOlF
L0NDt4SkosjgGwJAFklyR1uZ/wPJjj611cdBcztlPdqoxssQGnh85BzCj/u3WqBpE2vjvyyvyI5k
X6zk7S0ljKtt2jny2+00VsBerQJBAJGC1Mg5Oydo5NwD6BiROrPxGo2bpTbu/fhrT8ebHkTz2epl
U9VQQSQzY1oZMVX8i1m5WUTLPz2yLJIBQVdXqhMCQBGoiuSoSjafUhV7i1cEGpb88h5NBYZzWXGZ
37sJ5QsW+sJyoNde3xH8vdXhzU7eT82D6X/scw9RZz+/6rCJ4p0=
-----END RSA PRIVATE KEY-----""",
                    "github_installation_id": 123,
                }}}
        },
        mode_def=ModeDefinition(resource_defs={'github': github_resource}),
    )
    assert result.success

@responses.activate
def test_github_resource_create_issue():
    @solid(required_resource_keys={'github'})
    def github_solid(context):
        assert context.resources.github
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                'https://api.github.com/app/installations/123/access_tokens',
                status=201,
                json={
                    'token': 'fake_token',
                    'expires_at': '2016-07-11T22:14:10Z',
                },
            )
            rsps.add(
                rsps.POST,
                'https://api.github.com/graphql',
                status=200,
                json={
                    'data': {
                        'repository': {
                            'id': 123
                        }
                    },
                },
            )
            rsps.add(
                rsps.POST,
                'https://api.github.com/graphql',
                status=200,
                json={},
            )
            context.resources.github.create_issue(
                repo_name="dagster",
                repo_owner="dagster-io",
                title="test",
                body="body",
            )

    result = execute_solid(
        github_solid,
        environment_dict={
            'resources': {'github': {'config': {
                    "github_app_id": 123,
                    # Do not be alarmed, this is a fake key
                    "github_app_private_rsa_key": """
-----BEGIN RSA PRIVATE KEY-----
MIICXAIBAAKBgQCqGKukO1De7zhZj6+H0qtjTkVxwTCpvKe4eCZ0FPqri0cb2JZfXJ/DgYSF6vUp
wmJG8wVQZKjeGcjDOL5UlsuusFncCzWBQ7RKNUSesmQRMSGkVb1/3j+skZ6UtW+5u09lHNsj6tQ5
1s1SPrCBkedbNf0Tp0GbMJDyR4e9T04ZZwIDAQABAoGAFijko56+qGyN8M0RVyaRAXz++xTqHBLh
3tx4VgMtrQ+WEgCjhoTwo23KMBAuJGSYnRmoBZM3lMfTKevIkAidPExvYCdm5dYq3XToLkkLv5L2
pIIVOFMDG+KESnAFV7l2c+cnzRMW0+b6f8mR1CJzZuxVLL6Q02fvLi55/mbSYxECQQDeAw6fiIQX
GukBI4eMZZt4nscy2o12KyYner3VpoeE+Np2q+Z3pvAMd/aNzQ/W9WaI+NRfcxUJrmfPwIGm63il
AkEAxCL5HQb2bQr4ByorcMWm/hEP2MZzROV73yF41hPsRC9m66KrheO9HPTJuo3/9s5p+sqGxOlF
L0NDt4SkosjgGwJAFklyR1uZ/wPJjj611cdBcztlPdqoxssQGnh85BzCj/u3WqBpE2vjvyyvyI5k
X6zk7S0ljKtt2jny2+00VsBerQJBAJGC1Mg5Oydo5NwD6BiROrPxGo2bpTbu/fhrT8ebHkTz2epl
U9VQQSQzY1oZMVX8i1m5WUTLPz2yLJIBQVdXqhMCQBGoiuSoSjafUhV7i1cEGpb88h5NBYZzWXGZ
37sJ5QsW+sJyoNde3xH8vdXhzU7eT82D6X/scw9RZz+/6rCJ4p0=
-----END RSA PRIVATE KEY-----""",
                    "github_installation_id": 123,
                }}}
        },
        mode_def=ModeDefinition(resource_defs={'github': github_resource}),
    )
    assert result.success

@responses.activate
def test_github_resource_execute():
    @solid(required_resource_keys={'github'})
    def github_solid(context):
        assert context.resources.github
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                'https://api.github.com/app/installations/123/access_tokens',
                status=201,
                json={
                    'token': 'fake_token',
                    'expires_at': '2016-07-11T22:14:10Z',
                },
            )
            rsps.add(
                rsps.POST,
                'https://api.github.com/graphql',
                status=200,
                json={
                    'data': {
                        'repository': {
                            'id': 123
                        }
                    },
                },
            )
            context.resources.github.execute(
                query="""
                query get_repo_id($repo_name: String!, $repo_owner: String!) {
                    repository(name: $repo_name, owner: $repo_owner) {
                        id
                    }
                }""",
                variables={"repo_name": "dagster", "repo_owner": "dagster-io"}
            )

    result = execute_solid(
        github_solid,
        environment_dict={
            'resources': {'github': {'config': {
                    "github_app_id": 123,
                    # Do not be alarmed, this is a fake key
                    "github_app_private_rsa_key": """
-----BEGIN RSA PRIVATE KEY-----
MIICXAIBAAKBgQCqGKukO1De7zhZj6+H0qtjTkVxwTCpvKe4eCZ0FPqri0cb2JZfXJ/DgYSF6vUp
wmJG8wVQZKjeGcjDOL5UlsuusFncCzWBQ7RKNUSesmQRMSGkVb1/3j+skZ6UtW+5u09lHNsj6tQ5
1s1SPrCBkedbNf0Tp0GbMJDyR4e9T04ZZwIDAQABAoGAFijko56+qGyN8M0RVyaRAXz++xTqHBLh
3tx4VgMtrQ+WEgCjhoTwo23KMBAuJGSYnRmoBZM3lMfTKevIkAidPExvYCdm5dYq3XToLkkLv5L2
pIIVOFMDG+KESnAFV7l2c+cnzRMW0+b6f8mR1CJzZuxVLL6Q02fvLi55/mbSYxECQQDeAw6fiIQX
GukBI4eMZZt4nscy2o12KyYner3VpoeE+Np2q+Z3pvAMd/aNzQ/W9WaI+NRfcxUJrmfPwIGm63il
AkEAxCL5HQb2bQr4ByorcMWm/hEP2MZzROV73yF41hPsRC9m66KrheO9HPTJuo3/9s5p+sqGxOlF
L0NDt4SkosjgGwJAFklyR1uZ/wPJjj611cdBcztlPdqoxssQGnh85BzCj/u3WqBpE2vjvyyvyI5k
X6zk7S0ljKtt2jny2+00VsBerQJBAJGC1Mg5Oydo5NwD6BiROrPxGo2bpTbu/fhrT8ebHkTz2epl
U9VQQSQzY1oZMVX8i1m5WUTLPz2yLJIBQVdXqhMCQBGoiuSoSjafUhV7i1cEGpb88h5NBYZzWXGZ
37sJ5QsW+sJyoNde3xH8vdXhzU7eT82D6X/scw9RZz+/6rCJ4p0=
-----END RSA PRIVATE KEY-----""",
                    "github_installation_id": 123,
                }}}
        },
        mode_def=ModeDefinition(resource_defs={'github': github_resource}),
    )
    assert result.success
