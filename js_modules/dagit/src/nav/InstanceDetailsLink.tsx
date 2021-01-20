import {gql, useQuery} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';

import {InstanceDetailSummaryQuery} from 'src/nav/types/InstanceDetailSummaryQuery';

export const InstanceDetailsLink: React.FunctionComponent = () => {
  const {data} = useQuery<InstanceDetailSummaryQuery>(INSTANCE_DETAIL_SUMMARY_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  if (!data) {
    return <span />;
  }

  return <div style={{color: Colors.GRAY5, fontSize: 10.5}}>{data.version}</div>;
};

const INSTANCE_DETAIL_SUMMARY_QUERY = gql`
  query InstanceDetailSummaryQuery {
    version
  }
`;
