import styled from 'styled-components';

import {Box} from '../Box';
import {Colors} from '../Color';
import {
  AlignItems,
  BorderSide,
  BorderWidth,
  FlexDirection,
  JustifyContent as JustifyContentType,
  Spacing,
} from '../types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Box',
  component: Box,
};

export const Padding = () => {
  const spacings: Spacing[] = [0, 2, 4, 8, 12, 16, 20, 24, 32, 48, 64];
  return (
    <Box flex={{direction: 'row', gap: 2}}>
      {spacings.map((spacing) => (
        <Box key={`${spacing}`} background={Colors.backgroundGray()} padding={spacing}>
          {spacing}
        </Box>
      ))}
    </Box>
  );
};

export const BorderSides = () => {
  const sides: BorderSide[] = [
    'all',
    'top-and-bottom',
    'left-and-right',
    'top',
    'right',
    'bottom',
    'left',
  ];
  const widths: BorderWidth[] = [1, 2];
  return (
    <Box flex={{direction: 'column', gap: 16}}>
      {widths.map((width) => (
        <Box flex={{direction: 'column', gap: 8}} key={`width-${width}`}>
          <div>{`Width ${width}:`}</div>
          <Box flex={{direction: 'row', gap: 8}}>
            {sides.map((side) => (
              <Box
                key={side}
                background={Colors.backgroundGray()}
                border={{side, width, color: Colors.accentBlue()}}
                padding={24}
                style={{fontSize: '12px', textTransform: 'uppercase'}}
              >
                {side}
              </Box>
            ))}
          </Box>
        </Box>
      ))}
    </Box>
  );
};

export const FlexDirections = () => {
  const directions: FlexDirection[] = ['row', 'column', 'row-reverse', 'column-reverse'];
  const alignItems: AlignItems[] = ['stretch', 'center', 'flex-start', 'flex-end'];

  return (
    <Box flex={{direction: 'column', gap: 16}}>
      <div>Flex direction:</div>
      <Box flex={{direction: 'row', gap: 24}}>
        {directions.map((direction) => (
          <Box flex={{direction: 'column', gap: 12}} key={direction}>
            <ExampleText>{direction}</ExampleText>
            <Box background={Colors.backgroundGray()} flex={{direction}} padding={8}>
              <Box padding={12} background={Colors.accentBlue()} />
              <Box padding={12} background={Colors.accentCyan()} />
              <Box padding={12} background={Colors.accentGreen()} />
              <Box padding={12} background={Colors.accentYellow()} />
              <Box padding={12} background={Colors.accentRed()} />
            </Box>
          </Box>
        ))}
      </Box>
      <div>Align items:</div>
      <Box flex={{direction: 'row', gap: 24}}>
        {alignItems.map((alignment) => (
          <Box flex={{direction: 'column', gap: 12}} key={alignment}>
            <ExampleText>{alignment}</ExampleText>
            <Box
              background={Colors.backgroundGray()}
              flex={{direction: 'row', alignItems: alignment}}
              padding={8}
            >
              <Box padding={12} background={Colors.accentBlue()} />
              <Box padding={24} background={Colors.accentCyan()} />
              <Box padding={32} background={Colors.accentGreen()} />
              <Box padding={4} background={Colors.accentYellow()} />
              <Box padding={16} background={Colors.accentRed()} />
            </Box>
          </Box>
        ))}
      </Box>
    </Box>
  );
};

export const JustifyContent = () => {
  const justifyContent: JustifyContentType[] = [
    'space-between',
    'space-around',
    'space-evenly',
    'center',
    'flex-start',
    'flex-end',
  ];

  return (
    <Box flex={{direction: 'column', gap: 16}}>
      <div>Justify content:</div>
      <Box flex={{direction: 'column', gap: 24}}>
        {justifyContent.map((option) => (
          <Box flex={{direction: 'column', gap: 12}} key={option}>
            <ExampleText>{option}</ExampleText>
            <Box
              background={Colors.backgroundGray()}
              flex={{direction: 'row', justifyContent: option}}
              padding={8}
            >
              <Box padding={12} background={Colors.accentBlue()} />
              <Box padding={12} background={Colors.accentCyan()} />
              <Box padding={12} background={Colors.accentGreen()} />
              <Box padding={12} background={Colors.accentYellow()} />
              <Box padding={12} background={Colors.accentRed()} />
            </Box>
          </Box>
        ))}
      </Box>
    </Box>
  );
};

const ExampleText = styled.span`
  font-size: 12px;
  text-transform: uppercase;
`;
