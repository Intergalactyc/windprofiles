import pandas as pd
from multiprocessing import Pool, Queue, Process
import os
from windprofiles.user.logs import log_listener, configure_worker
from tqdm import tqdm
import signal

pd.options.mode.chained_assignment = None


def _init(queue):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    configure_worker(queue)


def analyze_directory(
    path: str | os.PathLike | list,
    analysis,
    logfile,
    rules: dict|None = None,
    nproc=1,
    limit=None,
    progress=False,
    **kwargs,
) -> list:
    # analysis should be a function which takes a single arg (to unpack as `filepath, {rules (if not None)}, <kwargs>`) and returns a dict

    if isinstance(path, list):
        initlist = path
    else:
        dir_path = os.path.abspath(path)
        initlist = [
            os.path.join(dir_path, filename) for filename in os.listdir(path)
        ]
    if rules is None:
        if len(kwargs) == 0:
            directory = initlist
        else:
            directory = [(f, *kwargs) for f in initlist]
    else:
        directory = [(f, rules, *kwargs) for f in initlist]
    if limit is not None:
        directory = directory[:limit]

    if progress:
        pbar = tqdm(total=len(directory))

    queue = Queue(-1)

    listener = Process(target=log_listener, args=(queue, logfile), daemon=True)
    listener.start()

    pool = Pool(
        processes=max(1, nproc - 1),
        initializer=_init,
        initargs=(queue,),
        maxtasksperchild=3,
    )

    results = []
    for res in pool.imap(analysis, directory):
        results.append(res)
        if pbar:
            pbar.update()
            pbar.refresh()
    pool.close()
    pool.join()

    return results
