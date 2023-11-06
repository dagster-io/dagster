// eslint-disable-next-line no-restricted-imports
import {Placement} from '@blueprintjs/popover2';
import React from 'react';
import styled, {CSSProperties} from 'styled-components';

import {Box} from './Box';
import {Button} from './Button';
import {Colors} from './Colors';
import {Popover} from './Popover';
import {Subheading} from './Text';

export enum ProductTourPosition {
  TOP_LEFT = 'top-start',
  TOP_CENTER = 'top',
  TOP_RIGHT = 'top-end',
  BOTTOM_LEFT = 'bottom-start',
  BOTTOM_CENTER = 'bottom',
  BOTTOM_RIGHT = 'bottom-end',
}

type ObjectType =
  | {img: string; video?: undefined; object?: undefined}
  | {video: string; img?: undefined; object?: undefined}
  | {object: React.ReactNode; video?: undefined; img?: undefined}
  | {img?: undefined; video?: undefined; object?: undefined};

type Props = {
  children: React.ReactNode;
  title: React.ReactNode;
  description?: React.ReactNode;
  actions?: {
    next?: () => void;
    dismiss?: () => void;
  };
  position: ProductTourPosition;
  width?: CSSProperties['width'];
} & ObjectType;

export const ProductTour = ({
  title,
  description,
  actions,
  position,
  children,
  img,
  video,
  object,
  width = '260px',
}: Props) => {
  const media = React.useMemo(() => {
    if (img) {
      return <img src={img} style={{borderRadius: '6px'}} />;
    }
    if (video) {
      return <video src={video} style={{borderRadius: '6px'}} autoPlay loop muted />;
    }
    return object;
  }, [img, video, object]);

  const actionsJsx = React.useMemo(() => {
    return (
      <ActionsContainer flex={{gap: 6, direction: 'row'}} margin={{top: 8}}>
        {actions?.next ? <Button onClick={actions.next}>Next</Button> : null}
        {actions?.dismiss ? <Button onClick={actions.dismiss}>Dismiss</Button> : null}
      </ActionsContainer>
    );
  }, [actions?.next, actions?.dismiss]);

  return (
    <Popover
      isOpen={true}
      placement={position as Placement}
      modifiers={{
        arrow: {enabled: true},
        preventOverflow: {enabled: true},
      }}
      minimal={false}
      content={
        <>
          <div />
          <ProductTourContainer flex={{direction: 'column', gap: 4}} padding={16} style={{width}}>
            <Box flex={{direction: 'column', gap: 8}}>
              {media}
              <Subheading style={{fontSize: '16px'}}>{title}</Subheading>
            </Box>
            <div>{description}</div>
            {actionsJsx}
          </ProductTourContainer>
          <div />
        </>
      }
    >
      {children}
    </Popover>
  );
};

const ProductTourContainer = styled(Box)`
  pointer-events: all;
  background: ${Colors.Gray900};
  border-radius: 4px;
  padding: 16px;
  box-shadow: 0px 2px 12px rgba(0, 0, 0, 0.12);

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
