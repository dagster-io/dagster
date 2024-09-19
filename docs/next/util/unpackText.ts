import React from 'react';

// This utility function is for our Markdoc components.
// This function unpacks the children of the Button component to avoid the hydration error caused by markdoc wraping blocks with an extra <p> tag.
// The conditional logic is to ensure that it works in all cases rather than just the one where the children are wrapped in a <p> tag.

export const unpackText = (children) => {
  // console.log(children);
  if (children?.type === 'p') {
    return [...React.Children.toArray(children.props.children)];
  } else {
    return children;
  }
};
