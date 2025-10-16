import {Box} from '../Box';
import {Button} from '../Button';
import {useDelayedState} from '../useDelayedState';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'useDelayedState',
};

export const Default = () => {
  const notDisabled = useDelayedState(5000);
  return (
    <Box flex={{direction: 'column', gap: 12}}>
      <div>The button will become enabled after five seconds.</div>
      <div>
        <Button disabled={!notDisabled}>Wait for it</Button>
      </div>
    </Box>
  );
};
