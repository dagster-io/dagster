import {useStateWithStorage} from '../../hooks/useStateWithStorage';

// Also read outside React at boot by `detectLayoutMode`, so a change applies on the next load.
export const PREFER_DESKTOP_SITE_STORAGE_KEY = 'preferDesktopSite';

export const validatePreferDesktopSite = (value: any) =>
  typeof value === 'boolean' ? value : false;

export const usePreferDesktopSite = () => {
  const [preferDesktopSite, setPreferDesktopSite] = useStateWithStorage(
    PREFER_DESKTOP_SITE_STORAGE_KEY,
    validatePreferDesktopSite,
  );

  return {preferDesktopSite, setPreferDesktopSite};
};
