import React, { useEffect, useState } from "react";

import Link from "next/link";
import { useRouter } from "next/router";

interface VersionedLinkProps {
  href: string;
  children: JSX.Element;
}

const VersionedLink = ({ href, children }: VersionedLinkProps) => {
  const router = useRouter();
  const [locale, setLocale] = useState("master");

  useEffect(() => {
    if (router.isReady) {
      setLocale(router.locale);
    }
  }, [router]);

  return (
    <Link href={href} locale={locale}>
      {children}
    </Link>
  );
};

export default VersionedLink;
