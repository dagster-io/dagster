import {QueryResult} from '@apollo/client';
import * as React from 'react';

import {AllSensors} from '../sensors/AllSensors';
import {Loading} from '../ui/Loading';

import {InstanceHealthQuery} from './types/InstanceHealthQuery';

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
