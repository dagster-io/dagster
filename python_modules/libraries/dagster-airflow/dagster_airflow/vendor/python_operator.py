#
# NOTE: This file is vendored directly from apache-airflow==1.10.3 to avoid taking a dependency on
#       any specific Airflow version.
#
# -*- coding: utf-8 -*-
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import os

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.utils.operator_helpers import context_to_airflow_vars


class PythonOperator(BaseOperator):
    """
    Executes a Python callable

    .. seealso::
        For more information on how to use this operator, take a look at the guide:
        :ref:`howto/operator:PythonOperator`

    :param python_callable: A reference to an object that is callable
    :type python_callable: python callable
    :param op_kwargs: a dictionary of keyword arguments that will get unpacked
        in your function
    :type op_kwargs: dict (templated)
    :param op_args: a list of positional arguments that will get unpacked when
        calling your callable
    :type op_args: list (templated)
    :param provide_context: if set to true, Airflow will pass a set of
        keyword arguments that can be used in your function. This set of
        kwargs correspond exactly to what you can use in your jinja
        templates. For this to work, you need to define `**kwargs` in your
        function header.
    :type provide_context: bool
    :param templates_dict: a dictionary where the values are templates that
        will get templated by the Airflow engine sometime between
        ``__init__`` and ``execute`` takes place and are made available
        in your callable's context after the template has been applied. (templated)
    :type templates_dict: dict[str]
    :param templates_exts: a list of file extensions to resolve while
        processing templated fields, for examples ``['.sql', '.hql']``
    :type templates_exts: list[str]
    """

    template_fields = ("templates_dict", "op_args", "op_kwargs")
    ui_color = "#ffefeb"

    # since we won't mutate the arguments, we should just do the shallow copy
    # there are some cases we can't deepcopy the objects(e.g protobuf).
    shallow_copy_attrs = ("python_callable", "op_kwargs")

    @apply_defaults
    def __init__(  # pylint: disable=keyword-arg-before-vararg
        self,
        python_callable,
        op_args=None,
        op_kwargs=None,
        provide_context=False,
        templates_dict=None,
        templates_exts=None,
        *args,
        **kwargs,
    ):
        super(PythonOperator, self).__init__(*args, **kwargs)
        if not callable(python_callable):
            raise AirflowException("`python_callable` param must be callable")
        self.python_callable = python_callable
        self.op_args = op_args or []
        self.op_kwargs = op_kwargs or {}
        self.provide_context = provide_context
        self.templates_dict = templates_dict
        if templates_exts:
            self.template_ext = templates_exts

    def execute(self, context):
        # Export context to make it available for callables to use.
        airflow_context_vars = context_to_airflow_vars(context, in_env_var_format=True)
        self.log.info(
            "Exporting the following env vars:\n%s",
            "\n".join(["{}={}".format(k, v) for k, v in airflow_context_vars.items()]),
        )
        os.environ.update(airflow_context_vars)

        if self.provide_context:
            context.update(self.op_kwargs)
            context["templates_dict"] = self.templates_dict
            self.op_kwargs = context

        return_value = self.execute_callable()
        self.log.info("Done. Returned value was: %s", return_value)
        return return_value

    def execute_callable(self):
        return self.python_callable(*self.op_args, **self.op_kwargs)
