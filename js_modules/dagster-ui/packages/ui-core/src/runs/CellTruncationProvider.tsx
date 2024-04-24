import {Button, Dialog, DialogFooter, Icon} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

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
`;

export class CellTruncationProvider extends React.Component<
  {
    children: React.ReactNode;
    style: React.CSSProperties;
    onExpand?: () => void;
    forceExpandability?: boolean;
  },
  {isOverflowing: boolean; showDialog: boolean}
> {
  state = {
    isOverflowing: false,
    showDialog: false,
  };

  private contentContainerRef: React.RefObject<HTMLDivElement> = React.createRef();

  componentDidMount() {
    this.detectOverflow();
  }

  componentDidUpdate() {
    this.detectOverflow();
  }

  detectOverflow() {
    const child =
      this.contentContainerRef.current && this.contentContainerRef.current.firstElementChild;

    if (!child) {
      return;
    }

    const isOverflowing =
      typeof this.props.style.height === 'number' && child.scrollHeight > this.props.style.height;
    if (isOverflowing !== this.state.isOverflowing) {
      this.setState({isOverflowing});
    }
  }

  dialogContents() {
    const message =
      this.contentContainerRef.current && this.contentContainerRef.current.textContent;
    if (message) {
      return <div style={{whiteSpace: 'pre-wrap'}}>{message}</div>;
    }
    return null;
  }

  onView = () => {
    const {onExpand} = this.props;
    onExpand ? onExpand() : this.setState({showDialog: true});
  };

  render() {
    const style = {...this.props.style, overflow: 'hidden'};

    return (
      <div style={style}>
        <div ref={this.contentContainerRef}>{this.props.children}</div>
        {(this.state.isOverflowing || this.props.forceExpandability) && (
          <>
            <OverflowFade />
            <OverflowButtonContainer>
              <Button intent="primary" icon={<Icon name="unfold_more" />} onClick={this.onView}>
                View full message
              </Button>
            </OverflowButtonContainer>
            {this.props.onExpand ? null : (
              <Dialog
                canEscapeKeyClose
                canOutsideClickClose
                isOpen={this.state.showDialog}
                onClose={() => this.setState({showDialog: false})}
                style={{width: 'auto', maxWidth: '80vw'}}
              >
                <div>{this.dialogContents()}</div>
                <DialogFooter topBorder>
                  <Button intent="primary" onClick={() => this.setState({showDialog: false})}>
                    Done
                  </Button>
                </DialogFooter>
              </Dialog>
            )}
          </>
        )}
      </div>
    );
  }
}
