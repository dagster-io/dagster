import clsx from 'clsx';
import {Fragment, HTMLProps, ReactNode, useLayoutEffect, useState} from 'react';

import styles from './css/PackageTree.module.css';

import {Contents} from './types';

function extractFromPathname(pathname: string) {
  const [selectedPkg, selectedComponent] = pathname.split('/').slice(2);
  return {selectedPkg, selectedComponent};
}
interface Props {
  contents: Contents | null;
  pathname: string;
  renderLink: (props: HTMLProps<HTMLAnchorElement>) => ReactNode;
}

export default function PackageTree({contents, pathname, renderLink}: Props) {
  const {selectedPkg, selectedComponent} = extractFromPathname(pathname);
  const [expandedPkgs, setExpandedPkgs] = useState<Set<string>>(
    () => new Set(selectedPkg ? [selectedPkg] : []),
  );

  useLayoutEffect(() => {
    setExpandedPkgs((current) => {
      const {selectedPkg} = extractFromPathname(pathname);
      const copy = new Set(current);
      if (selectedPkg) {
        copy.add(selectedPkg);
      }
      return copy;
    });
  }, [pathname]);

  const [search, setSearch] = useState('');

  const onTogglePkg = (pkg: string) => {
    setExpandedPkgs((prev) => {
      const copy = new Set(prev);
      if (copy.has(pkg)) {
        copy.delete(pkg);
      } else {
        copy.add(pkg);
      }
      return copy;
    });
  };

  return (
    <div className={styles.container}>
      <div className={styles.searchOuter}>
        <div className={styles.searchContainer}>
          <svg
            className={styles.icon}
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="currentColor"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M12.9167 11.6667H12.2583L12.025 11.4417C12.8699 10.4617 13.3343 9.21058 13.3333 7.91667C13.3333 6.84535 13.0157 5.7981 12.4205 4.90733C11.8253 4.01656 10.9793 3.3223 9.98954 2.91232C8.99977 2.50235 7.91066 2.39508 6.85993 2.60408C5.8092 2.81309 4.84404 3.32897 4.08651 4.08651C3.32897 4.84404 2.81309 5.8092 2.60408 6.85993C2.39508 7.91066 2.50235 8.99977 2.91232 9.98954C3.3223 10.9793 4.01656 11.8253 4.90733 12.4205C5.7981 13.0157 6.84535 13.3333 7.91667 13.3333C9.25834 13.3333 10.4917 12.8417 11.4417 12.025L11.6667 12.2583V12.9167L15.8333 17.075L17.075 15.8333L12.9167 11.6667ZM7.91667 11.6667C5.84167 11.6667 4.16667 9.99167 4.16667 7.91667C4.16667 5.84167 5.84167 4.16667 7.91667 4.16667C9.99167 4.16667 11.6667 5.84167 11.6667 7.91667C11.6667 9.99167 9.99167 11.6667 7.91667 11.6667Z"
              fill="currentColor"
            />
          </svg>
          <input
            type="text"
            placeholder="Jump to…"
            value={search}
            className={styles.search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>
      <div className={styles.treeContainer}>
        {contents?.map((pkg) => (
          <div key={pkg.name}>
            <div className={styles.pkgItem}>
              <button
                className={clsx(
                  styles.expandButton,
                  expandedPkgs.has(pkg.name) ? styles.expanded : null,
                )}
                onClick={() => onTogglePkg(pkg.name)}
              >
                <svg
                  className={styles.chevron}
                  width="20"
                  height="20"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M5.83301 8.33337L9.99967 12.5L14.1663 8.33337H5.83301Z"
                    fill="currentColor"
                  />
                </svg>
              </button>
              {renderLink({
                href: `/packages/${pkg.name}`,
                className: clsx(
                  styles.pkgLink,
                  expandedPkgs.has(pkg.name) ? styles.expanded : null,
                  selectedPkg === pkg.name && !selectedComponent ? styles.selected : null,
                ),
                children: (
                  <>
                    <TempFolderIcon />
                    <div className={styles.pkgName}>{pkg.name}</div>
                  </>
                ),
              })}
            </div>
            {expandedPkgs.has(pkg.name) ? (
              <div className={styles.componentList}>
                {pkg.componentTypes.map((componentType) => {
                  const isSelected =
                    selectedPkg === pkg.name && selectedComponent === componentType.name;
                  return (
                    <Fragment key={componentType.name}>
                      {renderLink({
                        href: `/packages/${pkg.name}/${componentType.name}`,
                        className: clsx(styles.componentLink, isSelected ? styles.selected : null),
                        children: (
                          <>
                            <TempIcon />
                            <span className={styles.componentName}>{componentType.name}</span>
                          </>
                        ),
                      })}
                    </Fragment>
                  );
                })}
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

const TempFolderIcon = () => {
  return (
    <svg
      className={styles.icon}
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M16.667 5.00004H10.0003L8.33366 3.33337H3.33366C2.41699 3.33337 1.67533 4.08337 1.67533 5.00004L1.66699 15C1.66699 15.9167 2.41699 16.6667 3.33366 16.6667H16.667C17.5837 16.6667 18.3337 15.9167 18.3337 15V6.66671C18.3337 5.75004 17.5837 5.00004 16.667 5.00004ZM16.667 15H3.33366V6.66671H16.667V15Z"
        fill="currentColor"
      />
    </svg>
  );
};

const TempIcon = () => {
  return (
    <svg
      className={styles.icon}
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M9.16667 16.1875V10.4791L4.16667 7.58329V13.2916L9.16667 16.1875ZM10.8333 16.1875L15.8333 13.2916V7.58329L10.8333 10.4791V16.1875ZM10 9.04163L14.9375 6.18746L10 3.33329L5.0625 6.18746L10 9.04163ZM3.33333 14.75C3.06944 14.5972 2.86458 14.3958 2.71875 14.1458C2.57292 13.8958 2.5 13.618 2.5 13.3125V6.68746C2.5 6.3819 2.57292 6.10413 2.71875 5.85413C2.86458 5.60413 3.06944 5.40274 3.33333 5.24996L9.16667 1.89579C9.43056 1.74301 9.70833 1.66663 10 1.66663C10.2917 1.66663 10.5694 1.74301 10.8333 1.89579L16.6667 5.24996C16.9306 5.40274 17.1354 5.60413 17.2812 5.85413C17.4271 6.10413 17.5 6.3819 17.5 6.68746V13.3125C17.5 13.618 17.4271 13.8958 17.2812 14.1458C17.1354 14.3958 16.9306 14.5972 16.6667 14.75L10.8333 18.1041C10.5694 18.2569 10.2917 18.3333 10 18.3333C9.70833 18.3333 9.43056 18.2569 9.16667 18.1041L3.33333 14.75Z"
        fill="currentColor"
      />
    </svg>
  );
};
