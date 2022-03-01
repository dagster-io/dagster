import {BreadcrumbProps, Breadcrumbs} from '@blueprintjs/core';
import {Box, ColorsWIP, PageHeader, TagWIP, Heading} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {RepositoryLink} from '../nav/RepositoryLink';
import {RepoAddress} from '../workspace/types';

type Props = {assetKey: {path: string[]}; repoAddress: RepoAddress | null} & Partial<
  React.ComponentProps<typeof PageHeader>
>;

export const AssetPageHeader: React.FC<Props> = ({assetKey, repoAddress, ...extra}) => {
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
      tags={
        repoAddress ? (
          <TagWIP icon="asset">
            Asset in <RepositoryLink repoAddress={repoAddress} />
          </TagWIP>
        ) : (
          <TagWIP icon="asset">Asset</TagWIP>
        )
      }
      {...extra}
    />
  );
};

const BreadcrumbLink = styled(Link)`
  color: ${ColorsWIP.Gray800};

  :hover,
  :active {
    color: ${ColorsWIP.Gray800};
  }
`;
