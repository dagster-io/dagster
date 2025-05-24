import {BaseTag, Colors, Icon, IconName} from '@dagster-io/ui-components';
import * as React from 'react';
import {useMemo} from 'react';
import styles from './useFilter.module.css';

import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {testId} from '../../testing/testId';

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
  theme = 'default',
}: {
  label: JSX.Element;
  iconName?: IconName;
  onRemove?: () => void;
  theme?: 'default' | 'cyan';
}) => {
  const {fillColor, textColor} = useMemo(() => {
    if (theme === 'default') {
      return {
        fillColor: Colors.backgroundBlue(),
        textColor: Colors.linkDefault(),
      };
    } else {
      return {
        fillColor: Colors.backgroundCyan(),
        textColor: Colors.textCyan(),
      };
    }
  }, [theme]);
  return (
    <div>
      <BaseTag
        icon={iconName ? <Icon name={iconName} color={textColor} /> : undefined}
        rightIcon={
          onRemove ? (
            <div
              onClick={onRemove}
              style={{cursor: 'pointer'}}
              tabIndex={0}
              data-testid={testId('filter-tag-remove')}
            >
              <Icon name="close" color={textColor} />
            </div>
          ) : null
        }
        label={label}
        fillColor={fillColor}
        textColor={textColor}
      />
    </div>
  );
};


export const FilterTagHighlightedText = React.forwardRef(
  (
    {
      children,
      color = Colors.textBlue(),
      ...rest
    }: Omit<React.ComponentProps<typeof TruncatedTextWithFullTextOnHover>, 'text'> & {
      children: string;
      color?: string;
    },
    ref: React.ForwardedRef<HTMLDivElement>,
  ) => {
    return (
      <TruncatedTextWithFullTextOnHover
        className={styles.filterTagHighlightedText}
        style={{color}}
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
