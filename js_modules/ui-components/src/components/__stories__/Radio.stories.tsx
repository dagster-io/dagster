import {Box} from '../Box';
import {Radio, RadioContainer, RadioGroup} from '../Radio';

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
        <RadioGroup defaultValue="london">
          <Radio value="london">London</Radio>
          <Radio value="paris">Paris</Radio>
          <Radio value="tokyo">Tokyo</Radio>
          <Radio value="pyongyang" disabled>
            Pyongyang
          </Radio>
        </RadioGroup>
      </RadioContainer>
    </div>
  );
};
