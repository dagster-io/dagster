import NextLink, { LinkProps } from 'next/link';
import { format } from 'url';
import getConfig from 'next/config';

const config = getConfig();

let basePath = '';
if (config) {
  const { publicRuntimeConfig } = getConfig();
  basePath = publicRuntimeConfig.basePath || '';
}

export const VersionedLink: React.FunctionComponent<LinkProps> = ({
  children,
  ...props
}) => (
  <NextLink {...props} as={`${basePath}${format(props.href)}`}>
    {children}
  </NextLink>
);

export const VersionedImage: React.FunctionComponent<any> = ({
  src,
  ...props
}) => <img src={`${basePath}${format(src)}`} {...props} />;

export function VersionedGithubLink(props: { filePath: string; word: string }) {
  const { filePath, word } = props;
  // get version from base path
  let version = 'master';
  if (basePath) {
    let match = /\/(\d+\.\d+\.\d+).*/.exec(basePath);
    version = match ? match[1] : 'master';
  }
  return (
    <a
      href={`https://github.com/dagster-io/dagster/tree/${version}/${filePath}`}
      target="_blank"
    >
      {word}
    </a>
  );
}
