import {QueryResult} from '@apollo/client';
import * as React from 'react';

import {InstanceHealthQuery} from 'src/instance/types/InstanceHealthQuery';
import {AllSensors} from 'src/sensors/AllSensors';
import {Loading} from 'src/ui/Loading';

interface Props {
  queryData: QueryResult<InstanceHealthQuery>;
}

export const InstanceSensors = (props: Props) => {
  const {queryData} = props;
  return (
    <Loading queryResult={queryData} allowStaleData={true}>
      {(data) => <AllSensors {...data} />}
    </Loading>
  );
};
