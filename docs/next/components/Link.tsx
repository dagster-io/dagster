import React, { useEffect, useState } from "react";
import { normalizeVersionPath, useVersion } from "../util/useVersion";

import NextLink from "next/link";
import path from "path";
import { useRouter } from "next/router";

interface LinkProps {
  href: string;
  children: JSX.Element;
  version?: string;
}

{
  /*
  <Link href="/abcd"></Link>
  <Link href="/abcd" version={newVersion}></Link>
  <Link href="/version/abcd" version={newVersion}></Link>
*/
}

const Link = ({ href, children, version }: LinkProps) => {
  const { asPath } = normalizeVersionPath(href);
  const { version: currentVersion, defaultVersion } = useVersion();

  if (version) {
    const versionedHref =
      version === defaultVersion
        ? path.join("/", asPath)
        : path.join("/", version, asPath);
    return <NextLink href={versionedHref}>{children}</NextLink>;
  }

  if (currentVersion === defaultVersion) {
    const versionedHref = path.join("/", href);
    return <NextLink href={versionedHref}>{children}</NextLink>;
  }

  const versionedHref = path.join("/", currentVersion, href);
  return <NextLink href={versionedHref}>{children}</NextLink>;
};

export default Link;
