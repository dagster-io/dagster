import {Box, Text, tokensAsStringArray} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import {useState} from 'react';

import {RunFilterToken} from '../../RunsFilterUtils';
import {RunsDateRangeSelect} from '../RunsDateRangeSelect';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunsDateRangeSelect',
  component: RunsDateRangeSelect,
};

type SelectTemplateProps = {
  initialTokens: RunFilterToken[];
};

const SelectTemplate = ({initialTokens}: SelectTemplateProps) => {
  const [tokens, setTokens] = useState(initialTokens);

  return (
    <Box flex={{direction: 'column', gap: 12, alignItems: 'flex-start'}}>
      <RunsDateRangeSelect tokens={tokens} onChange={setTokens} />
      <Text as="div" size={12} family="mono" color="textLight">
        q[]: {tokensAsStringArray(tokens).join(', ')}
      </Text>
    </Box>
  );
};

export const AllTime = () => <SelectTemplate initialTokens={[]} />;

export const Preset = () => (
  <SelectTemplate
    initialTokens={[{token: 'created_date_after', value: `${dayjs().startOf('day').unix()}`}]}
  />
);

export const Range = () => (
  <SelectTemplate
    initialTokens={[
      {token: 'created_date_after', value: '1772344800'},
      {token: 'created_date_before', value: '1772777999.999'},
    ]}
  />
);
