# -*- coding: utf-8 -*-
import time

import click
from click.testing import CliRunner
from dagster_aws.cli.term import Spinner, Term


def test_term():
    def term_helper(term_cmd, prefix, exit_code=0):
        @click.command()
        def fn():
            term_cmd('foo bar')

        runner = CliRunner()
        result = runner.invoke(fn)
        assert result.exit_code == exit_code
        assert result.output == prefix + u'foo bar\n'

    expected = [
        (Term.error, Term.ERROR_PREFIX),
        (Term.info, Term.INFO_PREFIX),
        (Term.success, Term.SUCCESS_PREFIX),
        (Term.waiting, Term.WAITING_PREFIX),
        (Term.warning, Term.WARNING_PREFIX),
    ]
    for term_cmd, prefix in expected:
        term_helper(term_cmd, prefix)

    term_helper(Term.fatal, Term.FATAL_PREFIX, exit_code=1)


def test_spinner(capsys):
    with Spinner():
        time.sleep(0.5)

    captured = capsys.readouterr()
    assert captured.out.encode('unicode-escape').startswith(
        b'\\u280b\\x08\\u2819\\x08\\u2839\\x08\\u2838\\x08'
    )
