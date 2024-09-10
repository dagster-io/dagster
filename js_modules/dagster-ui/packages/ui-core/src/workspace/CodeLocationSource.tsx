import {Colors, ExternalAnchorButton, Icon} from '@dagster-io/ui-components';

interface Metadata {
  key: string;
  value: string;
}

export const CodeLocationSource = ({metadata}: {metadata: Metadata[]}) => {
  const urlValue = extractRepoURL(metadata);

  if (urlValue.type === 'none') {
    return <div style={{color: Colors.textDisabled()}}>{'\u2013'}</div>;
  }

  if (urlValue.type === 'non-url') {
    return <div>{urlValue.value}</div>;
  }

  if (urlValue.type === 'unknown-url') {
    const {url} = urlValue;
    return (
      <a href={url.href} target="_blank" rel="noreferrer">
        {url.toString()}
      </a>
    );
  }

  const {type, url} = urlValue;

  return (
    <div>
      <ExternalAnchorButton
        href={url.toString()}
        icon={<Icon name={type === 'github-url' ? 'github' : 'gitlab'} />}
        rightIcon={<Icon name="open_in_new" />}
      >
        View repo
      </ExternalAnchorButton>
    </div>
  );
};

type RepoURLType =
  | {type: 'none'}
  | {type: 'non-url'; value: string}
  | {type: 'github-url'; url: URL}
  | {type: 'gitlab-url'; url: URL}
  | {type: 'unknown-url'; url: URL};

export const extractRepoURL = (metadata: Metadata[]): RepoURLType => {
  const metadataWithURL = metadata.find(({key}) => key === 'url');
  if (!metadataWithURL) {
    return {type: 'none'};
  }

  const {value} = metadataWithURL;
  let url = null;
  try {
    url = new URL(metadataWithURL.value);
  } catch (e) {
    // Not a URL. Just show the string, don't try to link it.
  }

  if (!url) {
    return {type: 'non-url', value};
  }

  const isGithub = url.hostname.includes('github.com');
  const isGitlab = url.hostname.includes('gitlab.com');

  if (isGithub) {
    return {type: 'github-url', url};
  }

  if (isGitlab) {
    return {type: 'gitlab-url', url};
  }

  return {type: 'unknown-url', url};
};

export const extractCommitHash = (metadata: Metadata[]) => {
  const metadataWithCommit = metadata.find(({key}) => key === 'commit_hash');
  return metadataWithCommit?.value || null;
};
