import {Box} from './Box';
import {Spinner} from './Spinner';

interface Props {
  label: React.ReactNode;
}

export const SpinnerWithText = ({label}: Props) => {
  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
      <Spinner purpose="body-text" />
      <span>{label}</span>
    </Box>
  );
};
