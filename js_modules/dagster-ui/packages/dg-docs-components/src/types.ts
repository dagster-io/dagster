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
  description: string;
  owners: string[];
  tags: string[];
};

export type DocsLinkProps = {
  key: string;
  href: string;
  className?: string;
  children: ReactNode;
};
