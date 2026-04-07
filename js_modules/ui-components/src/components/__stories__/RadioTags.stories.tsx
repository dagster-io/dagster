import {useState} from 'react';

import {Box} from '../Box';
import {RadioTags} from '../RadioTags';
import {BodySmall} from '../Text';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RadioTags',
  component: RadioTags,
};

export const Default = () => {
  const [value, setValue] = useState('all');

  return (
    <Box flex={{direction: 'column', gap: 16}} padding={16}>
      <BodySmall>Selected: {value}</BodySmall>
      <RadioTags
        name="filter"
        aria-label="Filter by status"
        options={[
          {value: 'all', label: 'All'},
          {value: 'active', label: 'Active'},
          {value: 'paused', label: 'Paused'},
          {value: 'error', label: 'Error'},
        ]}
        value={value}
        onChange={setValue}
      />
    </Box>
  );
};

export const WithIcons = () => {
  const [value, setValue] = useState('list');

  return (
    <Box flex={{direction: 'column', gap: 16}} padding={16}>
      <BodySmall>Selected: {value}</BodySmall>
      <RadioTags
        name="view"
        aria-label="View mode"
        options={[
          {value: 'list', label: 'List', icon: 'view_list'},
          {value: 'grid', label: 'Grid', icon: 'source'},
          {value: 'graph', label: 'Graph', icon: 'gantt_flat'},
        ]}
        value={value}
        onChange={setValue}
      />
    </Box>
  );
};
