import {
  Box,
  BreadcrumbProps,
  Breadcrumbs,
  Colors,
  Heading,
  Icon,
  MiddleTruncate,
  PageHeader,
} from '@dagster-io/ui-components';
import {observeEnabled} from '@shared/app/observeEnabled';
import {
  getAssetSelectionQueryString,
  useAssetSelectionState,
} from '@shared/asset-selection/useAssetSelectionState';
import * as React from 'react';
import {Link, useLocation} from 'react-router-dom';

import styles from './css/AssetPageHeader.module.css';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {globalAssetGraphPathToString} from '../../assets/globalAssetGraphPathToString';
import {AnchorButton} from '../../ui/AnchorButton';
import {CopyIconButton} from '../../ui/CopyButton';
import {MenuLink} from '../../ui/MenuLink';

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
  const copyableString = tokenForAssetKey(assetKey);

  const location = useLocation();
  const assetSelection = getAssetSelectionQueryString(location.search);

  const breadcrumbs = React.useMemo(() => {
    const appendSelection = (href: string) => {
      if (!assetSelection) {
        return href;
      }
      const url = new URL(href, window.location.origin);
      url.searchParams.set('asset-selection', assetSelection);
      return url.pathname + url.search;
    };

    const keyPathItems: BreadcrumbProps[] = [];
    assetKey.path.reduce((accum: string, elem: string) => {
      const nextAccum = `${accum ? `${accum}/` : ''}${encodeURIComponent(elem)}`;
      let href = `/assets/${nextAccum}?view=folder`;
      if (observeEnabled()) {
        href = `/assets?asset-selection=key:"${nextAccum}/*"`;
      }
      keyPathItems.push({text: elem, href: appendSelection(href)});
      return nextAccum;
    }, '');

    const headerItems = headerBreadcrumbs.map((item) => ({
      ...item,
      href: item.href ? appendSelection(item.href) : undefined,
    }));

    return [...headerItems, ...keyPathItems];
  }, [assetKey.path, headerBreadcrumbs, assetSelection]);

  return (
    <PageHeader
      title={
        <Box flex={{alignItems: 'center', gap: 4}} style={{maxWidth: '600px'}}>
          <Title>
            <Breadcrumbs
              items={breadcrumbs}
              currentBreadcrumbRenderer={({text}) => (
                <Heading size={16} weight={600} className={styles.truncatedHeading}>
                  {typeof text === 'string' ? <MiddleTruncate text={text} /> : text}
                </Heading>
              )}
              breadcrumbRenderer={({text, href}) => {
                if (href) {
                  return (
                    <Heading size={16} weight={600} className={styles.truncatedHeading}>
                      <Link className={styles.breadcrumbLink} to={href}>
                        {typeof text === 'string' ? <MiddleTruncate text={text} /> : text}
                      </Link>
                    </Heading>
                  );
                }

                return (
                  <Heading size={16} weight={600} className={styles.truncatedHeading}>
                    {typeof text === 'string' ? <MiddleTruncate text={text} /> : text}
                  </Heading>
                );
              }}
              overflowRenderer={({text, href}) =>
                href ? <MenuLink to={href} text={text} /> : null
              }
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
