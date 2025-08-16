import React, {useState, useEffect} from 'react';
import Link from '@docusaurus/Link';
import Logo from '@theme/Logo';

export default function NavbarLogo() {
  const [menuPosition, setMenuPosition] = useState<{x: number; y: number} | null>(null);

  useEffect(() => {
    const handleClick = () => setMenuPosition(null);
    if (menuPosition) {
      document.addEventListener('click', handleClick);
    }
    return () => {
      document.removeEventListener('click', handleClick);
    };
  }, [menuPosition]);

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setMenuPosition({x: e.clientX, y: e.clientY});
  };

  return (
    <>
      <Logo
        className="navbar__brand"
        imageClassName="navbar__logo"
        titleClassName="navbar__title text--truncate"
        onContextMenu={handleContextMenu}
      />
      {menuPosition && (
        <ul className="navbar-logo-menu" style={{position: 'fixed', top: menuPosition.y, left: menuPosition.x}}>
          <li>
            <Link href="/img/dagster-docs-logo.svg" download>
              Download SVG
            </Link>
          </li>
          <li>
            <Link href="https://dagster.io" target="_blank" rel="noopener noreferrer">
              Visit Dagster Website
            </Link>
          </li>
        </ul>
      )}
    </>
  );
}
