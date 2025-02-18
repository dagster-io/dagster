import {FontFamily} from '@dagster-io/ui-components';
import styled from 'styled-components';

import {gql, useQuery} from '../apollo-client';
import {VersionNumberQuery, VersionNumberQueryVariables} from './types/VersionNumber.types';

export const VersionNumber = () => {
  const {data} = useQuery<VersionNumberQuery, VersionNumberQueryVariables>(VERSION_NUMBER_QUERY);
  return <Version>{data?.version || <span>&nbsp;</span>}</Version>;
};

const Version = styled.div`
  font-size: 11px;
  font-family: ${FontFamily.monospace};
`;

export const VERSION_NUMBER_QUERY = gql`
  query VersionNumberQuery {
    version
  }
`;
