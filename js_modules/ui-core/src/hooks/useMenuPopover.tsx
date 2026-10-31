import {MouseEvent, useCallback, useRef, useState} from 'react';

/**
 * Open state for a click `Popover` whose content is a `Menu`.
 *
 * The popover doesn't close itself when a menu item is chosen, so an item that starts a slow
 * action (such as launching a run) stays clickable until the action completes. Pass `isMenuOpen`
 * and `onInteraction` to the `Popover`, `menuRef` and `onMenuClick` to the `Menu`, and `buttonRef`
 * to the trigger button: the menu then closes as soon as an enabled item is clicked, and focus
 * returns to the trigger so it isn't lost when the focused item unmounts.
 */
export const useMenuPopover = () => {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLUListElement>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const closeMenu = useCallback(() => {
    if (menuRef.current?.contains(document.activeElement)) {
      buttonRef.current?.focus();
    }
    setIsMenuOpen(false);
  }, []);

  const onInteraction = useCallback(
    (nextOpen: boolean) => {
      if (nextOpen) {
        setIsMenuOpen(true);
      } else {
        closeMenu();
      }
    },
    [closeMenu],
  );

  const onMenuClick = useCallback(
    (event: MouseEvent<HTMLUListElement>) => {
      // Disabled items stop their clicks, so only enabled ones reach here.
      if (event.target instanceof Element && event.target.closest('[role="menuitem"]')) {
        closeMenu();
      }
    },
    [closeMenu],
  );

  return {buttonRef, menuRef, isMenuOpen, onInteraction, onMenuClick};
};
