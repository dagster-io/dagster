import errno
import os

from collections import namedtuple


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_step_key(context, step_idx):
    return '{run_id}_step_{step_idx}.pickle'.format(run_id=context.run_id, step_idx=step_idx)


def get_input_key(context, step_idx):
    return '{run_id}_intermediate_results_{step_idx}.pickle'.format(
        run_id=context.run_id, step_idx=step_idx
    )


def get_deployment_package_key(context, step_idx):
    return '{run_id}_deployment_package_{step_idx}.zip'.format(
        run_id=context.run_id, step_idx=step_idx
    )


def get_resources_key(context):
    return '{run_id}_resources.pickle'.format(run_id=context.run_id)


LambdaInvocationPayload = namedtuple(
    'LambdaInvocationPayload', 'run_id step_idx key s3_bucket s3_key_inputs s3_key_body '
    's3_key_resources s3_key_outputs'
)

####################################################################################################
# Copyright 2018 PyWren Team
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
# WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
"""
Generic utility functions for serialization
"""

import base64
import os

import glob2


def bytes_to_b64str(byte_data):
    byte_data_64 = base64.b64encode(byte_data)
    byte_data_64_ascii = byte_data_64.decode('ascii')
    return byte_data_64_ascii


def b64str_to_bytes(str_data):
    str_ascii = str_data.encode('ascii')
    byte_data = base64.b64decode(str_ascii)
    return byte_data


def create_mod_data(mod_paths):
    module_data = {}
    # load mod paths
    for m in mod_paths:
        if os.path.isdir(m):
            files = glob2.glob(os.path.join(m, "**/*.py"))
            pkg_root = os.path.abspath(os.path.dirname(m))
        else:
            pkg_root = os.path.abspath(os.path.dirname(m))
            files = [m]
        for f in files:
            f = os.path.abspath(f)
            mod_str = open(f, 'rb').read()

            dest_filename = f[len(pkg_root) + 1:].replace(os.sep, "/")
            module_data[dest_filename] = bytes_to_b64str(mod_str)

    return module_data


####################################################################################################
