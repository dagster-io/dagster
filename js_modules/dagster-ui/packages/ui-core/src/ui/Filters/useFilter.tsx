import {
  BaseTag,
  Icon,
  IconName,
  colorBackgroundBlue,
  colorLinkDefault,
  colorTextBlue,
  colorTooltipBackground,
  colorTooltipText,
} from '@dagster-io/ui-components';
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
  iconName: IconName;
  onRemove: () => void;
}) => (
  <div>
    <BaseTag
      icon={<Icon name={iconName} color={colorLinkDefault()} />}
      rightIcon={
        <div onClick={onRemove} style={{cursor: 'pointer'}} tabIndex={0}>
          <Icon name="close" color={colorLinkDefault()} />
        </div>
      }
      label={label}
      fillColor={colorBackgroundBlue()}
      textColor={colorLinkDefault()}
    />
  </div>
);

const FilterTagHighlightedTextSpan = styled(TruncatedTextWithFullTextOnHover)`
  color: ${colorTextBlue()};
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
        text={children}
        tooltipStyle={LabelTooltipStyles}
        {...rest}
        ref={ref}
      />
    );
  },
);

const LabelTooltipStyles = JSON.stringify({
  background: colorTooltipBackground(),
  color: colorTooltipText(),
  border: 'none',
  borderRadius: 7,
  overflow: 'hidden',
  fontSize: 12,
  padding: '5px 10px',
  transform: 'translate(-10px,-5px)',
  fontWeight: 600,
} as React.CSSProperties);
