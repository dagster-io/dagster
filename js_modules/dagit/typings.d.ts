declare module "@vx/gradient";
declare module "@vx/group";
declare module "@vx/network";
declare module "@vx/shape";
declare module "@vx/legend";
declare module "@vx/scale";
declare module "@vx/responsive";

declare module "*.json" {
  const value: any;
  export default value;
}

declare module "worker-loader!*" {
  class WebpackWorker extends Worker {
    constructor();
  }

  export default WebpackWorker;
}
