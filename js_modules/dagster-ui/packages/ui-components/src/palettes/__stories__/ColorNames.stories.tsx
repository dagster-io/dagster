import {Fragment} from 'react';

import {Box} from '../../components/Box';
import {colorNameToVar} from '../colorNameToVar';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'ColorNames',
  // component: colorNameToVar,
};

const KEYS_TO_IGNORE = new Set(['BrowserColorScheme', 'BlueGradient']);

export const Default = () => {
  return (
    <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, width: '300px'}}>
      {Object.entries(colorNameToVar)
        .filter(([name]) => !KEYS_TO_IGNORE.has(name))
        .map(([name, value]) => (
          <Fragment key={name}>
            <Box flex={{direction: 'column', justifyContent: 'center', gap: 6}}>{name}</Box>
            <div style={{backgroundColor: value, height: '30px', width: '80px'}} />
          </Fragment>
        ))}
    </div>
  );
};
