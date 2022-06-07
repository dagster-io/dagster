import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {MenuItem} from './Menu';
import {Suggest} from './Suggest';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Suggest',
  component: Suggest,
} as Meta;

const US_STATES = [
  'Alabama',
  'Alaska',
  'Arizona',
  'Arkansas',
  'California',
  'Colorado',
  'Connecticut',
  'Delaware',
  'Florida',
  'Georgia',
  'Hawaii',
  'Idaho',
  'Illinois',
  'Indiana',
  'Iowa',
  'Kansas',
  'Kentucky',
  'Louisiana',
  'Maine',
  'Maryland',
  'Massachusetts',
  'Michigan',
  'Minnesota',
  'Mississippi',
  'Missouri',
  'Montana',
  'Nebraska',
  'Nevada',
  'New Hampshire',
  'New Jersey',
  'New Mexico',
  'New York',
  'North Carolina',
  'North Dakota',
  'Ohio',
  'Oklahoma',
  'Oregon',
  'Pennsylvania',
  'Rhode Island',
  'South Carolina',
  'South Dakota',
  'Tennessee',
  'Texas',
  'Utah',
  'Vermont',
  'Virginia',
  'Washington',
  'West Virginia',
  'Wisconsin',
  'Wyoming',
];

export const Default = () => {
  const [selectedItem, setSelectedItem] = React.useState<string>('');
  return (
    <Suggest<string>
      key="loading"
      inputProps={{
        placeholder: 'Type the name of a US state…',
        style: {width: '250px'},
      }}
      items={US_STATES}
      inputValueRenderer={(item) => item}
      itemPredicate={(query, item) => item.toLocaleLowerCase().includes(query.toLocaleLowerCase())}
      itemRenderer={(item, itemProps) => (
        <MenuItem
          active={itemProps.modifiers.active}
          onClick={(e) => itemProps.handleClick(e)}
          key={item}
          text={item}
        />
      )}
      noResults={<MenuItem disabled={true} text="No presets." />}
      onItemSelect={(item) => setSelectedItem(item)}
      selectedItem={selectedItem}
    />
  );
};
