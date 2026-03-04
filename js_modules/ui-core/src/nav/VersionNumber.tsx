import {FontFamily} from '@dagster-io/ui-components';
import styled from 'styled-components';

import {gql, useQuery} from '../apollo-client';
import {VersionNumberQuery, VersionNumberQueryVariables} from './types/VersionNumber.types';

export const VersionNumber = () => {
  const {version} = useVersionNumber();
  return (
    <Version>
      <span>{version || ' '}</span>
    </Version>
  );
};

export const useVersionNumber = () => {
  const {data, loading} = useQuery<VersionNumberQuery, VersionNumberQueryVariables>(
    VERSION_NUMBER_QUERY,
  );
  return {version: data?.version, loading: !data && loading};
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
