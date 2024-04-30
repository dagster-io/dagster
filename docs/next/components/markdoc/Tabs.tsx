import {Tab} from '@headlessui/react';
import {PersistentTabContext} from 'components/PersistentTabContext';
import React, {useEffect, useState, useCallback} from 'react';

const useHash = (): string => {
  const [hash, setHash] = React.useState(() => {
    return typeof window === 'undefined' ? '' : window.location.hash;
  });

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const handler = () => {
      setHash(window.location.hash);
    };

    window.addEventListener('hashchange', handler);
    return () => {
      window.removeEventListener('hashchange', handler);
    };
  }, []);

  return hash;
};

interface TabItem {
  name: string;
  children: any;
}
export const TabItem = (_: TabItem) => {}; // container to pass through name and children

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

export const TabGroup: React.FC<{children: any; persistentKey?: string}> = ({
  children,
  persistentKey,
}) => {
  const [selectedTab, setSelectedTab] = useState(0);
  const anchor = useHash();

  const [anchorsInChildren, setAnchorsInChildren] = useState<{[anchor: string]: number}>({});
  const handleTabs = useCallback((node: HTMLElement) => {
    if (!node) {
      return;
    }
    const out = {};

    // Once the tabs render, get the list of element IDs and the map to the
    // tab index they are in
    const tabs = node.querySelectorAll("[role='tabpanel']");
    for (let i = 0; i < tabs.length; i++) {
      const tab = tabs[i] as HTMLElement;
      for (const element of tab.querySelectorAll('[id]')) {
        out[element.id] = i;
      }
    }
    setAnchorsInChildren(out);
  }, []);

  useEffect(() => {
    const anchorWithoutHash = anchor.substring(1);
    if (anchorWithoutHash in anchorsInChildren) {
      const tabIdx = anchorsInChildren[anchorWithoutHash];

      // Scroll page to the hash after re-render
      setSelectedTab(tabIdx);
      setTimeout(() => {
        const elem = document.getElementById(anchorWithoutHash);
        elem?.scrollIntoView();
      }, 10);
    }
  }, [anchor, anchorsInChildren]);

  const contents = (
    <>
      <Tab.List className="flex space-x-2 m-2">
        {React.Children.map(children, (child, idx) => {
          return (
            <Tab
              key={idx}
              className={({selected}) =>
                classNames(
                  'w-full py-3 text-sm font-bold leading-5',
                  'focus:outline-none border-gray-200',
                  selected
                    ? 'border-b-2 border-primary-500 text-primary-500 bg-gray-150'
                    : 'border-b hover:border-gray-500 hover:text-gray-700',
                )
              }
            >
              {child?.props?.name}
            </Tab>
          );
        })}
      </Tab.List>
      <Tab.Panels ref={handleTabs}>
        {React.Children.map(children, (child, idx) => {
          // Set unmount={false} to ensure all tabs render (some are hidden)
          // this way we can gather all the ids in the tab group
          console.log(child);
          return (
            <Tab.Panel key={idx} className={classNames('p-3')} unmount={false}>
              {React.Children.toArray(child.props.children)}
            </Tab.Panel>
          );
        })}
      </Tab.Panels>
    </>
  );

  return (
    <div className="w-full px-2 py-2 sm:px-0">
      {persistentKey ? (
        <PersistentTabContext.Consumer>
          {(context) => (
            <Tab.Group
              selectedIndex={context.getTabState(persistentKey)}
              onChange={(idx) => context.setTabState(persistentKey, idx)}
            >
              {contents}
            </Tab.Group>
          )}
        </PersistentTabContext.Consumer>
      ) : (
        <Tab.Group selectedIndex={selectedTab} onChange={(idx) => setSelectedTab(idx)}>
          {contents}
        </Tab.Group>
      )}
    </div>
  );
};
