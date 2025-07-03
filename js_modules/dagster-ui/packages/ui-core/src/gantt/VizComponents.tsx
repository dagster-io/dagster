import styles from './css/VizComponents.module.css';

export const OptionsContainer = (props: React.HTMLAttributes<HTMLDivElement>) => (
  <div {...props} className={`${styles.optionsContainer} ${props.className || ''}`} />
);

export const OptionsDivider = (props: React.HTMLAttributes<HTMLDivElement>) => (
  <div {...props} className={`${styles.optionsDivider} ${props.className || ''}`} />
);

export const OptionsSpacer = (props: React.HTMLAttributes<HTMLDivElement>) => (
  <div {...props} className={`${styles.optionsSpacer} ${props.className || ''}`} />
);
