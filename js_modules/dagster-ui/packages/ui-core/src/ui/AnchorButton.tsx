// eslint-disable-next-line no-restricted-imports
import * as React from 'react';
import {AnchorButton as BlueprintAnchorButton} from '@blueprintjs/core';
import {Link, LinkProps} from 'react-router-dom';

import {StyledButton, StyledButtonText, buildColorSet} from '@dagster-io/ui-components';

type AnchorButtonProps = Omit<
  React.ComponentProps<typeof BlueprintAnchorButton>,
  'loading' | 'onClick' | 'onFocus' | 'type'
> &
  LinkProps & {
    label?: React.ReactNode;
  };

export const AnchorButton = React.forwardRef(
  (props: AnchorButtonProps, ref: React.ForwardedRef<HTMLAnchorElement>) => {
    const {children, icon, intent, outlined, rightIcon, ...rest} = props;

    const {fillColor, fillColorHover, textColor, iconColor, strokeColor, strokeColorHover} =
      React.useMemo(() => buildColorSet({intent, outlined}), [intent, outlined]);

    return (
      <StyledButton
        {...rest}
        as={Link}
        $fillColor={fillColor}
        $fillColorHover={fillColorHover}
        $strokeColor={strokeColor}
        $strokeColorHover={strokeColorHover}
        $textColor={textColor}
        $iconColor={iconColor}
        ref={ref}
      >
        {icon || null}
        {children ? <StyledButtonText>{children}</StyledButtonText> : null}
        {rightIcon || null}
      </StyledButton>
    );
  },
);

AnchorButton.displayName = 'AnchorButton';
