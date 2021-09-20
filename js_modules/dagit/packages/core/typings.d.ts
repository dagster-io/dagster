declare module '@vx/gradient';
declare module '@vx/group';
declare module '@vx/network';
declare module '@vx/shape';
declare module '@vx/legend';
declare module '@vx/scale';
declare module '@vx/responsive';

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

declare module 'worker-loader!*' {
  class WebpackWorker extends Worker {
    constructor();
  }

  // eslint-disable-next-line import/no-default-export
  export default WebpackWorker;
}

declare module 'chartjs-adapter-date-fns';
