import path from 'path';

import NextLink from 'next/link';
import React from 'react';

import {normalizeVersionPath, useVersion} from '../util/useVersion';

interface LinkProps {
  href: string;
  children: React.ReactNode;
  version?: string;
  passHref?: boolean;
}

{
  /*
  <Link href="/abcd"></Link>
  <Link href="/abcd" version={newVersion}></Link>
  <Link href="/version/abcd" version={newVersion}></Link>
*/
}

const Link = ({href, children, version, passHref = false}: LinkProps) => {
  const {asPath} = normalizeVersionPath(href);
  const {version: currentVersion, defaultVersion} = useVersion();

  if (version) {
    const versionedHref =
      version === defaultVersion ? path.join('/', asPath) : path.join('/', version, asPath);
    return (
      <NextLink legacyBehavior href={versionedHref} passHref={passHref}>
        {children}
      </NextLink>
    );
  }

  if (currentVersion === defaultVersion) {
    const versionedHref = path.join('/', href);
    return (
      <NextLink legacyBehavior href={versionedHref} passHref={passHref}>
        {children}
      </NextLink>
    );
  }

  const versionedHref = path.join('/', currentVersion, href);
  return (
    <NextLink legacyBehavior href={versionedHref} passHref={passHref}>
      {children}
    </NextLink>
  );
};

export default Link;
