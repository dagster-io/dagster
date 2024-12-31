import {Box, Icon, Tag, Tooltip} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {CONCURRENCY_KEY_DETAILS_QUERY} from './InstanceConcurrencyKeyInfo';
import {useQuery} from '../apollo-client';
import {
  ConcurrencyKeyDetailsQuery,
  ConcurrencyKeyDetailsQueryVariables,
} from '../instance/types/InstanceConcurrencyKeyInfo.types';

export const ConcurrencyGroupTag = ({groupName}: {groupName: string}) => {
  const groupPath = `/deployment/concurrency/${groupName}`;
  const {data} = useQuery<ConcurrencyKeyDetailsQuery, ConcurrencyKeyDetailsQueryVariables>(
    CONCURRENCY_KEY_DETAILS_QUERY,
    {
      variables: {
        concurrencyKey: groupName,
      },
    },
  );

  return (
    <Tag>
      <Box flex={{gap: 4, alignItems: 'center'}}>
        <Icon name="dynamic_feed" />
        <Link to={groupPath}>{groupName}</Link>
        {data?.instance.concurrencyLimit &&
        data.instance.concurrencyLimit.configuredLimit === undefined ? (
          <Tooltip
            placement="top"
            content="This concurrency group currently does not have any slots configured."
          >
            <Icon name="check_warning" />
          </Tooltip>
        ) : null}
      </Box>
    </Tag>
  );
};
