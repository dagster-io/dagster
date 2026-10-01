import {Box} from '../Box';
import {DagsterIcon, DagsterLogo} from '../DagsterLogo';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'DagsterLogo',
  component: DagsterLogo,
};

export const Default = () => {
  return (
    <Box flex={{direction: 'column', gap: 24, alignItems: 'flex-start'}}>
      <DagsterLogo />
      <DagsterIcon />
    </Box>
  );
};

export const Reversed = () => {
  return (
    <Box flex={{direction: 'column', gap: 24, alignItems: 'flex-start'}}>
      <DagsterLogo reversed />
      <DagsterIcon reversed />
    </Box>
  );
};

export const CustomHeight = () => {
  return (
    <Box flex={{direction: 'column', gap: 24, alignItems: 'flex-start'}}>
      <h2>Height prop is 77px</h2>
      <DagsterLogo height={77} />
      <DagsterIcon height={77} />
    </Box>
  );
};
