export type Spacing = 0 | 1 | 2 | 4 | 8 | 12 | 16 | 20 | 24 | 32 | 48 | 64;
export type DirectionalSpacing =
  | Spacing
  | {
      top?: Spacing;
      right?: Spacing;
      bottom?: Spacing;
      left?: Spacing;
      vertical?: Spacing;
      horizontal?: Spacing;
    };

export type AlignItems =
  | 'stretch'
  | 'center'
  | 'start'
  | 'end'
  | 'flex-start'
  | 'flex-end'
  | 'baseline';

export type FlexDirection = 'row' | 'row-reverse' | 'column' | 'column-reverse';
export type FlexProperties = {
  alignItems?: AlignItems;
  basis?: string;
  direction?: FlexDirection;
  display?: 'flex' | 'inline-flex';
  grow?: number;
  justifyContent?:
    | 'center'
    | 'start'
    | 'end'
    | 'flex-start'
    | 'flex-end'
    | 'left'
    | 'right'
    | 'space-between'
    | 'space-around'
    | 'space-evenly'
    | 'stretch';
  shrink?: number;
  wrap?: 'nowrap' | 'wrap' | 'wrap-reverse';
};

export type BorderSide = 'top' | 'right' | 'bottom' | 'left' | 'horizontal' | 'vertical' | 'all';
export type BorderWidth = 1 | 2;
export type BorderColor = 'light' | 'medium' | 'dark';
export type BorderSetting = {width: BorderWidth; color: BorderColor; side: BorderSide};
