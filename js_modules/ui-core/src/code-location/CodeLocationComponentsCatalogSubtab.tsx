import {
  ComponentBadgeProvider,
  type RenderComponentBadge,
} from '@dagster-io/dg-docs-components/ComponentBadgeContext';
import ComponentPageContents from '@dagster-io/dg-docs-components/ComponentPageContents';
import PackagePageDetails from '@dagster-io/dg-docs-components/PackagePageDetails';
import {Contents} from '@dagster-io/dg-docs-components/types';
import {Tag} from '@dagster-io/ui-components';
import {HTMLProps, memo, useCallback, useMemo} from 'react';
import {Link} from 'react-router-dom';

import {useQuery} from '../apollo-client';
import {CODE_LOCATION_COMPONENT_TYPES_QUERY} from './CodeLocationComponentTypesQuery';
import {CodeLocationDocsPackageTree} from './CodeLocationDocsPackageTree';
import {useFeatureFlags} from '../app/useFeatureFlags';
import styles from './css/CodeLocationDocsRoot.module.css';
import {
  CodeLocationComponentTypesQuery,
  CodeLocationComponentTypesQueryVariables,
} from './types/CodeLocationComponentTypesQuery.types';
import {COMMON_COLLATOR} from '../app/Util';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface Props {
  repoAddress: RepoAddress;
  packageName?: string;
  componentName?: string;
}

// Badges the component types that opt into UI creation/editing via
// `ComponentFormConfig(editable=True)`. The tree uses a compact, icon-only tag;
// the header shows the full label.
const renderComponentBadge: RenderComponentBadge = (component, options) => {
  if (!component.isAppManaged) {
    return null;
  }
  return (
    <Tag
      intent="success"
      icon="edit"
      tooltipText="This component can be created and edited from the UI form."
    >
      {options?.compact ? undefined : 'Creatable in UI'}
    </Tag>
  );
};

// When the instance UI is gated off, components can't be created from the UI,
// so the "Creatable in UI" badge would be misleading — render nothing.
const renderNoBadge: RenderComponentBadge = () => null;

export const CodeLocationComponentsCatalogSubtab = memo(
  ({repoAddress, packageName, componentName}: Props) => {
    const {flagComponentInstanceUI} = useFeatureFlags();
    const {data, loading} = useQuery<
      CodeLocationComponentTypesQuery,
      CodeLocationComponentTypesQueryVariables
    >(CODE_LOCATION_COMPONENT_TYPES_QUERY, {
      variables: {locationName: repoAddress.location},
    });

    // ``dg-docs-components`` expects the namespaced ``Package[]`` shape with
    // a JSON-encoded schema string. We group the flat list by namespace and
    // re-stringify the parsed schema at the boundary.
    const contents: Contents | null = useMemo(() => {
      const payload = data?.componentTypesForLocationOrError;
      if (payload?.__typename !== 'ComponentTypes') {
        return null;
      }
      const byNamespace = new Map<string, Contents[number]>();
      for (const c of payload.componentTypes) {
        let pkg = byNamespace.get(c.namespace);
        if (!pkg) {
          pkg = {name: c.namespace, componentTypes: []};
          byNamespace.set(c.namespace, pkg);
        }
        pkg.componentTypes.push({
          name: c.name,
          example: c.example,
          schema: c.schema == null ? '' : JSON.stringify(c.schema),
          description: c.description ?? null,
          owners: c.owners ?? [],
          tags: c.tags ?? [],
          isAppManaged: c.isAppManaged,
        });
      }
      return Array.from(byNamespace.values()).sort((a, b) =>
        COMMON_COLLATOR.compare(a.name, b.name),
      );
    }, [data]);

    const renderLink = useCallback(
      ({key, href, children, className}: HTMLProps<HTMLAnchorElement>) => (
        <Link
          key={key}
          to={workspacePathFromAddress(repoAddress, `/components/library${href || '#'}`)}
          className={className}
        >
          {children}
        </Link>
      ),
      [repoAddress],
    );

    const componentConfig = useMemo(() => {
      if (!packageName || !componentName || !contents) {
        return null;
      }
      return (
        contents
          .find((pkg) => pkg.name === packageName)
          ?.componentTypes.find((c) => c.name === componentName) ?? null
      );
    }, [contents, packageName, componentName]);

    const mainContent = () => {
      if (!packageName || !contents) {
        return null;
      }
      if (componentName) {
        if (!componentConfig) {
          return <div className={styles.error}>Component not found</div>;
        }
        return <ComponentPageContents componentConfig={componentConfig} />;
      }

      const matchingPackage = contents.find((pkg) => pkg.name === packageName);
      if (!matchingPackage) {
        return <div className={styles.error}>Package not found</div>;
      }

      return <PackagePageDetails pkg={matchingPackage} renderLink={renderLink} />;
    };

    let pathname = '';
    if (packageName) {
      pathname = componentName
        ? `/packages/${packageName}/${componentName}`
        : `/packages/${packageName}`;
    }

    return (
      <ComponentBadgeProvider
        value={flagComponentInstanceUI ? renderComponentBadge : renderNoBadge}
      >
        <div className={styles.contentContainer}>
          <div className={styles.sidebar}>
            <CodeLocationDocsPackageTree
              loading={loading}
              contents={contents}
              repoAddress={repoAddress}
              pathname={pathname}
              linkPrefix="/components/library"
            />
          </div>
          <div className={styles.main}>{mainContent()}</div>
        </div>
      </ComponentBadgeProvider>
    );
  },
);

CodeLocationComponentsCatalogSubtab.displayName = 'CodeLocationComponentsCatalogSubtab';
