// eslint-disable-next-line no-restricted-imports
import {BreadcrumbProps, Breadcrumbs} from '@blueprintjs/core';
import {Box, Colors, PageHeader, Heading} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

type Props = {assetKey: {path: string[]}} & Partial<React.ComponentProps<typeof PageHeader>>;

export const AssetPageHeader: React.FC<Props> = ({assetKey, ...extra}) => {
  const breadcrumbs = React.useMemo(() => {
    if (assetKey.path.length === 1) {
      return [{text: assetKey.path[0], href: '/instance/assets'}];
    }

    const list: BreadcrumbProps[] = [];
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
        <Box flex={{alignItems: 'center', gap: 4}} style={{maxWidth: '600px', overflow: 'hidden'}}>
          <Breadcrumbs
            items={breadcrumbs}
            breadcrumbRenderer={({text, href}) => (
              <Heading>
                <BreadcrumbLink to={href || '#'}>{text}</BreadcrumbLink>
              </Heading>
            )}
            currentBreadcrumbRenderer={({text}) => <Heading>{text}</Heading>}
          />
        </Box>
      }
      {...extra}
    />
  );
};

const BreadcrumbLink = styled(Link)`
  color: ${Colors.Gray800};

  :hover,
  :active {
    color: ${Colors.Gray800};
  }
`;
