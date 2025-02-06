import {Box, Icon, Tag, Tooltip} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {CONCURRENCY_KEY_DETAILS_QUERY} from './InstanceConcurrencyKeyInfo';
import {useQuery} from '../apollo-client';
import {
  ConcurrencyKeyDetailsQuery,
  ConcurrencyKeyDetailsQueryVariables,
} from '../instance/types/InstanceConcurrencyKeyInfo.types';

export const PoolTag = ({pool}: {pool: string}) => {
  const path = `/deployment/concurrency/${pool}`;
  const {data} = useQuery<ConcurrencyKeyDetailsQuery, ConcurrencyKeyDetailsQueryVariables>(
    CONCURRENCY_KEY_DETAILS_QUERY,
    {
      variables: {
        concurrencyKey: pool,
      },
    },
  );

  const concurrencyLimit = data?.instance.concurrencyLimit;
  return (
    <Tag intent={concurrencyLimit && concurrencyLimit.limit === null ? 'warning' : 'none'}>
      <Box flex={{gap: 4, alignItems: 'center'}}>
        <Icon name="dynamic_feed" />
        <Link to={path}>{pool}</Link>
        {concurrencyLimit && concurrencyLimit.limit === null ? (
          <Tooltip
            placement="top"
            content="This pool currently does not have any slots configured."
          >
            <Icon name="warning_outline" />
          </Tooltip>
        ) : null}
      </Box>
    </Tag>
  );
};
