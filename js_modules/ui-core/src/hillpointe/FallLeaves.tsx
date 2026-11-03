import {Button, DagsterTheme, Icon} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {useEffect, useState} from 'react';

import styles from './css/FallLeaves.module.css';
import {useThemeState} from '../app/useThemeState';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

// Leaves drift down across the screen, settle into a pile along the bottom,
// and a rake button sweeps the pile away. Only rendered on the Fall theme, and can be
// switched off in user settings.

const LEAVES_STORAGE_KEY = 'hillpointe-fall-leaves';

export const useFallLeavesEnabled = () =>
  useStateWithStorage(LEAVES_STORAGE_KEY, (value: any) =>
    typeof value === 'boolean' ? value : true,
  );

const COLORS = ['%23e8742a', '%23c9a227', '%23b8322a'];
const LEAF_PATH = 'M21 3C12 3 4 8 3 19c0 1 0 2 1 2 2-5 6-9 11-12-4 4-7 8-9 13 9 0 15-7 15-19z';

const leafImage = (fill: string) =>
  `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='${fill}'%3E%3Cpath d='${LEAF_PATH}'/%3E%3C/svg%3E")`;

type Leaf = {
  id: number;
  left: number; // vw
  size: number; // px
  duration: number; // s
  tilt: number; // deg, once landed
  image: string;
};

const SPAWN_EVERY_MS = 5000;
const MAX_FALLING = 2;
const MAX_PILE = 40;
const RAKE_MS = 700;

let nextId = 1;

const makeLeaf = (): Leaf => ({
  id: nextId++,
  left: 2 + Math.random() * 92,
  size: 18 + Math.round(Math.random() * 10),
  duration: 10 + Math.random() * 6,
  tilt: Math.round(Math.random() * 80 - 40),
  image: leafImage(COLORS[Math.floor(Math.random() * COLORS.length)] ?? '%23e8742a'),
});

export const FallLeaves = () => {
  const {theme} = useThemeState();
  const [enabled] = useFallLeavesEnabled();
  const active = enabled && theme === DagsterTheme.Fall;

  const [falling, setFalling] = useState<Leaf[]>([]);
  const [pile, setPile] = useState<Leaf[]>([]);
  const [raking, setRaking] = useState(false);

  useEffect(() => {
    if (!active) {
      setFalling([]);
      setPile([]);
      return;
    }
    const timer = setInterval(() => {
      setFalling((leaves) => (leaves.length >= MAX_FALLING ? leaves : [...leaves, makeLeaf()]));
    }, SPAWN_EVERY_MS);
    return () => clearInterval(timer);
  }, [active]);

  if (!active) {
    return null;
  }

  const land = (leaf: Leaf) => {
    setFalling((leaves) => leaves.filter((l) => l.id !== leaf.id));
    setPile((leaves) => (leaves.length >= MAX_PILE ? leaves : [...leaves, leaf]));
  };

  const rake = () => {
    setRaking(true);
    setTimeout(() => {
      setPile([]);
      setRaking(false);
    }, RAKE_MS);
  };

  return (
    <>
      {falling.map((leaf) => (
        <div
          key={leaf.id}
          className={clsx(styles.leaf, styles.falling)}
          style={{
            left: `${leaf.left}vw`,
            width: leaf.size,
            height: leaf.size,
            animationDuration: `${leaf.duration}s`,
            backgroundImage: leaf.image,
            ['--land' as string]: `calc(100vh + 40px - ${leaf.size}px)`,
          }}
          onAnimationEnd={() => land(leaf)}
        />
      ))}
      {pile.map((leaf, i) => (
        <div
          key={leaf.id}
          className={clsx(styles.leaf, styles.landed, raking ? styles.raked : null)}
          style={{
            left: `${leaf.left}vw`,
            bottom: (i % 3) * 6,
            width: leaf.size,
            height: leaf.size,
            transform: `rotate(${leaf.tilt}deg)`,
            backgroundImage: leaf.image,
          }}
        />
      ))}
      {pile.length > 0 ? (
        <div className={styles.rake}>
          <Button icon={<Icon name="eco" />} onClick={rake} disabled={raking}>
            Rake leaves ({pile.length})
          </Button>
        </div>
      ) : null}
    </>
  );
};
