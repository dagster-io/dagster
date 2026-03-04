import {
  ButtonChildren,
  CommonButtonProps,
  Intent,
  getButtonClassName,
} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {ReactNode, forwardRef} from 'react';
import {Link, LinkProps} from 'react-router-dom';

interface AnchorButtonProps extends CommonButtonProps, Omit<LinkProps, 'component'> {
  intent?: Intent;
  outlined?: boolean;
  label?: ReactNode;
}

export const AnchorButton = forwardRef(
  (props: AnchorButtonProps, ref: React.ForwardedRef<HTMLAnchorElement>) => {
    const {children, icon, intent, outlined, rightIcon, className, ...rest} = props;
    return (
      <Link {...rest} ref={ref} className={clsx(getButtonClassName(intent, outlined), className)}>
        <ButtonChildren left={icon} label={children} right={rightIcon} />
      </Link>
    );
  },
);

AnchorButton.displayName = 'AnchorButton';
