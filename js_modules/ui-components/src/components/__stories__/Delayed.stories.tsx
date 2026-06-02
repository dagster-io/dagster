import {Box} from '../Box';
import {Colors} from '../Color';
import {Delayed} from '../Delayed';
import {Heading} from '../Typography';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Delayed',
  component: Delayed,
};

export const Default = () => {
  return (
    <Box flex={{direction: 'column', gap: 12}}>
      <div>Wait 5 seconds for content to appear:</div>
      <Delayed delayMsec={5000}>
        <Box background={Colors.accentBlue()} padding={20}>
          <Heading size={20} weight={500} color="textDefault">
            Hello world!
          </Heading>
        </Box>
      </Delayed>
    </Box>
  );
};
