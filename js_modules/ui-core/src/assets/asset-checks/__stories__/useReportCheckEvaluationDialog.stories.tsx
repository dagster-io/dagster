import {MockedProvider} from '@apollo/client/testing';
import {Button} from '@dagster-io/ui-components';
import {MemoryRouter} from 'react-router-dom';

import {
  buildReportCheckAnyMutationMock,
  buildReportCheckPartitionDefinitionQueryMock,
  buildReportCheckPartitionHealthQueryMock,
  buildReportCheckPartitionedPartitionDefinitionQueryMock,
  testCheck,
  testCheckPartitioned,
} from '../__fixtures__/useReportCheckEvaluationDialog.fixtures';
import {useReportCheckEvaluationDialog} from '../useReportCheckEvaluationDialog';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Report Check Evaluation Dialog',
};

const WithButton = ({check}: {check: typeof testCheck | typeof testCheckPartitioned}) => {
  const {setIsOpen, element} = useReportCheckEvaluationDialog(check);
  return (
    <>
      <Button onClick={() => setIsOpen(true)}>Report evaluation</Button>
      {element}
    </>
  );
};

export const Default = () => (
  <MemoryRouter>
    <MockedProvider
      mocks={[buildReportCheckPartitionDefinitionQueryMock(), buildReportCheckAnyMutationMock()]}
    >
      <WithButton check={testCheck} />
    </MockedProvider>
  </MemoryRouter>
);

export const Partitioned = () => (
  <MemoryRouter>
    <MockedProvider
      mocks={[
        buildReportCheckPartitionedPartitionDefinitionQueryMock(),
        buildReportCheckPartitionHealthQueryMock(),
        buildReportCheckAnyMutationMock(),
      ]}
    >
      <WithButton check={testCheckPartitioned} />
    </MockedProvider>
  </MemoryRouter>
);
