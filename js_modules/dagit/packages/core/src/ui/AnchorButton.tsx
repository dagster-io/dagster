// eslint-disable-next-line no-restricted-imports
import {AnchorButton as BlueprintAnchorButton} from '@blueprintjs/core';
import {
  intentToFillColor,
  intentToStrokeColor,
  intentToTextColor,
  StyledButton,
  StyledButtonText,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link, LinkProps} from 'react-router-dom';

interface AnchorButtonProps
  extends Omit<React.ComponentProps<typeof BlueprintAnchorButton>, 'loading' | 'onClick' | 'type'>,
    LinkProps {
  label?: React.ReactNode;
}

export const AnchorButton = React.forwardRef(
  (props: AnchorButtonProps, ref: React.ForwardedRef<HTMLAnchorElement>) => {
    const {children, icon, intent, outlined, rightIcon, ...rest} = props;
    return (
      <StyledButton
        {...rest}
        as={Link}
        $fillColor={intentToFillColor(intent, outlined)}
        $strokeColor={intentToStrokeColor(intent, outlined)}
        $textColor={intentToTextColor(intent, outlined)}
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
