import React from 'react';
import Link from '@docusaurus/Link';
import Heading from '@theme/Heading';
interface CardProps {
  title: string;
  imagePath?: string;
  href: string;
  children: React.ReactNode;
}

const Card: React.FC<CardProps> = ({title, imagePath, href, children}) => (
  <Link to={href} className="card">
    {imagePath && (
      <img
        style={{
          marginBottom: '6px',
          background: 'var(--theme-color-background-default)',
          transition: 'background 0.5s',
        }}
        src={`${imagePath}`}
        alt={title}
        width="56"
        height="56"
      />
    )}
    <Heading as="h3">{title}</Heading>
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
