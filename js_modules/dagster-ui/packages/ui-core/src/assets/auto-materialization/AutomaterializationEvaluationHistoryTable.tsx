import {Body2, Colors, Table} from '@dagster-io/ui-components';
import React from 'react';

import {Timestamp} from '../../app/time/Timestamp';
import {TimeElapsed} from '../../runs/TimeElapsed';
import {AnchorButton} from '../../ui/AnchorButton';

export const AutomaterializationEvaluationHistoryTable = () => {
  // TODO
  return (
    <Table>
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>Status</th>
          <th>Duration</th>
          <th>Result</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            <Timestamp timestamp={{unix: 0}} />
          </td>
          <td>
            <div />
          </td>
          <td>
            <TimeElapsed startUnix={0} endUnix={10000} />
          </td>
          <td>
            <Body2 color={Colors.Gray700}>No runs launched</Body2>
          </td>
          <td>
            <AnchorButton to="/">View details</AnchorButton>
          </td>
        </tr>
      </tbody>
    </Table>
  );
};
