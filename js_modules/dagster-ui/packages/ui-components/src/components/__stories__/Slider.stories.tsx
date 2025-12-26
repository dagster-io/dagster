import {useState} from 'react';

import {Box} from '../Box';
import {Slider} from '../Slider';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Slider',
  component: Slider,
};

export const Sizes = () => {
  const [value, setValue] = useState(2);

  return (
    <Box flex={{direction: 'column', gap: 32}}>
      <Slider value={value} onChange={setValue} min={0} max={10} step={0.1} />
      <div style={{height: 200}}>
        <Slider
          orientation="vertical"
          min={0}
          max={10}
          step={1}
          value={value}
          onChange={setValue}
        />
      </div>
      <Slider disabled value={value} onChange={setValue} min={0} max={10} step={0.01} />
    </Box>
  );
};
