import inspect

def a_generator():
    if True:
        return None
    # for i in range(5):
    #     yield i

def run_a_generator():
    result = a_generator()
    print(f"result {result}")

    if inspect.isgenerator(result) or isinstance(result, list):
        if inspect.isgenerator(result):
            print("result is generator")
        if isinstance(result, list):
            print("result is list")
        for item in result:
            print(f"item {item}")
            # yield item


run_a_generator()