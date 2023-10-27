import NextLink from 'next/link';
import React from 'react';

interface LinkProps {
  href: string;
  children: React.ReactNode;
  passHref?: boolean;
}

{
  /*
  <Link href="/abcd"></Link>
*/
}

const Link = ({href, children, passHref = false}: LinkProps) => {
  return (
    <NextLink href={href} passHref={passHref} legacyBehavior>
      {children}
    </NextLink>
  );
};

export default Link;
