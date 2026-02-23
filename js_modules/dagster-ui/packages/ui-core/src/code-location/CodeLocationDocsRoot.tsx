import ComponentPageContents from '@dagster-io/dg-docs-components/ComponentPageContents';
import ListView from '@dagster-io/dg-docs-components/ListView';
import PackagePageDetails from '@dagster-io/dg-docs-components/PackagePageDetails';
import {Contents} from '@dagster-io/dg-docs-components/types';
import {Box} from '@dagster-io/ui-components';
import {CodeLocationPageHeader} from '@shared/code-location/CodeLocationPageHeader';
import {CodeLocationTabs} from '@shared/code-location/CodeLocationTabs';
import {memo, useContext, useMemo} from 'react';
import {Link, Redirect, useParams} from 'react-router-dom';

import {useQuery} from '../apollo-client';
import {CodeLocationDocsPackageTree} from './CodeLocationDocsPackageTree';
import {CODE_LOCATION_DOCS_QUERY} from './CodeLocationDocsQuery';
import styles from './css/CodeLocationDocsRoot.module.css';
import {
  CodeLocationDocsQuery,
  CodeLocationDocsQueryVariables,
} from './types/CodeLocationDocsQuery.types';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {repoAddressAsURLString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
}

export const CodeLocationDocsRoot = (props: Props) => {
  const params = useParams<{
    repoPath: string;
    packageName?: string;
    componentName?: string;
  }>();

  const {repoAddress} = props;
  const {locationEntries, loadingNonAssets: loading} = useContext(WorkspaceContext);
  const locationEntry = locationEntries.find((entry) => entry.name === repoAddress.location);

  if (!locationEntry) {
    if (!loading) {
      return <Redirect to="/deployment/locations" />;
    }
    return <div />;
  }

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <CodeLocationPageHeader repoAddress={repoAddress} />
      <Box padding={{horizontal: 24}} border="bottom">
        <CodeLocationTabs
          repoAddress={repoAddress}
          selectedTab="docs"
          locationEntry={locationEntry}
        />
      </Box>
      <div className={styles.contentContainer}>
        <QueryfulCodeLocationDocs
          repoAddress={repoAddress}
          packageName={params.packageName}
          componentName={params.componentName}
        />
      </div>
    </Box>
  );
};

interface QueryfulCodeLocationDocsProps {
  repoAddress: RepoAddress;
  packageName?: string;
  componentName?: string;
}
const QueryfulCodeLocationDocs = memo(
  ({repoAddress, packageName, componentName}: QueryfulCodeLocationDocsProps) => {
    const {data, loading} = useQuery<CodeLocationDocsQuery, CodeLocationDocsQueryVariables>(
      CODE_LOCATION_DOCS_QUERY,
      {
        variables: {
          repositorySelector: {
            repositoryName: repoAddress.name,
            repositoryLocationName: repoAddress.location,
          },
        },
      },
    );

    const contents = useMemo(() => {
      const repo = data?.repositoryOrError;
      if (repo?.__typename !== 'Repository') {
        return null;
      }

      const json =
        repo.locationDocsJsonOrError.__typename === 'LocationDocsJson'
          ? repo.locationDocsJsonOrError.json
          : null;

      if (typeof json === 'string') {
        try {
          return JSON.parse(json) as Contents;
        } catch (e) {
          console.error(e);
          return null;
        }
      }

      return null;
    }, [data]);

    const mainContent = () => {
      if (packageName) {
        if (componentName) {
          const componentConfig = contents
            ?.find((pkg) => pkg.name === packageName)
            ?.componentTypes.find((component) => component.name === componentName);
          if (!componentConfig) {
            return <div className={styles.error}>Component not found</div>;
          }
          return <ComponentPageContents componentConfig={componentConfig} />;
        }

        const matchingPackage = contents?.find((pkg) => pkg.name === packageName);
        if (!matchingPackage) {
          return <div className={styles.error}>Package not found</div>;
        }

        return (
          <PackagePageDetails
            pkg={matchingPackage}
            renderLink={({key, href, children, ...rest}) => {
              return (
                <Link
                  key={key}
                  to={`/locations/${repoAddressAsURLString(repoAddress)}/docs${href || '#'}`}
                  {...rest}
                >
                  {children}
                </Link>
              );
            }}
          />
        );
      }

      return (
        <ListView
          loading={loading}
          contents={contents}
          renderLink={({key, href, children, ...rest}) => {
            return (
              <Link
                key={key}
                to={`/locations/${repoAddressAsURLString(repoAddress)}/docs${href || '#'}`}
                {...rest}
              >
                {children}
              </Link>
            );
          }}
        />
      );
    };

    const pathname = packageName
      ? `/packages/${packageName}${componentName ? `/${componentName}` : ''}`
      : '';

    return (
      <>
        <div className={styles.sidebar}>
          <CodeLocationDocsPackageTree
            loading={loading}
            contents={contents}
            repoAddress={repoAddress}
            pathname={pathname}
          />
        </div>
        <div className={styles.main}>{mainContent()}</div>
      </>
    );
  },
);

QueryfulCodeLocationDocs.displayName = 'QueryfulCodeLocationDocs';
