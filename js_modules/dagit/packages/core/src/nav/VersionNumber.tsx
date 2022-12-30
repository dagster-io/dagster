import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import styled from 'styled-components/macro';

import {VersionNumberQuery} from './types/VersionNumberQuery';

export const VersionNumber = () => {
  const {data} = useQuery<VersionNumberQuery>(VERSION_NUMBER_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  return <Version>{data?.version || <span>&nbsp;</span>}</Version>;
};

const Version = styled.div`
  font-size: 11px;
`;

const VERSION_NUMBER_QUERY = gql`
  query VersionNumberQuery {
    version
  }
`;
