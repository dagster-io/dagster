"use client";

import {Contents} from "@/util/types";

import styles from "./css/PackageTree.module.css";
import clsx from "clsx";
import {usePathname} from "next/navigation";
import Link from "next/link";
import {useState} from "react";

interface Props {
  contents: Contents | null;
}

export default function PackageTree({contents}: Props) {
  const pathname = usePathname();

  const [selectedPkg, selectedComponent] = pathname.split("/").slice(2);
  const [expandedPkgs, setExpandedPkgs] = useState<Set<string>>(
    () => new Set(selectedPkg ? [selectedPkg] : [])
  );

  const [search, setSearch] = useState("");

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
            <Link
              href={`/packages/${pkg.name}`}
              className={clsx(
                styles.pkgLink,
                expandedPkgs.has(pkg.name) ? styles.expanded : null,
                selectedPkg === pkg.name && !selectedComponent
                  ? styles.selected
                  : null
              )}
              onClick={() => {
                onTogglePkg(pkg.name);
              }}
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
              <div className={styles.pkgName}>{pkg.name}</div>
            </Link>
            {expandedPkgs.has(pkg.name) ? (
              <div className={styles.componentList}>
                {pkg.componentTypes.map((componentType) => {
                  const isSelected =
                    selectedPkg === pkg.name &&
                    selectedComponent === componentType.name;
                  return (
                    <Link
                      key={componentType.name}
                      href={`/packages/${pkg.name}/${componentType.name}`}
                      className={clsx(
                        styles.componentLink,
                        isSelected ? styles.selected : null
                      )}
                    >
                      {componentType.name}
                    </Link>
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
