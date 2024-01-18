import * as React from 'react';
import styled from 'styled-components';

import {Button, Icon} from '@dagster-io/ui-components';

import {showCustomAlert} from '../app/CustomAlertProvider';

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
  {isOverflowing: boolean}
> {
  state = {
    isOverflowing: false,
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

  defaultExpand() {
    const message =
      this.contentContainerRef.current && this.contentContainerRef.current.textContent;
    message &&
      showCustomAlert({
        body: <div style={{whiteSpace: 'pre-wrap'}}>{message}</div>,
      });
  }

  onView = () => {
    const {onExpand} = this.props;
    onExpand ? onExpand() : this.defaultExpand();
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
          </>
        )}
      </div>
    );
  }
}
