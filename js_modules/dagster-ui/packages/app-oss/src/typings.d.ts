/* eslint-disable import/no-default-export */

/// <reference types="next" />

declare module '@vx/gradient';
declare module '@vx/group';
declare module '@vx/network';
declare module '@vx/shape';
declare module '@vx/legend';
declare module '@vx/scale';
declare module '@vx/responsive';

declare module 'amator';

declare let __webpack_public_path__: string;

// Type declarations for Clipboard API
// https://developer.mozilla.org/en-US/docs/Web/API/Clipboard_API
interface Clipboard {
  writeText(newClipText: string): Promise<void>;
  // Add any other methods you need here.
}

interface NavigatorClipboard {
  // Only available in a secure context.
  readonly clipboard?: Clipboard;
}

interface Navigator extends NavigatorClipboard {}

declare module '*.json' {
  const value: any;
  export default value;
}

declare module '*.mp4' {
  const src: string;
  export default src;
}

declare module 'worker-loader!*' {
  class WebpackWorker extends Worker {
    constructor();
  }

  export default WebpackWorker;
}

declare namespace Intl {
  type Key = 'calendar' | 'collation' | 'currency' | 'numberingSystem' | 'timeZone' | 'unit';

  function supportedValuesOf(input: Key): string[];

  interface Locale extends LocaleOptions {
    timeZones: string[];
  }
}
