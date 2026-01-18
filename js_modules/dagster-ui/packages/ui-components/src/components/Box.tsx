import clsx from 'clsx';
import {HTMLAttributes, forwardRef} from 'react';

import styles from './Box.module.css';
import {Colors} from './Color';
import {
  AlignItems,
  BorderSetting,
  BorderSide,
  BorderWidth,
  DirectionalSpacing,
  FlexDirection,
  FlexProperties,
  FlexWrap,
  JustifyContent,
} from './types';

export interface Props {
  background?: string | null;
  border?: BorderSide | BorderSetting | null;
  flex?: FlexProperties | null;
  margin?: DirectionalSpacing | null;
  padding?: DirectionalSpacing | null;
}

type CSSProperties = React.CSSProperties;

const getPaddingClassForNumber = (padding: number): string => {
  return clsx(
    padding === 1 ? styles.p1 : null,
    padding === 2 ? styles.p2 : null,
    padding === 4 ? styles.p4 : null,
    padding === 8 ? styles.p8 : null,
    padding === 12 ? styles.p12 : null,
    padding === 16 ? styles.p16 : null,
    padding === 20 ? styles.p20 : null,
    padding === 24 ? styles.p24 : null,
    padding === 32 ? styles.p32 : null,
    padding === 48 ? styles.p48 : null,
    padding === 64 ? styles.p64 : null,
  );
};

const getLeftPaddingClassForNumber = (padding: number): string => {
  return clsx(
    padding === 1 ? styles.pl1 : null,
    padding === 2 ? styles.pl2 : null,
    padding === 4 ? styles.pl4 : null,
    padding === 8 ? styles.pl8 : null,
    padding === 12 ? styles.pl12 : null,
    padding === 16 ? styles.pl16 : null,
    padding === 20 ? styles.pl20 : null,
    padding === 24 ? styles.pl24 : null,
    padding === 32 ? styles.pl32 : null,
    padding === 48 ? styles.pl48 : null,
    padding === 64 ? styles.pl64 : null,
  );
};

const getRightPaddingClassForNumber = (padding: number): string => {
  return clsx(
    padding === 1 ? styles.pr1 : null,
    padding === 2 ? styles.pr2 : null,
    padding === 4 ? styles.pr4 : null,
    padding === 8 ? styles.pr8 : null,
    padding === 12 ? styles.pr12 : null,
    padding === 16 ? styles.pr16 : null,
    padding === 20 ? styles.pr20 : null,
    padding === 24 ? styles.pr24 : null,
    padding === 32 ? styles.pr32 : null,
    padding === 48 ? styles.pr48 : null,
    padding === 64 ? styles.pr64 : null,
  );
};

const getBottomPaddingClassForNumber = (padding: number): string => {
  return clsx(
    padding === 1 ? styles.pb1 : null,
    padding === 2 ? styles.pb2 : null,
    padding === 4 ? styles.pb4 : null,
    padding === 8 ? styles.pb8 : null,
    padding === 12 ? styles.pb12 : null,
    padding === 16 ? styles.pb16 : null,
    padding === 20 ? styles.pb20 : null,
    padding === 24 ? styles.pb24 : null,
    padding === 32 ? styles.pb32 : null,
    padding === 48 ? styles.pb48 : null,
    padding === 64 ? styles.pb64 : null,
  );
};

const getTopPaddingClassForNumber = (padding: number): string => {
  return clsx(
    padding === 1 ? styles.pt1 : null,
    padding === 2 ? styles.pt2 : null,
    padding === 4 ? styles.pt4 : null,
    padding === 8 ? styles.pt8 : null,
    padding === 12 ? styles.pt12 : null,
    padding === 16 ? styles.pt16 : null,
    padding === 20 ? styles.pt20 : null,
    padding === 24 ? styles.pt24 : null,
    padding === 32 ? styles.pt32 : null,
    padding === 48 ? styles.pt48 : null,
    padding === 64 ? styles.pt64 : null,
  );
};

const getPaddingClasses = (padding: DirectionalSpacing): string => {
  if (typeof padding === 'number') {
    return getPaddingClassForNumber(padding);
  }

  const {top, right, bottom, left, vertical, horizontal} = padding;
  const topPaddingClass = getTopPaddingClassForNumber(top ?? vertical ?? 0);
  const bottomPaddingClass = getBottomPaddingClassForNumber(bottom ?? vertical ?? 0);
  const rightPaddingClass = getRightPaddingClassForNumber(right ?? horizontal ?? 0);
  const leftPaddingClass = getLeftPaddingClassForNumber(left ?? horizontal ?? 0);

  return clsx(topPaddingClass, rightPaddingClass, bottomPaddingClass, leftPaddingClass);
};

const getMarginClassForNumber = (margin: number): string => {
  return clsx(
    margin === 1 ? styles.m1 : null,
    margin === 2 ? styles.m2 : null,
    margin === 4 ? styles.m4 : null,
    margin === 8 ? styles.m8 : null,
    margin === 12 ? styles.m12 : null,
    margin === 16 ? styles.m16 : null,
    margin === 20 ? styles.m20 : null,
    margin === 24 ? styles.m24 : null,
    margin === 32 ? styles.m32 : null,
    margin === 48 ? styles.m48 : null,
    margin === 64 ? styles.m64 : null,
  );
};

const getLeftMarginClassForNumber = (margin: number): string => {
  return clsx(
    margin === 1 ? styles.ml1 : null,
    margin === 2 ? styles.ml2 : null,
    margin === 4 ? styles.ml4 : null,
    margin === 8 ? styles.ml8 : null,
    margin === 12 ? styles.ml12 : null,
    margin === 16 ? styles.ml16 : null,
    margin === 20 ? styles.ml20 : null,
    margin === 24 ? styles.ml24 : null,
    margin === 32 ? styles.ml32 : null,
    margin === 48 ? styles.ml48 : null,
    margin === 64 ? styles.ml64 : null,
  );
};

const getRightMarginClassForNumber = (margin: number): string => {
  return clsx(
    margin === 1 ? styles.mr1 : null,
    margin === 2 ? styles.mr2 : null,
    margin === 4 ? styles.mr4 : null,
    margin === 8 ? styles.mr8 : null,
    margin === 12 ? styles.mr12 : null,
    margin === 16 ? styles.mr16 : null,
    margin === 20 ? styles.mr20 : null,
    margin === 24 ? styles.mr24 : null,
    margin === 32 ? styles.mr32 : null,
    margin === 48 ? styles.mr48 : null,
    margin === 64 ? styles.mr64 : null,
  );
};

const getBottomMarginClassForNumber = (margin: number): string => {
  return clsx(
    margin === 1 ? styles.mb1 : null,
    margin === 2 ? styles.mb2 : null,
    margin === 4 ? styles.mb4 : null,
    margin === 8 ? styles.mb8 : null,
    margin === 12 ? styles.mb12 : null,
    margin === 16 ? styles.mb16 : null,
    margin === 20 ? styles.mb20 : null,
    margin === 24 ? styles.mb24 : null,
    margin === 32 ? styles.mb32 : null,
    margin === 48 ? styles.mb48 : null,
    margin === 64 ? styles.mb64 : null,
  );
};

const getTopMarginClassForNumber = (margin: number): string => {
  return clsx(
    margin === 1 ? styles.mt1 : null,
    margin === 2 ? styles.mt2 : null,
    margin === 4 ? styles.mt4 : null,
    margin === 8 ? styles.mt8 : null,
    margin === 12 ? styles.mt12 : null,
    margin === 16 ? styles.mt16 : null,
    margin === 20 ? styles.mt20 : null,
    margin === 24 ? styles.mt24 : null,
    margin === 32 ? styles.mt32 : null,
    margin === 48 ? styles.mt48 : null,
    margin === 64 ? styles.mt64 : null,
  );
};

const getMarginClasses = (margin: DirectionalSpacing): string => {
  if (typeof margin === 'number') {
    return getMarginClassForNumber(margin);
  }

  const {top, right, bottom, left, vertical, horizontal} = margin;
  const topMarginClass = getTopMarginClassForNumber(top ?? vertical ?? 0);
  const bottomMarginClass = getBottomMarginClassForNumber(bottom ?? vertical ?? 0);
  const rightMarginClass = getRightMarginClassForNumber(right ?? horizontal ?? 0);
  const leftMarginClass = getLeftMarginClassForNumber(left ?? horizontal ?? 0);

  return clsx(topMarginClass, rightMarginClass, bottomMarginClass, leftMarginClass);
};

const getFlexDirectionClass = (direction: FlexDirection | undefined): string => {
  return clsx(
    direction === 'row' ? styles.flexRow : null,
    direction === 'row-reverse' ? styles.flexRowReverse : null,
    direction === 'column' ? styles.flexColumn : null,
    direction === 'column-reverse' ? styles.flexColumnReverse : null,
  );
};

const getFlexWrapClass = (wrap: FlexWrap | undefined): string => {
  return clsx(
    wrap === 'wrap' ? styles.flexWrap : null,
    wrap === 'nowrap' ? styles.flexNowrap : null,
    wrap === 'wrap-reverse' ? styles.flexWrapReverse : null,
  );
};

const getAlignItemsClass = (alignItems: AlignItems | undefined): string => {
  return clsx(
    alignItems === 'stretch' ? styles.alignStretch : null,
    alignItems === 'center' ? styles.alignCenter : null,
    alignItems === 'start' ? styles.alignStart : null,
    alignItems === 'end' ? styles.alignEnd : null,
    alignItems === 'flex-start' ? styles.alignFlexStart : null,
    alignItems === 'flex-end' ? styles.alignFlexEnd : null,
    alignItems === 'baseline' ? styles.alignBaseline : null,
  );
};

const getJustifyContentClass = (justifyContent: JustifyContent | undefined): string => {
  return clsx(
    justifyContent === 'flex-start' ? styles.justifyFlexStart : null,
    justifyContent === 'flex-end' ? styles.justifyFlexEnd : null,
    justifyContent === 'center' ? styles.justifyCenter : null,
    justifyContent === 'start' ? styles.justifyStart : null,
    justifyContent === 'end' ? styles.justifyEnd : null,
    justifyContent === 'left' ? styles.justifyLeft : null,
    justifyContent === 'right' ? styles.justifyRight : null,
    justifyContent === 'space-between' ? styles.justifySpaceBetween : null,
    justifyContent === 'space-around' ? styles.justifySpaceAround : null,
    justifyContent === 'space-evenly' ? styles.justifySpaceEvenly : null,
    justifyContent === 'stretch' ? styles.justifyStretch : null,
  );
};

// Helper to convert flex properties to classes and inline styles
const getFlexStyles = (flex: FlexProperties): {classes: string[]; inlineStyle: CSSProperties} => {
  const classes: string[] = [];
  const inlineStyle: CSSProperties = {};

  // Display
  const display = flex.display;
  if (display === 'flex' || display === undefined) {
    classes.push(clsx(styles.flex));
  } else if (display === 'inline-flex') {
    classes.push(clsx(styles.inlineFlex));
  }

  classes.push(getFlexDirectionClass(flex.direction));
  classes.push(getFlexWrapClass(flex.wrap));
  classes.push(getAlignItemsClass(flex.alignItems));
  classes.push(getJustifyContentClass(flex.justifyContent));

  // Numeric properties - use inline styles
  if (flex.grow !== undefined && flex.grow !== null) {
    inlineStyle.flexGrow = flex.grow;
  }
  if (flex.shrink !== undefined && flex.shrink !== null) {
    inlineStyle.flexShrink = flex.shrink;
  }
  if (flex.basis !== undefined && flex.basis !== null) {
    inlineStyle.flexBasis = flex.basis;
  }
  if (flex.gap !== undefined && flex.gap !== null) {
    inlineStyle.gap = `${flex.gap}px`;
  }

  return {classes, inlineStyle};
};

const getBorderClassFromSide = (side: BorderSide): string => {
  return clsx(
    side === 'top' ? styles.borderTop : null,
    side === 'bottom' ? styles.borderBottom : null,
    side === 'left' ? styles.borderLeft : null,
    side === 'right' ? styles.borderRight : null,
    side === 'top-and-bottom' ? styles.borderTopBottom : null,
    side === 'left-and-right' ? styles.borderLeftRight : null,
    side === 'all' ? styles.borderAll : null,
  );
};

const getBorderWidthClass = (width: BorderWidth): string => {
  return clsx(width === 2 ? styles.borderWidth2 : null, width === 4 ? styles.borderWidth4 : null);
};

const getCustomBorderStyle = (side: BorderSide, width: BorderWidth, color: string): string => {
  switch (side) {
    case 'all':
      return `inset 0 0 0 ${width}px ${color}`;
    case 'top-and-bottom':
      return `inset 0 ${width}px ${color}, inset 0 -${width}px ${color}`;
    case 'left-and-right':
      return `inset ${width}px 0 ${color}, inset -${width}px 0 ${color}`;
    case 'top':
      return `inset 0 ${width}px ${color}`;
    case 'bottom':
      return `inset 0 -${width}px ${color}`;
    case 'right':
      return `inset -${width}px 0 ${color}`;
    case 'left':
      return `inset ${width}px 0 ${color}`;
    default:
      return '';
  }
};

// Helper to convert border to classes and inline style
const getBorderStyles = (
  border: BorderSide | BorderSetting,
): {classes: string[]; inlineStyle: CSSProperties | null} => {
  const classes: string[] = [];
  let inlineStyle: CSSProperties | null = null;

  const borderValue: BorderSetting =
    typeof border === 'string' ? {side: border, width: 1, color: Colors.keylineDefault()} : border;
  const {side, width = 1, color = Colors.keylineDefault()} = borderValue;

  classes.push(getBorderClassFromSide(side));
  classes.push(getBorderWidthClass(width));

  // If custom color is provided, use inline style to override.
  const defaultColor = Colors.keylineDefault();
  if (color !== defaultColor) {
    // Generate box-shadow value based on side and width
    inlineStyle = {boxShadow: getCustomBorderStyle(side, width, color)};
  }

  return {classes, inlineStyle};
};

export const Box = forwardRef<HTMLDivElement, Props & HTMLAttributes<HTMLDivElement>>(
  (props, ref) => {
    const {
      background,
      border,
      flex,
      margin,
      padding,
      className: userClassName,
      style: userStyle,
      ...rest
    } = props;

    const classes: (string | undefined)[] = [];
    const inlineStyles: CSSProperties = {};

    if (padding) {
      classes.push(getPaddingClasses(padding));
    }

    if (margin) {
      classes.push(getMarginClasses(margin));
    }

    if (flex) {
      const {classes: flexClasses, inlineStyle: flexStyle} = getFlexStyles(flex);
      classes.push(...flexClasses);
      Object.assign(inlineStyles, flexStyle);
    }

    if (background) {
      inlineStyles.backgroundColor = background;
    }

    if (border) {
      const {classes: borderClasses, inlineStyle: borderStyle} = getBorderStyles(border);
      classes.push(...borderClasses);
      if (borderStyle) {
        Object.assign(inlineStyles, borderStyle);
      }
    }

    const finalStyle = {
      ...inlineStyles,
      ...userStyle,
    };

    return (
      <div
        {...rest}
        ref={ref}
        className={clsx(classes, userClassName)}
        style={Object.keys(finalStyle).length > 0 ? finalStyle : undefined}
      />
    );
  },
);

Box.displayName = 'Box';
