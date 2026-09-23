import {createContext, useContext} from 'react';

/**
 * Whether the page is rendered in the mobile layout (nav drawer + floating menu button).
 * Provided by `AppContainer`; defaults to false, so pages and components can read it
 * without any provider in tests and stories.
 */
export const IsMobileContext = createContext(false);

export const useIsMobile = () => useContext(IsMobileContext);
