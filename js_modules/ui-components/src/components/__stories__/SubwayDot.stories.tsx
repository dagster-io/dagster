import {Box} from '../Box';
import {SubwayDot} from '../SubwayDot';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'SubwayDot',
  component: SubwayDot,
};

export const Default = () => {
  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <SubwayDot label="Alpha" />
      <SubwayDot label="Bravo" />
      <SubwayDot label="Charlie" />
      <SubwayDot label="Delta" />
      <SubwayDot label="Echo" />
    </Box>
  );
};

export const WithIcon = () => {
  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <SubwayDot label="Check" icon="check_circle" />
      <SubwayDot label="Error" icon="error" />
      <SubwayDot label="Star" icon="star" />
    </Box>
  );
};

export const CustomSizes = () => {
  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <SubwayDot label="Small" blobSize={16} fontSize={9} />
      <SubwayDot label="Default" />
      <SubwayDot label="Large" blobSize={36} fontSize={18} />
    </Box>
  );
};

export const CustomColor = () => {
  return (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <SubwayDot label="Red" blobColor="#CF4C49" />
      <SubwayDot label="Blue" blobColor="#0080B6" />
      <SubwayDot label="Green" blobColor="#508E74" />
    </Box>
  );
};
