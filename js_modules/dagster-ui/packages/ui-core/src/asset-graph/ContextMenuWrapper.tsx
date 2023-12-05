import {colorPopoverBackground} from '@dagster-io/ui-components';
import React from 'react';
import ReactDOM from 'react-dom';

export const ContextMenuWrapper = ({
  children,
  menu,
}: {
  children: React.ReactNode;
  menu: React.ReactNode;
}) => {
  const [menuVisible, setMenuVisible] = React.useState(false);
  const [menuPosition, setMenuPosition] = React.useState<{top: number; left: number}>({
    top: 0,
    left: 0,
  });

  const showMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setMenuVisible(true);
    setMenuPosition({top: e.pageY, left: e.pageX});
  };

  const hideMenu = () => {
    setMenuVisible(false);
  };
  const ref = React.useRef<HTMLDivElement | null>(null);
  React.useEffect(() => {
    const node = ref.current;
    const listener = (e: MouseEvent) => {
      if (ref.current && e.target && !ref.current.contains(e.target as Node)) {
        hideMenu();
      }
    };
    const keydownListener = (e: KeyboardEvent) => {
      if (ref.current && e.code === 'Escape') {
        hideMenu();
      }
    };
    if (menuVisible && node) {
      document.body.addEventListener('click', listener);
      document.body.addEventListener('keydown', keydownListener);
    }
    return () => {
      if (node) {
        document.body.removeEventListener('click', listener);
        document.body.removeEventListener('keydown', keydownListener);
      }
    };
  }, [menuVisible]);

  return (
    <div ref={ref}>
      <div onContextMenu={showMenu} onClick={hideMenu}>
        {children}
      </div>
      {menuVisible
        ? ReactDOM.createPortal(
            <div
              style={{
                position: 'absolute',
                top: menuPosition.top,
                left: menuPosition.left,
                backgroundColor: colorPopoverBackground(),
                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                zIndex: 10,
                borderRadius: '4px',
              }}
              onClick={(e) => {
                e.stopPropagation();
              }}
            >
              {menu}
            </div>,
            document.body,
          )
        : null}
    </div>
  );
};
