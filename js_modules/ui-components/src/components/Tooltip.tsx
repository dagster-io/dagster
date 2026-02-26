import * as RadixTooltip from '@radix-ui/react-tooltip';
import clsx from 'clsx';

import styles from './css/Tooltip.module.css';

const placementMap: Record<PlacementType, {side: SideType; align: AlignType}> = {
  top: {side: 'top', align: 'center'},
  'top-start': {side: 'top', align: 'start'},
  'top-end': {side: 'top', align: 'end'},
  bottom: {side: 'bottom', align: 'center'},
  'bottom-start': {side: 'bottom', align: 'start'},
  'bottom-end': {side: 'bottom', align: 'end'},
  left: {side: 'left', align: 'center'},
  'left-start': {side: 'left', align: 'start'},
  'left-end': {side: 'left', align: 'end'},
  right: {side: 'right', align: 'center'},
  'right-start': {side: 'right', align: 'start'},
  'right-end': {side: 'right', align: 'end'},
};

type PlacementType =
  | 'top'
  | 'bottom'
  | 'left'
  | 'right'
  | 'top-start'
  | 'top-end'
  | 'bottom-start'
  | 'bottom-end'
  | 'left-start'
  | 'left-end'
  | 'right-start'
  | 'right-end';

type AlignType = 'start' | 'center' | 'end';
type SideType = 'top' | 'bottom' | 'left' | 'right';

interface ModifierConfig {
  offset?: {
    enabled?: boolean;
    options?: {
      offset?: [number, number];
    };
  };
  [key: string]: any;
}

interface Props {
  children: React.ReactNode;
  content: React.ReactNode;

  // Blueprint API compatibility
  placement?: PlacementType;
  position?: PlacementType; // Blueprint alias for placement
  modifiers?: ModifierConfig;
  popoverClassName?: string;
  minimal?: boolean; // Ignored but accepted for compatibility
  isOpen?: boolean; // Blueprint controlled state (alias for open)

  // Custom Dagster props
  display?: React.CSSProperties['display'];
  canShow?: boolean;

  // Radix passthrough props
  open?: boolean;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  delayDuration?: number;
  disableHoverableContent?: boolean;
}

// ============================================================================
// Placement Mapping (Blueprint → Radix)
// ============================================================================

function mapPlacementToRadix(placement?: PlacementType): {
  side: SideType;
  align: AlignType;
} {
  if (!placement) {
    return {side: 'top', align: 'center'};
  }

  return placementMap[placement] || {side: 'top', align: 'center'};
}

// ============================================================================
// Offset Extraction (Blueprint modifiers → Radix sideOffset)
// ============================================================================

function extractSideOffset(modifiers?: ModifierConfig): number {
  const defaultOffset = 8; // Blueprint default was [0, 8]

  if (!modifiers?.offset?.enabled) {
    return defaultOffset;
  }

  const offset = modifiers.offset.options?.offset;
  if (Array.isArray(offset) && offset.length >= 2) {
    return offset[1]; // Blueprint uses [skidding, distance], we want distance
  }

  return defaultOffset;
}

// ============================================================================
// Main Component
// ============================================================================

export const Tooltip = (props: Props) => {
  const {
    children,
    content,
    placement,
    position, // Blueprint alias
    modifiers,
    popoverClassName = '',
    canShow = true,
    isOpen, // Blueprint controlled state
    open,
    defaultOpen,
    onOpenChange,
    delayDuration,
    disableHoverableContent,
    minimal: _minimal, // Accepted but ignored
    ...rest
  } = props;

  // Handle canShow=false: return bare children without tooltip wrapper
  if (!canShow) {
    return <>{children}</>;
  }

  // Determine placement (position is an alias for placement in Blueprint)
  const effectivePlacement = placement || position;
  const {side, align} = mapPlacementToRadix(effectivePlacement);
  const sideOffset = extractSideOffset(modifiers);

  // Use isOpen if provided (Blueprint compatibility), otherwise use open
  const effectiveOpen = isOpen !== undefined ? isOpen : open;

  return (
    <RadixTooltip.Provider delayDuration={100}>
      <RadixTooltip.Root
        open={effectiveOpen}
        defaultOpen={defaultOpen}
        onOpenChange={onOpenChange}
        delayDuration={delayDuration}
        disableHoverableContent={disableHoverableContent}
      >
        <RadixTooltip.Trigger asChild>
          <span>{children}</span>
        </RadixTooltip.Trigger>
        <RadixTooltip.Portal>
          <RadixTooltip.Content
            {...rest}
            className={clsx(styles.tooltip, popoverClassName)}
            side={side}
            align={align}
            sideOffset={sideOffset}
            collisionPadding={8}
          >
            {content}
          </RadixTooltip.Content>
        </RadixTooltip.Portal>
      </RadixTooltip.Root>
    </RadixTooltip.Provider>
  );
};
