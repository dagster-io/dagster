const NICE_TIME_LABEL_STRIDES = [1, 2, 3, 4, 6, 12, 24];

export const getTimeLabelStride = ({
  interval,
  minLabelSpacing,
  rangeMs,
  width,
}: {
  interval: number;
  minLabelSpacing: number;
  rangeMs: [number, number];
  width: number;
}) => {
  const duration = rangeMs[1] - rangeMs[0];

  if (duration <= 0 || interval <= 0 || minLabelSpacing <= 0 || width <= 0) {
    return 1;
  }

  const pixelsPerInterval = (width * interval) / duration;
  const minimumStride = Math.max(1, Math.ceil(minLabelSpacing / pixelsPerInterval));

  return NICE_TIME_LABEL_STRIDES.find((stride) => stride >= minimumStride) ?? minimumStride;
};
