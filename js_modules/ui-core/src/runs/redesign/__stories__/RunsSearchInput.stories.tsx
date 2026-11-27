import {MockedProvider} from '@apollo/client/testing';
import {Box, Text, tokensAsStringArray} from '@dagster-io/ui-components';
import {useState} from 'react';

import {DagsterTag} from '../../RunTag';
import {RunFilterToken} from '../../RunsFilterUtils';
import {
  buildRunTagFocusMocks,
  buildRunTagValuesQueryMockedResponse,
} from '../../__fixtures__/RunTagQueries.fixtures';
import {RunsSearchInput} from '../RunsSearchInput';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunsSearchInput',
  component: RunsSearchInput,
};

const MOCKS = [
  ...buildRunTagFocusMocks({
    tagKeys: ['team', 'env'],
    values: {
      [DagsterTag.SensorName]: ['new_files_sensor'],
      [DagsterTag.User]: ['marco@dagsterlabs.com'],
    },
  }),
  buildRunTagValuesQueryMockedResponse('team', ['data', 'devrel']),
  buildRunTagValuesQueryMockedResponse('env', ['prod', 'staging']),
];

type InputTemplateProps = {
  initialTokens: RunFilterToken[];
};

const InputTemplate = ({initialTokens}: InputTemplateProps) => {
  const [tokens, setTokens] = useState(initialTokens);
  const tokenStrings = tokensAsStringArray(tokens);

  return (
    <MockedProvider mocks={MOCKS}>
      <Box flex={{direction: 'column', gap: 12}} style={{width: 640}}>
        <RunsSearchInput tokens={tokens} onChange={setTokens} />
        <Text as="div" size={12} family="mono" color="textLight">
          q[]: {tokenStrings.join(', ')}
        </Text>
      </Box>
    </MockedProvider>
  );
};

export const Empty = () => <InputTemplate initialTokens={[]} />;

export const LegacyTokens = () => (
  <InputTemplate
    initialTokens={[
      {token: 'status', value: 'FAILURE'},
      {token: 'status', value: 'CANCELED'},
      {token: 'pipeline', value: 'nightly_etl'},
      {token: 'tag', value: 'dagster/sensor_name=new_files_sensor'},
      {token: 'tag', value: 'user=marco@dagsterlabs.com'},
      {token: 'tag', value: 'team=data'},
    ]}
  />
);
