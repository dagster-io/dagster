import React from 'react';
import Link from '@docusaurus/Link';
import Heading from '@theme/Heading';
interface CardProps {
  title: string;
  icon: string;
  href: string;
  children: React.ReactNode;
}

const Card: React.FC<CardProps> = ({title, icon, href, children}) => (
  <Link to={href} className="card">
    <Heading as="h3">{title}</Heading>
    <i className={`icon-${icon}`}></i>
    <p>{children}</p>
  </Link>
);

interface CardGroupProps {
  cols: number;
  children: React.ReactNode;
}

const CardGroup: React.FC<CardGroupProps> = ({cols, children}) => (
  <div className={`card-group cols-${cols}`}>{children}</div>
);

export {Card, CardGroup};
