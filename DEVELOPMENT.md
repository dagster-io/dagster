Setup for developing the Dagit UI

1. Install Python 3.6.
  * You can't use Python 3.7+ yet because of https://github.com/apache/arrow/issues/1125

2. Create a virtual environment
  ```
  python3 -m venv ~/venvs/dagit/
  source ~/venvs/dagit/bin/activate
  pip
  ```

3. Install all the dependencies, and make the dagit and dagster packages available by name:
  ```
  cd ./dagster
  pip install -r dev-requirements.txt
  pip install -e .
  cd ../dagit
  pip install -r dev-requirements.txt
  pip install -e .
  ```

4. Run the GraphQL server from a directory that contains a repository.yml file.
   For example:

   ```
   cd ./dagster/dagster/dagster_examples
   python3.6 /path/to/python_modules/dagit/bin/dagit -p 3333
   ```

5. Run the JS component of the Dagit UI, pointing it to the GraphQL server:
  ```
  cd ./dagit/dagit/webapp
  yarn install
  REACT_APP_GRAPHQL_URI="http://localhost:3333/graphql" yarn start
  ```

6. You can run tests for python by running `tox` in `python_modules/dagit` or `python_modules/dagster`.

7. Inside webapp directory, you can run tests too. `yarn test` runs all tests. In development it's handy to run `yarn run jest --watch` to have interactive test runner.

8. Some webapp tests use *snapshots* - auto-generated results to which the test render tree is compared. Those tests are supposed to break when you change something, check that the change is sensible and run `yarn run jest -u` to update snapshot to the new result. You can also update snapshots interactively when you are in `--watch` mode.
