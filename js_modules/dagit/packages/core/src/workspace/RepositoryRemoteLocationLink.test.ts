import {formatRepositoryUrl} from './RepositoryRemoteLocationLink';

describe('formatRepositoryUrl', () => {
  it('formats GitHub and GitLab URLs as expected', () => {
    const githubHttps = formatRepositoryUrl(
      'https://github.com/dagster-io/dagster/tree/f04aaa/integration_tests/scripts',
    );
    expect(githubHttps).toBe('dagster-io/dagster@f04aaa');

    const githubHttp = formatRepositoryUrl(
      'https://github.com/dagster-io/dagster/tree/f04aaa/integration_tests/scripts',
    );
    expect(githubHttp).toBe('dagster-io/dagster@f04aaa');

    const githubRoot = formatRepositoryUrl('https://github.com/dagster-io/dagster/tree/0.9.10');
    expect(githubRoot).toBe('dagster-io/dagster@0.9.10');

    const gitlabHttps = formatRepositoryUrl(
      'https://gitlab.com/gitlab-org/gitlab/-/blob/0c153c/doc/user/project',
    );
    expect(gitlabHttps).toBe('gitlab-org/gitlab@0c153c');

    const gitlabHttp = formatRepositoryUrl(
      'http://gitlab.com/gitlab-org/gitlab/-/blob/0c153c/doc/user/project',
    );
    expect(gitlabHttp).toBe('gitlab-org/gitlab@0c153c');

    const gitlabRoot = formatRepositoryUrl('http://gitlab.com/gitlab-org/gitlab/-/tree/v14.3.3-ee');
    expect(gitlabRoot).toBe('gitlab-org/gitlab@v14.3.3-ee');
  });

  it('other URLs are unchanged', () => {
    const dagsterUrl = formatRepositoryUrl('https://dagster.io/');
    expect(dagsterUrl).toBe('https://dagster.io/');

    const nonRepoGithubUrl = formatRepositoryUrl('https://github.com/marketplace');
    expect(nonRepoGithubUrl).toBe('https://github.com/marketplace');
  });
});
