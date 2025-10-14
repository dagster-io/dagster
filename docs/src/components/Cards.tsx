import React, {type ReactNode} from 'react';
import type {PropSidebarItemLink} from '@docusaurus/plugin-content-docs';
import DocCard from '@theme/DocCard';

interface CardProps {
  label: string;
  href: string;
  description?: string;
  logo?: string;
  community?: boolean;
}

const Card: React.FC<CardProps> = ({label, href, description, logo, community}) => {
  const item: PropSidebarItemLink = {
    type: 'link',
    label,
    href,
    description,
    docId: undefined,
    customProps: {logo, community},
  };

  return <DocCard item={item} />;
};

export {Card};
