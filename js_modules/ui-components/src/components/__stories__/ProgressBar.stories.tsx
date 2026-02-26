import {useEffect, useState} from 'react';

import {Box} from '../Box';
import {Colors} from '../Color';
import {ProgressBar} from '../ProgressBar';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'ProgressBar',
  component: ProgressBar,
};

export const Sizes = () => {
  const [value, setValue] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setValue((value) => (value < 100 ? value + 1 : value));
    }, 200);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box flex={{direction: 'column', gap: 32}}>
      <Box padding={20} border="all">
        <Box flex={{direction: 'column', gap: 16}}>
          <ProgressBar value={10} animate fillColor={Colors.accentGray()} />
          <ProgressBar value={70} fillColor={Colors.accentGray()} />
        </Box>
      </Box>
      <Box padding={20} border="all">
        <Box flex={{direction: 'column', gap: 16}}>
          <ProgressBar value={10} animate />
          <ProgressBar value={70} />
        </Box>
      </Box>
      <Box padding={20} border="all">
        <Box flex={{direction: 'column', gap: 16}}>
          <ProgressBar value={value} animate fillColor={Colors.accentGreen()} />
        </Box>
      </Box>
    </Box>
  );
};
