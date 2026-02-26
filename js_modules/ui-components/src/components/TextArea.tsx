import clsx from 'clsx';
import * as React from 'react';

import styles from './css/TextArea.module.css';

interface TextAreaProps extends React.ComponentPropsWithRef<'textarea'> {
  resize?: React.CSSProperties['resize'];
  strokeColor?: string;
}

export const TextArea = React.forwardRef(
  (props: TextAreaProps, ref: React.ForwardedRef<HTMLTextAreaElement>) => {
    const {resize, strokeColor, style, className, ...rest} = props;

    const textareaStyle = {
      ...style,
      ...(resize ? {'--text-area-resize': resize} : {}),
      ...(strokeColor
        ? {
            '--text-input-stroke-color': strokeColor,
            '--text-input-stroke-color-hover': strokeColor,
          }
        : {}),
    } as React.CSSProperties;

    return (
      <textarea
        {...rest}
        ref={ref}
        className={clsx(styles.textarea, className)}
        style={textareaStyle}
      />
    );
  },
);

TextArea.displayName = 'TextArea';
