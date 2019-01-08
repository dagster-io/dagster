#!/usr/bin/env bash
#dagstermill --module-name dagstermill.dagstermill_tests.repository --fn-name define_example_repository --notebook notebooks/CLI_example -s notebook_solid 
#dagstermill --notebook notebooks/CLI_from_YML -s notebook_solid
dagstermill -f file_name.py --fn-name random_fn_name --notebook notebooks/CLI_from_file -s notebook_solid
dagstermill --notebook notebooks/CLI_default_solid_name
dagstermill --notebook notebooks/CLI_jupyter --jupyter
