import {Colors, Slider} from '@dagster-io/ui-components';
import * as React from 'react';

/**
 * Renders a horizontal slider that lets you adjust the graph's relative zoom from 1-100.
 */
export const ZoomSlider = React.memo((props: {value: number; onChange: (v: number) => void}) => {
  return (
    <Slider
      value={props.value}
      onChange={props.onChange}
      min={0}
      max={100}
      step={0.1}
      trackColor={Colors.backgroundGray()}
      rangeColor={Colors.accentGray()}
    />
  );
});
