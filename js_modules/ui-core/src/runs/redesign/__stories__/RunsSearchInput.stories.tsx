import {Box, Text, tokensAsStringArray} from '@dagster-io/ui-components';
import {useState} from 'react';

import {RunFilterToken} from '../../RunsFilterUtils';
import {RunsSearchInput} from '../RunsSearchInput';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunsSearchInput',
  component: RunsSearchInput,
};

type InputTemplateProps = {
  initialTokens: RunFilterToken[];
};

const InputTemplate = ({initialTokens}: InputTemplateProps) => {
  const [tokens, setTokens] = useState(initialTokens);
  const tokenStrings = tokensAsStringArray(tokens);

  return (
    <Box flex={{direction: 'column', gap: 12}} style={{width: 640}}>
      <RunsSearchInput tokens={tokens} onChange={setTokens} />
      <Text as="div" size={12} family="mono" color="textLight">
        q[]: {tokenStrings.join(', ')}
      </Text>
    </Box>
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
      {token: 'created_date_after', value: '1700000000.5'},
    ]}
  />
);
