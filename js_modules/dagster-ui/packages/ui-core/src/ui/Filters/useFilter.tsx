import {BaseTag, Colors, Icon, IconName} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';

export type FilterObject<T = any> = {
  isActive: boolean;
  activeJSX: JSX.Element;
  icon: IconName;
  name: string;
  getResults: (query: string) => {label: JSX.Element; key: string; value: any}[];
  getNoResultsPlaceholder?: (query: string) => string;
  onSelect: (selectArg: {
    value: T;
    close: () => void;
    createPortal: (element: JSX.Element) => () => void;
    clearSearch: () => void;
  }) => void;
  onUnselected?: () => void;
  isLoadingFilters?: boolean;
  menuWidth?: number | string;
};

export const FilterTag = ({
  iconName,
  label,
  onRemove,
}: {
  label: JSX.Element;
  iconName?: IconName;
  onRemove: () => void;
}) => (
  <div>
    <BaseTag
      icon={iconName ? <Icon name={iconName} color={Colors.linkDefault()} /> : undefined}
      rightIcon={
        <div onClick={onRemove} style={{cursor: 'pointer'}} tabIndex={0}>
          <Icon name="close" color={Colors.linkDefault()} />
        </div>
      }
      label={label}
      fillColor={Colors.backgroundBlue()}
      textColor={Colors.linkDefault()}
    />
  </div>
);

const FilterTagHighlightedTextSpan = styled(TruncatedTextWithFullTextOnHover)`
  color: ${Colors.textBlue()};
  font-weight: 600;
  font-size: 12px;
  max-width: 100px;
`;

export const FilterTagHighlightedText = React.forwardRef(
  (
    {
      children,
      ...rest
    }: Omit<React.ComponentProps<typeof TruncatedTextWithFullTextOnHover>, 'text'> & {
      children: string;
    },
    ref: React.ForwardedRef<HTMLDivElement>,
  ) => {
    return (
      <FilterTagHighlightedTextSpan
        text={
          <>
            {children}
            {/* The following display:none div is a hack to trick CustomTooltipProvider into showing the tooltip even if the text isn't truncated */}
            <div style={{display: 'none'}}>…</div>
          </>
        }
        tooltipStyle={LabelTooltipStyles}
        {...rest}
        tooltipText={rest.tooltipText || children}
        ref={ref}
      />
    );
  },
);

const LabelTooltipStyles = JSON.stringify({
  background: Colors.tooltipBackground(),
  color: Colors.tooltipText(),
  border: 'none',
  borderRadius: 7,
  overflow: 'hidden',
  fontSize: 12,
  padding: '5px 10px',
  transform: 'translate(-10px,-5px)',
  fontWeight: 600,
} as React.CSSProperties);
