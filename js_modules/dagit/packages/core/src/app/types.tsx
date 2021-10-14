import {match} from 'react-router-dom';

export type RenderConfig<M, P> = {
  match: match<M>;
  permissions: P;
};

export type RouteConfig<M extends {[K in keyof M]?: string}, P> = {
  path: string;
  isAvailable?: (permissions: P) => boolean;
  render?: (config: RenderConfig<M, P>) => JSX.Element;
  routes?: RouteConfig<any, P>[];
};
