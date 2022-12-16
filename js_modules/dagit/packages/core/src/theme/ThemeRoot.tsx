import {
  Button,
  Box,
  Colors,
  ColorKey,
  resetColorTheme,
  Popover,
  setColorValue,
  useColorValue,
} from '@dagster-io/ui';
import {Sketch, Circle} from '@uiw/react-color';
import React from 'react';
import rgbHex from 'rgb-hex';
import styled from 'styled-components/macro';

export const ThemeRoot = () => {
  return (
    <div style={{margin: '32px'}}>
      <div>
        <Button onClick={resetColorTheme}>Reset Theme</Button>
      </div>
      <Box flex={{direction: 'row', wrap: 'wrap', gap: 8, alignItems: 'center'}} margin={{top: 16}}>
        {Object.keys(Colors).map((key) => {
          return <ColorRow key={key} colorKey={key as ColorKey} />;
        })}
      </Box>
    </div>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default ThemeRoot;

const ColorRow: React.FC<{colorKey: ColorKey}> = ({colorKey}) => {
  const colorValue = useColorValue(colorKey);
  const [isSwatchOpen, setIsSwatchOpen] = React.useState(false);
  const hexColor = colorValue.includes('#') ? colorValue : '#' + rgbHex(colorValue);
  return (
    <Box flex={{gap: 8, alignItems: 'center'}}>
      <div>
        <Popover
          isOpen={isSwatchOpen}
          onClose={() => setIsSwatchOpen(false)}
          content={
            <Sketch
              color={hexColor}
              onChange={(color) => {
                setColorValue(colorKey, color.hex);
              }}
            />
          }
        >
          <CircleWrapper
            onClick={() => setIsSwatchOpen(!isSwatchOpen)}
            style={{transform: 'scale(0.5)'}}
          >
            <Circle colors={[hexColor]} />
          </CircleWrapper>
        </Popover>
      </div>
      <span>{colorKey}</span>
    </Box>
  );
};

const CircleWrapper = styled.span`
  > * > * {
    width: 18px !important;
    height: 18px !important;
  }
`;
