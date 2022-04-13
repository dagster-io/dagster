declare module '@vx/shape';

declare module '*.json' {
  const value: any;
  // eslint-disable-next-line import/no-default-export
  export default value;
}

declare module '*.png' {
  const value: string;
  // eslint-disable-next-line import/no-default-export
  export default value;
}

declare module '*.svg' {
  const content: any;
  // eslint-disable-next-line import/no-default-export
  export default content;
}

declare module 'worker-loader!*' {
  class WebpackWorker extends Worker {
    constructor();
  }

  // eslint-disable-next-line import/no-default-export
  export default WebpackWorker;
}

declare module 'chartjs-adapter-date-fns';
