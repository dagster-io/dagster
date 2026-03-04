import {Button, Dialog, DialogFooter, Icon} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {MAX_ROW_HEIGHT_PX} from './LogsRowComponents';

const OverflowFade = styled.div`
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  user-select: none;
  pointer-events: none;
`;

const OverflowButtonContainer = styled.div`
  position: absolute;
  bottom: 6px;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: row;
  justify-content: center;
  gap: 8px;
`;

interface Props {
  children: React.ReactNode;
  style: React.CSSProperties;
  onExpand?: () => void;
  forceExpandability?: boolean;
}

export const CellTruncationProvider = (props: Props) => {
  const [state, setState] = React.useState({
    isOverflowing: false,
    showDialog: false,
  });
  const contentContainerRef = React.useRef<HTMLDivElement>(null);

  const detectOverflow = React.useCallback(() => {
    const child = contentContainerRef.current?.firstElementChild;
    if (!child) {
      return;
    }

    const isOverflowing = child.scrollHeight > MAX_ROW_HEIGHT_PX;
    setState((prev) => (prev.isOverflowing !== isOverflowing ? {...prev, isOverflowing} : prev));
  }, []);

  React.useEffect(() => {
    detectOverflow();
  });

  const dialogContents = () => {
    const message = contentContainerRef.current?.textContent;
    return message ? <div style={{whiteSpace: 'pre-wrap'}}>{message}</div> : null;
  };

  const onView = () => {
    if (props.onExpand) {
      props.onExpand();
    } else {
      setState((prev) => ({...prev, showDialog: true}));
    }
  };

  const style = {...props.style, overflow: 'hidden'};

  return (
    <div style={style}>
      <div ref={contentContainerRef}>{props.children}</div>
      {(state.isOverflowing || props.forceExpandability) && (
        <>
          <OverflowFade />
          <OverflowButtonContainer>
            <Button intent="primary" icon={<Icon name="unfold_more" />} onClick={onView}>
              View full message
            </Button>
          </OverflowButtonContainer>
          {props.onExpand ? null : (
            <Dialog
              canEscapeKeyClose
              canOutsideClickClose
              isOpen={state.showDialog}
              onClose={() => setState((prev) => ({...prev, showDialog: false}))}
              style={{width: 'auto', maxWidth: '80vw'}}
            >
              <div>{dialogContents()}</div>
              <DialogFooter topBorder>
                <Button
                  intent="primary"
                  onClick={() => setState((prev) => ({...prev, showDialog: false}))}
                >
                  Done
                </Button>
              </DialogFooter>
            </Dialog>
          )}
        </>
      )}
    </div>
  );
};
