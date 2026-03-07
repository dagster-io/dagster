export const useFavoriteAssets = (): {
  loading: boolean;
  favorites: null | Set<string>;
} => ({loading: false, favorites: null});
