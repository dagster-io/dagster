/* eslint-disable import/no-default-export */
/// <reference types="next" />

declare module '@vx/shape';

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

declare module '*.graphql' {
  import { DocumentNode } from 'graphql';
  const Schema: DocumentNode;

  export = Schema;
}

declare module 'chartjs-adapter-date-fns';

declare namespace Intl {
  type Key = 'calendar' | 'collation' | 'currency' | 'numberingSystem' | 'timeZone' | 'unit';

  function supportedValuesOf(input: Key): string[];

  interface Locale extends LocaleOptions {
    timeZones: string[];
  }
}

type StaticImageData = {
  src: string;
  height: number;
  width: number;
  placeholder?: string;
};

declare module '*.svg' {
  const content: StaticImageData;
  export default content;
}

declare module '*.png' {
  const content: StaticImageData;
  export default content;
}

declare module '*.jpg' {
  const content: StaticImageData;
  export default content;
}

declare module '*.jpeg' {
  const content: StaticImageData;
  export default content;
}

declare module '*.gif' {
  const content: StaticImageData;
  export default content;
}

declare module '*.webp' {
  const content: StaticImageData;
  export default content;
}

declare module '*.ico' {
  const content: StaticImageData;
  export default content;
}

declare module '*.bmp' {
  const content: StaticImageData;
  export default content;
}

declare module '*.avif' {
  const content: StaticImageData;
  export default content;
}
