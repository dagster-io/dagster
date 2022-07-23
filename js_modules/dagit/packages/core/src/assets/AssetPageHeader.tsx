// eslint-disable-next-line no-restricted-imports
import {BreadcrumbProps, Breadcrumbs} from '@blueprintjs/core';
import {Box, Colors, PageHeader, Heading, Icon} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

type Props = {assetKey: {path: string[]}} & Partial<React.ComponentProps<typeof PageHeader>>;

export const AssetPageHeader: React.FC<Props> = ({assetKey, ...extra}) => {
  const breadcrumbs = React.useMemo(() => {
    const list: BreadcrumbProps[] = [{text: 'Assets', href: '/instance/assets'}];

    assetKey.path.reduce((accum: string, elem: string) => {
      const href = `${accum}/${encodeURIComponent(elem)}`;
      list.push({text: elem, href});
      return href;
    }, '/instance/assets');

    return list;
  }, [assetKey.path]);

  return (
    <PageHeader
      title={
        <Box
          flex={{alignItems: 'center', gap: 4}}
          style={{maxWidth: '600px', overflow: 'hidden', marginBottom: 4}}
        >
          <BreadcrumbsWithSlashes
            items={breadcrumbs}
            currentBreadcrumbRenderer={({text}) => <Heading>{text}</Heading>}
            breadcrumbRenderer={({text, href}) => (
              <Heading>
                <BreadcrumbLink to={href || '#'}>{text}</BreadcrumbLink>
              </Heading>
            )}
          />
        </Box>
      }
      {...extra}
    />
  );
};

export const AssetGlobalLineageLink = () => (
  <Link to="/instance/asset-groups">
    <Box flex={{gap: 4}}>
      <Icon color={Colors.Link} name="schema" />
      View global asset lineage
    </Box>
  </Link>
);

const BreadcrumbsWithSlashes = styled(Breadcrumbs)`
  & li:not(:first-child)::after {
    background: none;
    font-size: 20px;
    font-weight: bold;
    color: #5c7080;
    content: '/';
    width: 8px;
    line-height: 16px;
  }
`;

const BreadcrumbLink = styled(Link)`
  color: ${Colors.Gray800};

  :hover,
  :active {
    color: ${Colors.Gray800};
  }
`;
