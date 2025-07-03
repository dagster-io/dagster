import styles from './css/Version.module.css';

export const Version = ({children, className, ...props}: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={`${styles.version} ${className || ''}`} {...props}>
    {children}
  </div>
);
