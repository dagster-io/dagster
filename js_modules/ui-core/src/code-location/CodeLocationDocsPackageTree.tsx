import PackageTree from '@dagster-io/dg-docs-components/PackageTree';
import {Contents} from '@dagster-io/dg-docs-components/types';
import clsx from 'clsx';
import {Link} from 'react-router-dom';

import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';
import styles from './css/CodeLocationDocsPackageTree.module.css';

interface Props {
  loading?: boolean;
  contents: Contents | null;
  repoAddress: RepoAddress;
  pathname: string;
  /** Path under the location, prepended to each href. Defaults to ``/docs``. */
  linkPrefix?: string;
}

export const CodeLocationDocsPackageTree = ({
  loading,
  contents,
  repoAddress,
  pathname,
  linkPrefix = '/docs',
}: Props) => {
  return (
    <PackageTree
      contents={contents}
      pathname={pathname}
      loading={loading}
      renderLink={({key, href, children, className, ...rest}) => {
        const url = href ? workspacePathFromAddress(repoAddress, `${linkPrefix}${href}`) : '#';
        return (
          <Link key={key} to={url} {...rest} className={clsx(styles.link, className)}>
            {children}
          </Link>
        );
      }}
    />
  );
};
