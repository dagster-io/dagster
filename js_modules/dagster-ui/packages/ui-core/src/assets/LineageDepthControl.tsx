import {Box, Button, Colors, Icon, JoinedButtons, TextInput} from '@dagster-io/ui-components';
import React, {useLayoutEffect, useState} from 'react';

export const LineageDepthControl = ({
  value,
  max,
  onChange,
}: {
  value: number;
  max: number;
  onChange: (v: number) => void;
}) => {
  const [text, setText] = useState(`${value}`);
  useLayoutEffect(() => {
    setText(`${value}`);
  }, [value]);

  // We maintain the value in a separate piece of state so the user can clear it
  // or briefly have an invalid value, and also so that the graph doesn't re-render
  // on each keystroke which could be expensive.
  const commitText = () => {
    const next = Number(text) ? Math.min(max, Number(text)) : value;
    onChange(next);
  };

  return (
    <Box flex={{gap: 8, alignItems: 'center'}}>
      Graph depth
      <JoinedButtons>
        <Button
          disabled={value <= 1}
          onClick={() => onChange(value - 1)}
          icon={<Icon name="dash" />}
        />
        <TextInput
          min={1}
          max={max}
          disabled={max <= 1}
          inputMode="numeric"
          style={{
            width: 40,
            marginLeft: -1,
            textAlign: 'center',
            height: 32,
            padding: 6,
            borderRadius: 0,
            boxShadow: 'none',
            border: `1px solid ${Colors.borderDefault()}`,
          }}
          key={value}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === 'Return' ? commitText() : undefined)}
          onBlur={() => commitText()}
        />
        <Button
          disabled={value >= max}
          onClick={() => onChange(value + 1)}
          icon={<Icon name="add" />}
        />
        <Button disabled={value >= max} onClick={() => onChange(max)}>
          All
        </Button>
      </JoinedButtons>
    </Box>
  );
};
