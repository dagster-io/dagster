import {BaseTag, Colors, Icon, IconName} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';

import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';

export type FilterObject<T = any> = {
  isActive: boolean;
  activeJSX: JSX.Element;
  icon: IconName;
  name: string;
  getResults: (query: string) => {label: JSX.Element; key: string; value: any}[];
  onSelect: (selectArg: {
    value: T;
    close: () => void;
    createPortal: (element: JSX.Element) => () => void;
    clearSearch: () => void;
  }) => void;
  onUnselected?: () => void;
  isLoadingFilters?: boolean;
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
  <div style={{display: 'inline-block', height: '24px'}}>
    <BaseTag
      icon={<Icon name={iconName} color={Colors.Link} />}
      rightIcon={
        <div onClick={onRemove} style={{cursor: 'pointer'}} tabIndex={0}>
          <Icon name="close" color={Colors.Link} />
        </div>
      }
      label={label}
      fillColor={Colors.Blue50}
      textColor={Colors.Link}
    />
  </div>
);

const FilterTagHighlightedTextSpan = styled(TruncatedTextWithFullTextOnHover)`
  color: ${Colors.Blue500};
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
  background: Colors.Blue50,
  color: Colors.Blue500,
  border: 'none',
  borderRadius: 7,
  overflow: 'hidden',
  fontSize: 12,
  padding: '5px 10px',
  transform: 'translate(-10px,-5px)',
  fontWeight: 600,
} as React.CSSProperties);
