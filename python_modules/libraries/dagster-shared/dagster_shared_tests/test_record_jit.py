from dataclasses import dataclass

from dagster_shared.record import record


def test_jit_check_collision():
    @record
    class Spec:
        name: list[str]

    @dataclass
    class LeakingClass:
        name: str

    checks = [LeakingClass("dont"), LeakingClass("leak"), LeakingClass("pls")]
    specs = []

    for check in checks:
        specs.append(
            Spec(
                name=[check.name],
            )
        )


def test_check_arg():
    @record
    class Test:
        check: list[str]

    arg = ["a", "b"]
    assert Test(check=arg).check == arg
