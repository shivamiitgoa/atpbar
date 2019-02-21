# Tai Sakuma <tai.sakuma@gmail.com>
import time, random
import multiprocessing

import pytest

from atpbar import atpbar
from atpbar import register_reporter, find_reporter, flush

##__________________________________________________________________||
@pytest.mark.skip() # This test sometime doesn't end. It is not because of a
                    # deadlock of atpbar.funcs._lock. It is because `queue` in
                    # this function doesn't join sometime for an unknown reason
def test_nested_multiprocessing_from_loop(mock_progressbar, wrap_end_pickup):

    def task(n, name):
        for i in atpbar(range(n), name=name):
            time.sleep(0.0001)

    def worker(reporter, task, queue):
        register_reporter(reporter)
        while True:
            args = queue.get()
            print(args)
            print(queue.empty())
            if args is None:
                queue.task_done()
                break
            task(*args)
            queue.task_done()

    nprocesses = 3
    processes = [ ]

    queue = multiprocessing.JoinableQueue()

    for i in atpbar(range(nprocesses)):
        reporter = find_reporter() # reporter is created here so as to let
                                   # atpbar own the pickup
        p = multiprocessing.Process(target=worker, args=(reporter, task, queue))
        p.start()
        processes.append(p)

        if i == nprocesses - 1:
            ntasks = 6
            for i in atpbar(range(ntasks)):
                name = 'task {}'.format(i)
                n = random.randint(5, 10)
                queue.put((n, name))
                time.sleep(0.01) # sleep to make sure atpbar in a
                                 # subprocess starts before this loop ends

    for i in range(nprocesses):
        queue.put(None)
        print('queue.put(None)')
        print(reporter.queue.empty())
        queue.join() # This doesn't join sometime
        print('queue.join()')

    print(wrap_end_pickup.call_count)
    flush()
    print(wrap_end_pickup.call_count)

    assert 1 == wrap_end_pickup.call_count
    assert len(mock_progressbar.present.call_args_list) >= 2 + 6*2

##__________________________________________________________________||