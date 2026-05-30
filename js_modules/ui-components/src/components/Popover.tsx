// eslint-disable-next-line no-restricted-imports
import {
  Popover as BlueprintPopover,
  PopoverProps as BlueprintPopoverProps,
} from '@blueprintjs/core';
import * as RadixPopover from '@radix-ui/react-popover';
import deepmerge from 'deepmerge';
import {useCallback, useEffect, useRef, useState} from 'react';
// Overwrite arrays instead of concatting them.
const overwriteMerge = (_destination: unknown[], source: unknown[]) => source;

/**
 * For hover interactions, we still use Blueprint Popover since Radix Popover
 * is click-only by design. Hover popovers will be migrated separately
 * (likely to Radix HoverCard or Tooltip).
 */
const BlueprintHoverPopover = (props: BlueprintPopoverProps) => {
  return (
    <BlueprintPopover
      minimal
      autoFocus={false}
      enforceFocus={false}
      {...props}
      popoverClassName={`dagster-popover ${props.popoverClassName}`}
      modifiers={deepmerge(
        {offset: {enabled: true, options: {offset: [0, 8]}}},
        props.modifiers || {},
        {arrayMerge: overwriteMerge},
      )}
    />
  );
};

// --- Radix Popover for click interactions ---

const ALIGN_MAP: Record<string, 'start' | 'end'> = {
  left: 'start',
  right: 'end',
  top: 'start',
  bottom: 'end',
  start: 'start',
  end: 'end',
};

function parsePlacement(p?: string): {
  side: 'top' | 'bottom' | 'left' | 'right';
  align: 'start' | 'center' | 'end';
} {
  if (!p || p.startsWith('auto')) {
    return {side: 'bottom', align: 'center'};
  }
  const [side, alignKey] = p.split('-');
  return {
    side: side as 'top' | 'bottom' | 'left' | 'right',
    align: alignKey ? (ALIGN_MAP[alignKey] ?? 'center') : 'center',
  };
}

const RadixClickPopover = ({
  children,
  content,
  placement: placementProp,
  position,
  isOpen: controlledOpen,
  onInteraction,
  canEscapeKeyClose = true,
  disabled = false,
  fill = false,
  modifiers,
  usePortal = true,
  className,
  popoverClassName,
  targetProps: {ref: _targetRef, ...targetProps} = {},
  targetTagName,
  onOpening,
  onOpened,
  onClosed,
  hasBackdrop = false,
  backdropProps: {ref: _backdropRef, ...backdropProps} = {},
  matchTargetWidth = false,
}: BlueprintPopoverProps) => {
  const {side, align} = parsePlacement((placementProp ?? position) as string | undefined);

  const offsetMod = modifiers?.offset as
    | {enabled: boolean; options: {offset: [number, number]}}
    | undefined;
  const [crossAxisOffset, mainAxisOffset] =
    offsetMod?.enabled && offsetMod.options?.offset ? offsetMod.options.offset : [0, 8];

  const isControlled = controlledOpen !== undefined;
  const [uncontrolledOpen, setUncontrolledOpen] = useState(false);
  const open = isControlled ? controlledOpen : uncontrolledOpen;

  const prevOpenRef = useRef(open);

  useEffect(() => {
    const node = document.createElement('div');
    if (open && !prevOpenRef.current) {
      onOpening?.(node);
      requestAnimationFrame(() => onOpened?.(node));
    } else if (!open && prevOpenRef.current) {
      onClosed?.(node);
    }
    prevOpenRef.current = open;
  }, [open, onOpening, onOpened, onClosed]);

  const setOpen = useCallback(
    (nextOpen: boolean, e?: React.SyntheticEvent) => {
      if (disabled && nextOpen) {
        return;
      }
      if (onInteraction) {
        onInteraction(nextOpen, e as React.SyntheticEvent<HTMLElement> | undefined);
      }
      if (!isControlled) {
        setUncontrolledOpen(nextOpen);
      }
    },
    [disabled, onInteraction, isControlled],
  );

  const TriggerTag = (targetTagName ?? (fill ? 'div' : 'span')) as 'span' | 'div';

  const contentNode = (
    <RadixPopover.Content
      className={`dagster-popover ${popoverClassName ?? ''}`}
      side={side}
      align={align}
      sideOffset={mainAxisOffset}
      alignOffset={crossAxisOffset}
      onEscapeKeyDown={canEscapeKeyClose ? undefined : (e) => e.preventDefault()}
      onOpenAutoFocus={(e) => e.preventDefault()}
      onCloseAutoFocus={(e) => e.preventDefault()}
      style={{
        zIndex: 20,
        outline: 'none',
        ...(matchTargetWidth ? {minWidth: 'var(--radix-popover-trigger-width)'} : {}),
      }}
    >
      {content}
    </RadixPopover.Content>
  );

  return (
    <RadixPopover.Root
      open={disabled ? false : open}
      onOpenChange={useCallback((nextOpen: boolean) => setOpen(nextOpen), [setOpen])}
    >
      <RadixPopover.Trigger asChild>
        <TriggerTag
          className={`bp5-popover-target ${className ?? ''}`}
          style={fill ? {display: 'block', width: '100%'} : {}}
          onClick={
            isControlled
              ? (e: React.MouseEvent) => {
                  e.preventDefault();
                  setOpen(!open, e);
                }
              : undefined
          }
          {...targetProps}
        >
          {children}
        </TriggerTag>
      </RadixPopover.Trigger>
      {hasBackdrop && open ? (
        <div
          {...backdropProps}
          style={{position: 'fixed', inset: 0, zIndex: 19, ...backdropProps.style}}
          onClick={() => setOpen(false)}
        />
      ) : null}
      {usePortal ? <RadixPopover.Portal>{contentNode}</RadixPopover.Portal> : contentNode}
    </RadixPopover.Root>
  );
};

// --- Unified Popover export ---

export const Popover = (props: BlueprintPopoverProps) => {
  if (props.interactionKind === 'hover' || props.interactionKind === 'hover-target') {
    return <BlueprintHoverPopover {...props} />;
  }
  return <RadixClickPopover {...props} />;
};
