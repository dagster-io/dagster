export type TimeFormat = {
  showTimezone?: boolean;
  showSeconds?: boolean;
  showMsec?: boolean;
};

export const DEFAULT_TIME_FORMAT = {
  showTimezone: false,
  showSeconds: false,
  showMsec: false,
};

export const DEFAULT_TOOLTIP_TIME_FORMAT = {showSeconds: false, showTimezone: true};
