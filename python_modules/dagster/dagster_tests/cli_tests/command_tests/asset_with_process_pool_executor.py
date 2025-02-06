from concurrent.futures import ProcessPoolExecutor

import dagster
import tqdm


def f(x: int) -> int:
    return x * 2


@dagster.asset()
def multiprocess_asset() -> None:
    with ProcessPoolExecutor(max_workers=1) as pool:
        list(
            tqdm.tqdm(
                pool.map(f, range(1)),
                total=1,
            )
        )
