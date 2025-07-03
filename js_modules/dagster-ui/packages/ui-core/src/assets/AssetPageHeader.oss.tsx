// eslint-disable-next-line no-restricted-imports
import {BreadcrumbProps, Breadcrumbs} from '@blueprintjs/core';
import {Box, Colors, Icon, MiddleTruncate, PageHeader, Subtitle1} from '@dagster-io/ui-components';
import * as React from 'react';
import {useContext} from 'react';
import {Link, useHistory, useLocation} from 'react-router-dom';
import {observeEnabled} from 'shared/app/observeEnabled.oss';
import {
  getAssetSelectionQueryString,
  useAssetSelectionState,
} from 'shared/asset-selection/useAssetSelectionState.oss';

import styles from './css/AssetPageHeader.module.css';
import {globalAssetGraphPathToString} from './globalAssetGraphPathToString';
import {AppContext} from '../app/AppContext';
import {AnchorButton} from '../ui/AnchorButton';
import {CopyIconButton} from '../ui/CopyButton';

type Props = Partial<React.ComponentProps<typeof PageHeader>> & {
  assetKey: {path: string[]};
  headerBreadcrumbs: BreadcrumbProps[];
  Title?: ({children}: {children: React.ReactNode}) => React.ReactNode;
  view: 'asset' | 'catalog';
};

const defaultTitleComponent = ({children}: {children: React.ReactNode}) => children;

export const AssetPageHeader = ({
  assetKey,
  headerBreadcrumbs,
  Title = defaultTitleComponent,
  view: _view,
  ...extra
}: Props) => {
  const history = useHistory();
  const {basePath} = useContext(AppContext);

  const copyableString = assetKey.path.join('/');

  const location = useLocation();
  const assetSelection = getAssetSelectionQueryString(location.search);

  const breadcrumbs = React.useMemo(() => {
    const keyPathItems: BreadcrumbProps[] = [];
    assetKey.path.reduce((accum: string, elem: string) => {
      const nextAccum = `${accum ? `${accum}/` : ''}${encodeURIComponent(elem)}`;
      let href = `/assets/${nextAccum}?view=folder`;
      if (observeEnabled()) {
        href = `/assets?asset-selection=key:"${nextAccum}/*"`;
      }
      keyPathItems.push({text: elem, href});
      return nextAccum;
    }, '');

    // Use createHref to prepend the basePath on all items. We don't have control over the
    // breadcrumb overflow rendering, and Blueprint renders the overflow items with no awareness
    // of the basePath. This allows us to render appropriate href values for the overflow items,
    // and we can then remove the basePath for individual rendered breadcrumbs, which we are
    // able to control.
    const headerItems = headerBreadcrumbs.map((item) => {
      const url = new URL(item.href ?? '', window.location.origin);
      if (assetSelection) {
        url.searchParams.set('asset-selection', assetSelection);
      }
      return {
        ...item,
        href: item.href
          ? history.createHref({pathname: url.pathname, search: url.search})
          : undefined,
      };
    });

    // Attach the filter state querystring to key path items.
    const keyPathItemsWithSearch = keyPathItems.map((item) => {
      const url = new URL(item.href ?? '', window.location.origin);
      if (assetSelection) {
        url.searchParams.set('asset-selection', assetSelection);
      }
      return {
        ...item,
        href: history.createHref({pathname: url.pathname, search: url.search}),
      };
    });

    return [...headerItems, ...keyPathItemsWithSearch];
  }, [assetKey.path, headerBreadcrumbs, assetSelection, history]);

  return (
    <PageHeader
      title={
        <Box flex={{alignItems: 'center', gap: 4}} style={{maxWidth: '600px'}}>
          <Title>
            <Breadcrumbs
              className={styles.breadcrumbsWithSlashes}
              items={breadcrumbs}
              currentBreadcrumbRenderer={({text, href}) => (
                <Subtitle1 key={href} className={styles.truncatedHeading}>
                  {typeof text === 'string' ? <MiddleTruncate text={text} /> : text}
                </Subtitle1>
              )}
              breadcrumbRenderer={({text, href}) => {
                // Strip the leading basePath. It is prepended in order to make overflow
                // items have the correct href values since we can't control the overflow
                // rendering. Here, however, we can do what we want, and we render with
                // react-router Link components that don't need the basePath.
                const pathWithoutBase = href ? href.replace(basePath, '') : '';
                return (
                  <Subtitle1 key={href} className={styles.truncatedHeading}>
                    <Link to={pathWithoutBase || '#'} className={styles.breadcrumbLink}>
                      {typeof text === 'string' ? <MiddleTruncate text={text} /> : text}
                    </Link>
                  </Subtitle1>
                );
              }}
              popoverProps={{
                minimal: true,
                modifiers: {offset: {enabled: true, options: {offset: [0, 8]}}},
                popoverClassName: 'dagster-popover',
              }}
            />
            {copyableString ? <CopyIconButton value={copyableString} /> : undefined}
          </Title>
        </Box>
      }
      {...extra}
    />
  );
};

export const AssetGlobalLineageLink = () => {
  const [assetSelection] = useAssetSelectionState();
  return (
    <Link to={globalAssetGraphPathToString({opsQuery: assetSelection, opNames: []})}>
      <Box flex={{gap: 4}}>
        <Icon color={Colors.linkDefault()} name="lineage" />
        View lineage
      </Box>
    </Link>
  );
};

export const AssetGlobalLineageButton = () => (
  <AnchorButton intent="primary" icon={<Icon name="lineage" />} to="/asset-groups">
    View asset lineage
  </AnchorButton>
);
