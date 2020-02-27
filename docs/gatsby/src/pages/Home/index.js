/** @jsx jsx */
import { jsx, Grid } from "theme-ui";

import { Layout } from "systems/Core";
import logo from "../../images/symbol.png";
import photoIcon from "./images/photo-icon.svg";
import graphIcon from "./images/graph-icon.svg";
import shieldIcon from "./images/shield-icon.svg";

import * as styles from "./styles";

export const Home = () => {
  return (
    <Layout>
      <div sx={styles.firstBlock}>
        <img src={logo} width={120} />
        <h1>
          A better way to build <span>modern data applications</span>
        </h1>
      </div>
      <div sx={styles.secondBlock}>
        <div>
          <img src={photoIcon} sx={styles.icon} width={50} />
          <h2>Elegant Programming Model</h2>
          <p>
            Dagster is a set of abstractions for building self-describing,
            testable, and reliable data applications. It embraces the
            principales of functional data programming; gradual, optional
            typing; and testability as a first-class value.
          </p>
        </div>
        <div>
          <img src={graphIcon} sx={styles.icon} width={50} />
          <h2>Beautiful Tools</h2>
          <p>
            Dagster's development environment, dagit - designed for data
            engineers, machine learning engineers, data scientists - enables
            astoundingly productive local development.
          </p>
        </div>
        <div>
          <img src={shieldIcon} sx={styles.icon} width={50} />
          <h2>Flexible and Incremental</h2>
          <p>
            Dagster integrates with your existing tools and infrastructure, and
            can invoke any computation-wheter it be Spark, Python, a Jupyter
            notebook, or SQL. It is algo designed to deploy to any workflow
            engine, such as Airflow.
          </p>
        </div>
      </div>
    </Layout>
  );
};
