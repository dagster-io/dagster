import {Box} from '../Box';
import {Colors} from '../Color';
import {ProgressBar} from '../ProgressBar';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'ProgressBar',
  component: ProgressBar,
};

export const Sizes = () => {
  return (
    <Box flex={{direction: 'column', gap: 32, alignItems: 'flex-start'}}>
      <Box padding={20} border="all">
        <Box flex={{direction: 'column', gap: 16}}>
          <ProgressBar intent="primary" value={0.1} animate={true} />
          <ProgressBar intent="primary" value={0.7} />
        </Box>
      </Box>
      <Box padding={20} border="all">
        <Box flex={{direction: 'column', gap: 16}}>
          <ProgressBar
            intent="primary"
            value={0.1}
            animate={true}
            fillColor={Colors.accentBlue()}
          />
          <ProgressBar intent="primary" value={0.7} fillColor={Colors.accentBlue()} />
        </Box>
      </Box>
    </Box>
  );
};
