import Link from "next/link";
import { useRouter } from "next/router";

interface VersionedLinkProps {
  href: string;
  children: JSX.Element;
}

const VersionedLink = ({ href, children }: VersionedLinkProps) => {
  const { locale } = useRouter();

  return (
    <Link href={href} locale={locale}>
      {children}
    </Link>
  );
};

export default VersionedLink;
