/* eslint-disable import/no-default-export */

/// <reference types="next" />

declare module 'amator';

declare module '@vx/gradient';
declare module '@vx/group';
declare module '@vx/network';
declare module '@vx/shape';
declare module '@vx/legend';
declare module '@vx/scale';
declare module '@vx/responsive';

declare module '*.mp4' {
  const src: string;
  export default src;
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

declare module '*.css' {
  const content: Record<string, string>;
  export default content;
}
