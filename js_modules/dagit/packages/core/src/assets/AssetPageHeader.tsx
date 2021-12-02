import {BreadcrumbProps, Breadcrumbs} from '@blueprintjs/core';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {PageHeader} from '../ui/PageHeader';
import {TagWIP} from '../ui/TagWIP';
import {Heading} from '../ui/Text';

import {useAssetView} from './useAssetView';

export const AssetPageHeader: React.FC<
  {currentPath: string[]} & Partial<React.ComponentProps<typeof PageHeader>>
> = ({currentPath, ...extra}) => {
  const [view] = useAssetView();

  const breadcrumbs = React.useMemo(() => {
    if (currentPath.length === 1 || view !== 'directory') {
      return null;
    }

    const list: BreadcrumbProps[] = [];
    currentPath.reduce((accum: string, elem: string) => {
      const href = `${accum}/${encodeURIComponent(elem)}`;
      list.push({text: elem, href});
      return href;
    }, '/instance/assets');

    return list;
  }, [currentPath, view]);

  return (
    <PageHeader
      title={
        view !== 'directory' || !breadcrumbs ? (
          <Heading>{currentPath[currentPath.length - 1]}</Heading>
        ) : (
          <Box
            flex={{alignItems: 'center', gap: 4}}
            style={{maxWidth: '600px', overflow: 'hidden'}}
          >
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
        )
      }
      tags={<TagWIP icon="asset">Asset</TagWIP>}
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
