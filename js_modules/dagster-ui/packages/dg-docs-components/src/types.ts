import {ReactNode} from 'react';

export type Contents = Package[];

export type Package = {
  name: string;
  componentTypes: ComponentType[];
};

export type ComponentType = {
  name: string;
  author: string;
  example: string;
  schema: string;
  description: string;
  tags: string[];
};

export type DocsLinkProps = {
  href: string;
  className?: string;
  children: ReactNode;
};
