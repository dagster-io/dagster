import {Box} from '../Box';
import {Radio, RadioContainer} from '../Radio';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Radio',
  component: Radio,
};

export const Default = () => {
  return (
    <div>
      <Box margin={{bottom: 8}}>Vacation to:</Box>
      <RadioContainer>
        <Radio name="vacation" label="London" />
        <Radio name="vacation" label="Paris" />
        <Radio name="vacation" label="Tokyo" />
        <Radio name="vacation" label="Pyongyang" disabled />
      </RadioContainer>
    </div>
  );
};
