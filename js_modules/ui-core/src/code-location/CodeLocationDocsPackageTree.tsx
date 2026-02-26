import PackageTree from '@dagster-io/dg-docs-components/PackageTree';
import {Contents} from '@dagster-io/dg-docs-components/types';
import clsx from 'clsx';
import {Link} from 'react-router-dom';

import {repoAddressAsURLString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import styles from './css/CodeLocationDocsPackageTree.module.css';

interface Props {
  loading?: boolean;
  contents: Contents | null;
  repoAddress: RepoAddress;
  pathname: string;
}

export const CodeLocationDocsPackageTree = ({loading, contents, repoAddress, pathname}: Props) => {
  return (
    <PackageTree
      contents={contents}
      pathname={pathname}
      loading={loading}
      renderLink={({key, href, children, className, ...rest}) => {
        const url = href ? `/locations/${repoAddressAsURLString(repoAddress)}/docs${href}` : '#';
        return (
          <Link key={key} to={url} {...rest} className={clsx(styles.link, className)}>
            {children}
          </Link>
        );
      }}
    />
  );
};
