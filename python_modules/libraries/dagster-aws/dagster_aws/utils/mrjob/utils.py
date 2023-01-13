# This file duplicated from the Yelp MRJob project:
#
#   https://github.com/Yelp/mrjob
#
#
# -*- coding: utf-8 -*-
# Copyright 2013 Lyft
# Copyright 2015-2016 Yelp
# Copyright 2017 Yelp and Contributors
# Copyright 2019 Yelp and Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""General information about Amazon Web Services, such as region-to-endpoint
mappings. Also includes basic utilities for working with boto3.
"""

import socket
import ssl
from datetime import datetime, timedelta

import botocore
from dateutil.tz import tzutc

from .retry import RetryWrapper

### Utilities ###

# if AWS throttles us, how long to wait (in seconds) before trying again?
_AWS_BACKOFF = 20
_AWS_BACKOFF_MULTIPLIER = 1.5
_AWS_MAX_TRIES = 20  # this takes about a day before we run out of tries


def _client_error_code(ex):
    """Get the error code for the given ClientError."""
    return ex.response.get("Error", {}).get("Code", "")


def _client_error_status(ex):
    """Get the HTTP status for the given ClientError."""
    resp = ex.response
    # sometimes status code is in ResponseMetadata, not Error
    return resp.get("Error", {}).get("HTTPStatusCode") or resp.get("ResponseMetadata", {}).get(
        "HTTPStatusCode"
    )


def _is_retriable_client_error(ex):
    """Is the exception from a boto3 client retriable?"""
    if isinstance(ex, botocore.exceptions.ClientError):
        # these rarely get through in boto3
        code = _client_error_code(ex)
        # "Throttl" catches "Throttled" and "Throttling"
        if any(c in code for c in ("Throttl", "RequestExpired", "Timeout")):
            return True
        # spurious 505s thought to be part of an AWS load balancer issue
        return _client_error_status(ex) == 505
    # in Python 2.7, SSLError is a subclass of socket.error, so catch
    # SSLError first
    elif isinstance(ex, ssl.SSLError):
        # catch ssl.SSLError: ('The read operation timed out',). See #1827.
        # also catches 'The write operation timed out'
        return any(isinstance(arg, str) and "timed out" in arg for arg in ex.args)
    elif isinstance(ex, socket.error):
        return ex.args in ((104, "Connection reset by peer"), (110, "Connection timed out"))
    else:
        return False


def _wrap_aws_client(raw_client, min_backoff=None):
    """Wrap a given boto3 Client object so that it can retry when
    throttled.
    """
    return RetryWrapper(
        raw_client,
        retry_if=_is_retriable_client_error,
        backoff=max(_AWS_BACKOFF, min_backoff or 0),
        multiplier=_AWS_BACKOFF_MULTIPLIER,
        max_tries=_AWS_MAX_TRIES,
        unwrap_methods={"get_paginator"},
    )


def _boto3_now():
    """Get a ``datetime`` that's compatible with :py:mod:`boto3`.
    These are always UTC time, with time zone ``dateutil.tz.tzutc()``.
    """
    return datetime.now(tzutc())


def strip_microseconds(delta):
    """Return the given :py:class:`datetime.timedelta`, without microseconds.

    Useful for printing :py:class:`datetime.timedelta` objects.
    """
    return timedelta(delta.days, delta.seconds)
