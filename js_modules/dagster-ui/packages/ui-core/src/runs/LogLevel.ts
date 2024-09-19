export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARNING = 'WARNING',
  ERROR = 'ERROR',
  CRITICAL = 'CRITICAL',
  EVENT = 'EVENT', // structured events
}

export const DefaultLogLevels = ['INFO', 'WARNING', 'ERROR', 'CRITICAL', 'EVENT'];
