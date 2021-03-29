import {QueryResult} from '@apollo/client';
import * as React from 'react';

import {AllSchedules} from '../schedules/AllSchedules';
import {Loading} from '../ui/Loading';

import {InstanceHealthQuery} from './types/InstanceHealthQuery';

interface Props {
  queryData: QueryResult<InstanceHealthQuery>;
}

export const InstanceSchedules = React.memo((props: Props) => {
  const {queryData} = props;
  return (
    <Loading queryResult={queryData} allowStaleData={true}>
      {(data) => <AllSchedules {...data} />}
    </Loading>
  );
});
