import {QueryResult} from '@apollo/client';
import * as React from 'react';

import {InstanceHealthQuery} from 'src/instance/types/InstanceHealthQuery';
import {AllSchedules} from 'src/schedules/AllSchedules';
import {Loading} from 'src/ui/Loading';

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
