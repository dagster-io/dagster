import React from 'react';
import {createPortal} from 'react-dom';
import styled, {CSSProperties} from 'styled-components/macro';

import {Box} from './Box';
import {Button} from './Button';
import {Colors} from './Colors';
import {Subheading} from './Text';

export enum Position {
  TOP_LEFT,
  TOP_CENTER,
  TOP_RIGHT,
  BOTTOM_LEFT,
  BOTTOM_CENTER,
  BOTTOM_RIGHT,
}

type ObjectType =
  | {img: string; video?: undefined; object?: undefined}
  | {video: string; img?: undefined; object?: undefined}
  | {object: React.ReactNode; video?: undefined; img?: undefined}
  | {img?: undefined; video?: undefined; object?: undefined};

type Props = {
  title: React.ReactNode;
  description?: React.ReactNode;
  actions?: {
    next?: () => void;
    dismiss?: () => void;
  };
  position: Position;
  width?: CSSProperties['width'];
} & ObjectType;

export const ProductTour: React.FC<Props> = ({
  title,
  description,
  actions,
  position,
  children,
  img,
  video,
  object,
  width,
}) => {
  const media = React.useMemo(() => {
    if (img) {
      return <img src={img} />;
    }
    if (video) {
      return <video src={video} />;
    }
    return object;
  }, [img, video, object]);

  const childrenRef = React.useRef<HTMLDivElement>(null);

  const [top, setTop] = React.useState(-9999);
  const [left, setLeft] = React.useState(-9999);
  const [right, setRight] = React.useState(-9999);
  const [bottom, setBottom] = React.useState(-9999);

  React.useLayoutEffect(() => {
    const childrenWrapper = childrenRef.current;
    if (!childrenWrapper) {
      return () => {};
    }

    const resizeObserver = new ResizeObserver(() => {
      const {top, left, right, bottom} = childrenWrapper.getBoundingClientRect();
      setTop(top);
      setLeft(left);
      setRight(right);
      setBottom(bottom);
    });

    resizeObserver.observe(childrenWrapper);

    return () => {
      resizeObserver.disconnect();
    };
  });

  const actionsJsx = React.useMemo(() => {
    return (
      <ActionsContainer flex={{gap: 6, direction: 'row'}} margin={{top: 8}}>
        {actions?.next ? <Button onClick={actions.next}>Next</Button> : null}
        {actions?.dismiss ? <Button onClick={actions.dismiss}>Dismiss</Button> : null}
      </ActionsContainer>
    );
  }, [actions?.next, actions?.dismiss]);

  return (
    <>
      <div ref={childrenRef}>{children}</div>
      {createPortal(
        <ProductTourPositioner
          $left={left}
          $right={right}
          $bottom={bottom}
          $top={top}
          $position={position}
        >
          <ProductTourContainer flex={{direction: 'column', gap: 4}} padding={16} style={{width}}>
            {media}
            <Subheading style={{fontSize: '16px'}}>{title}</Subheading>
            <div>{description}</div>
            {actionsJsx}
          </ProductTourContainer>
        </ProductTourPositioner>,
        document.body,
      )}
    </>
  );
};

const ProductTourContainer = styled(Box)`
  pointer-events: all;
  background: ${Colors.Gray900};
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0px 2px 12px rgba(0, 0, 0, 0.12);

  width: 260px;
  &,
  button {
    &,
    &:hover,
    &:focus {
      color: ${Colors.White};
    }
  }
`;

const ActionsContainer = styled(Box)`
  > *:not(:first-child) {
    &,
    &:hover,
    &:focus {
      border: none;
      box-shadow: none;
    }
  }
  > * {
    &:hover,
    &:focus {
      opacity: 0.9;
    }
  }
`;

const ProductTourPositioner: React.FC<{
  $position: Position;
  $left: number;
  $bottom: number;
  $right: number;
  $top: number;
}> = ({$position, $right, $left, $bottom, $top, children}) => {
  const isCentered = [Position.TOP_CENTER, Position.BOTTOM_CENTER].includes($position);
  const isTop = [Position.TOP_CENTER, Position.TOP_RIGHT, Position.TOP_LEFT].includes($position);
  const isLeft = [Position.TOP_LEFT, Position.BOTTOM_LEFT].includes($position);
  const isRight = [Position.TOP_RIGHT, Position.BOTTOM_RIGHT].includes($position);

  return (
    <div
      style={{
        pointerEvents: 'none',
        position: 'absolute',
        ...(isTop ? {top: $top} : {top: $bottom}),
        ...(isLeft ? {left: $left} : {}),
        ...(isRight ? {left: $right} : {}),
        ...(isCentered ? {left: $left, right: $right, width: $right - $left + 'px'} : {}),
      }}
    >
      <div style={{position: 'relative'}}>
        <div
          style={{
            position: 'absolute',
            ...(isTop ? {bottom: '10px'} : {top: '10px'}),
            ...(isLeft ? {left: 0} : {}),
            ...(isRight ? {right: 0} : {}),
            ...(isCentered ? {left: 0, right: 0} : {}),
          }}
        >
          <div
            style={
              isCentered
                ? {display: 'flex', justifyContent: 'space-around', alignItems: 'center'}
                : undefined
            }
          >
            <ProductTourPointer
              isCentered={isCentered}
              isTop={isTop}
              isLeft={isLeft}
              isRight={isRight}
            />
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

const ProductTourPointer: React.FC<{
  isCentered: boolean;
  isTop: boolean;
  isLeft: boolean;
  isRight: boolean;
}> = ({isTop, isLeft, isRight}) => {
  return (
    <div
      style={{
        position: 'absolute',
        width: 0,
        height: 0,
        borderStyle: 'solid',
        borderWidth: isTop ? '10px 10px 0 10px' : '0 10px 10px 10px',
        borderColor: isTop
          ? `${Colors.Gray900} transparent transparent transparent`
          : `transparent transparent ${Colors.Gray900} transparent`,
        ...(isTop ? {bottom: '-10px'} : {top: '-10px'}),
        ...(isLeft ? {left: '14px'} : {}),
        ...(isRight ? {right: '14px'} : {}),
      }}
    />
  );
};
