import * as React from 'react';

import {Box} from './Box';
import {Button} from './Button';
import {Popover} from './Popover';
import {Subheading} from './Text';
import styles from './css/ProductTour.module.css';

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
  canShow?: boolean;
  actions?: {
    custom?: React.ReactNode;
    next?: () => void;
    dismiss?: () => void;
  };
  position: ProductTourPosition;
  width?: React.CSSProperties['width'];
  modifiers?: React.ComponentProps<typeof Popover>['modifiers'];
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
  modifiers = {},
  width = '260px',
  canShow = true,
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
      <Box className={styles.actions} flex={{gap: 6, direction: 'row'}} margin={{top: 8}}>
        {actions?.custom}
        {actions?.next ? <Button onClick={actions.next}>Next</Button> : null}
        {actions?.dismiss ? <Button onClick={actions.dismiss}>Dismiss</Button> : null}
      </Box>
    );
  }, [actions?.custom, actions?.next, actions?.dismiss]);

  return (
    <Popover
      popoverClassName="bp5-dark"
      isOpen={canShow}
      placement={position}
      modifiers={{
        arrow: {enabled: true},
        preventOverflow: {enabled: true},
        ...modifiers,
      }}
      minimal={false}
      content={
        <div
          onClick={(ev) => {
            ev.stopPropagation();
          }}
        >
          <div />
          <Box
            className={styles.container}
            flex={{direction: 'column', gap: 4}}
            padding={16}
            style={{width}}
          >
            <Box flex={{direction: 'column', gap: 8}}>
              {media}
              <Subheading style={{fontSize: '16px'}}>{title}</Subheading>
            </Box>
            <div>{description}</div>
            {actionsJsx}
          </Box>
          <div />
        </div>
      }
    >
      {children}
    </Popover>
  );
};
