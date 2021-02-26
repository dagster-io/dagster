import {Colors} from '@blueprintjs/core';
import React from 'react';

import {AssetNumericHistoricalData} from 'src/assets/AssetView';

export const Sparkline: React.FunctionComponent<{
  data: AssetNumericHistoricalData[0];
  width: number;
  height: number;
}> = ({data, width, height}) => {
  const ref = React.createRef<HTMLCanvasElement>();
  React.useEffect(() => {
    if (!ref.current) {
      return;
    }
    const {width, height} = ref.current;
    const ctx = ref.current.getContext('2d');
    if (!ctx) {
      return;
    }
    const margin = height * 0.15;
    const yScale = (height - margin * 2) / (data.maxY - data.minY);
    const xScale = width / (data.maxXNumeric - data.minXNumeric);

    ctx.clearRect(0, 0, width, height);
    ctx.resetTransform();
    ctx.scale(1, -1);
    ctx.translate(0, -height);

    ctx.beginPath();
    ctx.strokeStyle = Colors.BLUE3;
    ctx.lineWidth = 3;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    let penUp = true;
    for (let ii = 0; ii < data.values.length; ii++) {
      const v = data.values[ii];
      if (v.y === null) {
        penUp = true;
      } else {
        const xPx = xScale * (v.xNumeric - data.minXNumeric);
        const yPx = margin + 0.5 + Math.round(yScale * (v.y - data.minY));
        if (penUp) {
          ctx.moveTo(xPx - 2, yPx);
          ctx.lineTo(xPx, yPx);
          penUp = false;
        } else {
          ctx.lineTo(xPx, yPx);
        }
      }
    }
    ctx.stroke();
  }, [ref, data]);

  // Note: canvas `width` attribute is @2x the CSS width to force retina rendering on all displays
  return (
    <canvas
      ref={ref}
      width={width * 2}
      height={height * 2}
      style={{width: width, height: height}}
    />
  );
};
