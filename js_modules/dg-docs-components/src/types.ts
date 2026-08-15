import {ReactNode} from 'react';

export type Contents = Package[];

export type Package = {
  name: string;
  componentTypes: ComponentType[];
};

export type ComponentType = {
  name: string;
  example: string;
  schema: string;
  description: string | null;
  owners: string[];
  tags: string[];
  /**
   * Whether this component type can be created and edited from the UI form
   * (i.e. its author opted in via ``ComponentFormConfig(editable=True)``).
   * Optional so external consumers of this package are unaffected.
   */
  isAppManaged?: boolean;
};

export type DocsLinkProps = {
  key: string;
  href: string;
  className?: string;
  children: ReactNode;
};
