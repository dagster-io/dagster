import makefun
import dagster
import inspect


def solid_from_func(func):
    # (1a) capture the signature of func
    sig = inspect.signature(func)

    # (1b) modify the signature to add 'context' and drop default args and var args
    params = list(sig.parameters.values())
    params =\
        [x for x in params if
         (x.default == inspect.Parameter.empty)
         and (x.kind not in [inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL])]
    params.insert(0, inspect.Parameter('context', kind=inspect.Parameter.POSITIONAL_OR_KEYWORD))
    new_sig = sig.replace(parameters=params)

    # (2) create our solid
    @dagster.solid(config={})
    @makefun.wraps(func, new_sig=new_sig)
    def solid(context, *args, **kwargs):
        # call the original function
        return func(*args, **kwargs)

    return solid
