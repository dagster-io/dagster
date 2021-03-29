import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import ReactDOM from 'react-dom';
import styled from 'styled-components/macro';

const MODIFIER_KEYCODES = [17, 18, 91, 224];
const SHORTCUT_VISIBILITY_EVENT_TYPE = 'shortcut-visibility';
const SHORTCUT_VISIBLITY_DELAY = 800;

// Global page state / handling of "shortcut mode". Press any modifier key
// for 800ms to show shortcuts. This code emits a custom event that React
// components on the page can listen for to update their states and vends
// the current state via getShortcutsVisible. (Always having a correct
// "initial state" based on previous keyboard events is why this cannot be
// implemented inside a React component.
//
let shortcutsVisible = false;
let shortcutsTimer: NodeJS.Timeout | null = null;

function getShortcutsVisible() {
  return shortcutsVisible;
}

function setShortcutsVisible(state: boolean) {
  shortcutsVisible = state;
  window.dispatchEvent(new CustomEvent(SHORTCUT_VISIBILITY_EVENT_TYPE));
}

function hideShortcuts() {
  if (shortcutsTimer) {
    clearTimeout(shortcutsTimer);
    shortcutsTimer = null;
  }
  if (shortcutsVisible) {
    setShortcutsVisible(false);
  }
}

const otherModifiersUsed = (event: KeyboardEvent) => {
  const {key} = event;
  return (
    event.shiftKey ||
    (key !== 'Alt' && event.altKey) ||
    (key !== 'Ctrl' && event.ctrlKey) ||
    (key !== 'Meta' && event.metaKey)
  );
};

window.addEventListener('keydown', (event) => {
  const isModifier = MODIFIER_KEYCODES.includes(event.keyCode);
  if (!isModifier || otherModifiersUsed(event)) {
    // If any non-modifiers are pressed or if multiple modifiers are in use, kill the timeout
    // and hide the shortcuts.
    hideShortcuts();
  } else if (!shortcutsTimer && !shortcutsVisible) {
    shortcutsTimer = setTimeout(() => setShortcutsVisible(true), SHORTCUT_VISIBLITY_DELAY);
  }
});
window.addEventListener('keyup', (event) => {
  if (MODIFIER_KEYCODES.includes(event.keyCode)) {
    hideShortcuts();
  }
});
window.addEventListener('blur', () => {
  hideShortcuts();
});

interface ShortcutHandlerProps {
  // Optionally pass onGlobalKeyDown to receive every global key event
  onGlobalKeyDown?: (event: KeyboardEvent) => void;

  // Optionally pass onShortcut and shortcutFilter to receive key events
  // that match the shortcutFilter test with preventDefault() already called.
  // This allows you to co-locate the shortcut label and event test code.
  onShortcut?: (event: KeyboardEvent) => void;
  shortcutFilter?: (event: KeyboardEvent) => boolean;

  // Pass a shortcutLabel for the item to be highlighted during shortcut preview.
  shortcutLabel?: string;
}

interface ShortcutHandlerState {
  previewPosition: null | {left: number; top: number};
}

export class ShortcutHandler extends React.Component<ShortcutHandlerProps, ShortcutHandlerState> {
  state: ShortcutHandlerState = {
    previewPosition: null,
  };

  componentDidMount() {
    window.addEventListener('keydown', this.onGlobalKeydown);
    window.addEventListener(SHORTCUT_VISIBILITY_EVENT_TYPE, this.onShortcutVisiblityChange);
    this.onShortcutVisiblityChange();
  }

  componentWillUnmount() {
    window.removeEventListener('keydown', this.onGlobalKeydown);
    window.removeEventListener(SHORTCUT_VISIBILITY_EVENT_TYPE, this.onShortcutVisiblityChange);
  }

  onShortcutVisiblityChange = () => {
    if (getShortcutsVisible()) {
      // Deprecated one day, but not likely to be soon? Alternative is to React.cloneElement
      // and attach a ref prop to `children` without wrapping it in another DOM node, but
      // we can't be sure we get a DOM node and not a React component ref. @BG
      // https://reactjs.org/docs/refs-and-the-dom.html#exposing-dom-refs-to-parent-components
      // eslint-disable-next-line react/no-find-dom-node
      const el = ReactDOM.findDOMNode(this);
      if (!el || !(el instanceof HTMLElement)) {
        return;
      }
      const rect = el.getBoundingClientRect();
      this.setState({
        previewPosition: {
          left: rect.left + rect.width,
          top: rect.top + rect.height,
        },
      });
    } else if (this.state.previewPosition !== null) {
      this.setState({previewPosition: null});
    }
  };

  onGlobalKeydown = (event: KeyboardEvent) => {
    const {target} = event;

    const inTextInput =
      target &&
      ((target as HTMLElement).nodeName === 'INPUT' ||
        (target as HTMLElement).nodeName === 'TEXTAREA');

    if (inTextInput && !(event.altKey || event.ctrlKey || event.metaKey)) {
      return;
    }

    this.props.onGlobalKeyDown?.(event);

    if (this.props.onShortcut && this.props.shortcutFilter && this.props.shortcutFilter(event)) {
      event.preventDefault();

      // Pull the focus out of the currently focused field (if there is one). This better
      // simulates typical onClick behavior where the button is focused by mousedown before
      // the click so shortcut activation doesn't need to be  tested separately. It also
      // ensures the value of the codemirror / text input is "committed" before the click.
      if (document.activeElement instanceof HTMLElement) {
        document.activeElement.blur();
      }

      this.props.onShortcut(event);
    }
  };

  render() {
    const {children, shortcutLabel} = this.props;
    const {previewPosition} = this.state;

    if (shortcutLabel && previewPosition) {
      return (
        <>
          {children}
          <ShortcutAnnotation style={{top: previewPosition.top, left: previewPosition.left}}>
            {shortcutLabel}
          </ShortcutAnnotation>
        </>
      );
    }
    return <>{children}</>;
  }
}

const ShortcutAnnotation = styled.div`
  position: fixed;
  min-width: 32px;
  font-size: 12px;
  font-weight: 600;
  line-height: 14px;
  text-align: center;
  padding: 2px;
  z-index: 20;
  transform: translate(-90%, -10px);
  color: ${Colors.LIGHT_GRAY3};
  background: ${Colors.DARK_GRAY4};
  border: 1px solid ${Colors.GRAY4};
  border-radius: 3px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
`;
