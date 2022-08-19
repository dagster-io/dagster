from dagster import asset

@asset
def a():
    return 1

@asset
def b():
    return 2

@asset
def c(a):
    return a + 1

@asset
def d(b):
    return b + 1

@asset
def e(a, b):
    return a + b + 1

@asset
def f(d):
    return d + 1

@asset
def g(d):
    return d + 2

