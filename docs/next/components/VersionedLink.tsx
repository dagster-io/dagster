import Link from "next/link";
import { useRouter } from "next/router";
import React, { useState, useEffect } from "react";

interface VersionedLinkProps {
  href: string;
  children: JSX.Element;
}

const VersionedLink = ({ href, children }: VersionedLinkProps) => {
  // safely pass undefined router at the first render
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
