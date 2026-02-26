import * as React from 'react';

import {Box} from '../Box';
import {Button} from '../Button';
import {Checkbox} from '../Checkbox';
import {Colors} from '../Color';
import {Icon} from '../Icon';
import {Tooltip} from '../Tooltip';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Tooltip',
  component: Tooltip,
};

export const Default = () => {
  const content = (
    <>
      View snapshot as of <strong>12cad35e</strong>
    </>
  );

  return (
    <Box flex={{direction: 'column', gap: 8, alignItems: 'flex-start'}}>
      <p style={{color: Colors.textLight()}}>
        Use the <code>Tooltip</code> component to attach additional explanations, descriptions, and
        context to controls, icons, etc.
      </p>
      <Tooltip content={content} placement="bottom">
        Tooltip Below
      </Tooltip>
      <Tooltip content={content} placement="top">
        Tooltip Above
      </Tooltip>
      <Tooltip
        content={content}
        modifiers={{offset: {enabled: true, options: {offset: [0, 16]}}}}
        placement="right"
      >
        Tooltip After, Custom Offset
      </Tooltip>
      <Tooltip
        content={
          <div style={{display: 'flex', width: 400, gap: 8}}>
            <Icon name="warning" color={Colors.accentYellow()} />
            <div>
              Wow, who would have thought you can put an entire paragraph into a tooltip? Just
              don&apos;t try to put interactable content here, they don&apos;t hold focus.
            </div>
          </div>
        }
        placement="top"
      >
        Tooltip with Block Content
      </Tooltip>
    </Box>
  );
};

export const CanShow = () => {
  const [disabled, setDisabled] = React.useState(true);
  return (
    <Box flex={{direction: 'column', alignItems: 'flex-start', gap: 12}}>
      <Checkbox
        format="switch"
        checked={disabled}
        onChange={() => setDisabled((current) => !current)}
        label="Disable button and show tooltip?"
      />
      <Tooltip content="I am a disabled button!" canShow={disabled}>
        <Button disabled={disabled}>
          {disabled ? 'Disabled button with tooltip' : 'Enabled button'}
        </Button>
      </Tooltip>
    </Box>
  );
};
