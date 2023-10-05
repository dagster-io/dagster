import {Body2, Box, ButtonLink, Colors, Dialog, Table, Tag} from '@dagster-io/ui-components';
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
            <StatusTag status="Complete" />
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

const StatusTag = ({
  status,
  errors,
}:
  | {status: 'Evaluating' | 'Skipped' | 'Complete'; errors?: null}
  | {
      status: 'Failure';
      errors: any;
    }) => {
  const [showErrors, setShowErrors] = React.useState(false);
  const tag = React.useMemo(() => {
    switch (status) {
      case 'Evaluating':
        return (
          <Tag intent="primary" icon="spinner">
            Evaluating
          </Tag>
        );
      case 'Skipped':
        return <Tag icon="dot">Skipped</Tag>;
      case 'Failure':
        console.log({errors});
        return (
          <Box flex={{direction: 'row', alignItems: 'center'}}>
            <Tag intent="danger" icon="dot" />
            <ButtonLink
              onClick={() => {
                setShowErrors(true);
              }}
            >
              View errors
            </ButtonLink>
          </Box>
        );
      case 'Complete':
        return <Tag intent="success" icon="dot" />;
    }
  }, []);

  return (
    <>
      {tag}
      <Dialog isOpen={showErrors}>errors</Dialog>
    </>
  );
};
