import {ReactNode, createContext, useContext} from 'react';

import {ComponentType} from './types';

/**
 * Lets a consuming app render a badge next to a component type (e.g. in the
 * package tree and component header) without this package depending on the
 * app's component library. The default renders nothing, so consumers that do
 * not provide a renderer are unaffected.
 */
export type RenderComponentBadge = (
  component: ComponentType,
  options?: {compact?: boolean},
) => ReactNode;

const ComponentBadgeContext = createContext<RenderComponentBadge>(() => null);

export const ComponentBadgeProvider = ComponentBadgeContext.Provider;

export function useComponentBadge(): RenderComponentBadge {
  return useContext(ComponentBadgeContext);
}
