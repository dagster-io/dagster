/* eslint-disable no-restricted-imports */
import * as React from 'react';
import {IPopoverProps} from '@blueprintjs/core';
import {Select as BlueprintSelect, SelectProps} from '@blueprintjs/select';

/* eslint-enable no-restricted-imports */
import deepmerge from 'deepmerge';

export const Select = <T,>(props: React.PropsWithChildren<SelectProps<T>>) => {
  const popoverProps: Partial<IPopoverProps> = {
    ...props.popoverProps,
    minimal: true,
    modifiers: deepmerge(
      {offset: {enabled: true, offset: '0, 8px'}},
      props.popoverProps?.modifiers || {},
    ),
    popoverClassName: `dagster-popover ${props.popoverProps?.className || ''}`,
  };

  return <BlueprintSelect {...props} popoverProps={popoverProps} />;
};
