import {useCatalogViews} from 'shared/assets/catalog/useCatalogViews.oss';

export type ViewType =
  | ReturnType<typeof useCatalogViews>['privateViews'][number]
  | ReturnType<typeof useCatalogViews>['publicViews'][number];
