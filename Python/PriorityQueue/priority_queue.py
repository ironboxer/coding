"""
基于多线程实现一个优先队列
"""

import time
import random
import logging
from heapq import heappush, heappop
from threading import Lock, Condition
from functools import total_ordering

formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s")
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

logger = logging.getLogger("root")
logger.addHandler(ch)


@total_ordering
class JobItem:
    
    def __init__(self, executing_ts, job):
        self.executing_ts = executing_ts
        self.job = job
        # ...
        
    def __eq__(self, other):
        return self.executing_ts == other.executing_ts
    
    def __lt__(self, other):
        return self.executing_ts < other.executing_ts


    def __str__(self):
        return "JobItem(%d)" % self.executing_ts


class PriorityQueue:

    def __init__(self):
        self.queue = []
        # 互斥锁
        self.mutex = Lock()
        # 条件对象
        self.more = Condition(self.mutex)

    def get(self):
        # 先加互斥锁
        with self.mutex:
            while True:
                if not self.queue:
                    # 堆为空则等待条件变量
                    # wait内部将释放互斥锁
                    self.more.wait()

                    # 条件变量满足，线程重新唤醒
                    # wait返回前，重新拿到互斥锁
                    # 睡眠这段时间，至少有一个生产者压入新任务
                    # 新任务有可能被其他线程抢走，因此需要重新检查堆是否为空
                    continue

                # 检查堆顶任务
                job_item = self.queue[0]
                logger.info("get job from queue: %s" % job_item)
                # 判断执行时间是否到达
                now = time.time()
                executing_ts = job_item.executing_ts
                if executing_ts > now:
                    # 执行时间未到，则继续等待，直到时间达到或者有生产者压入新任务
                    self.more.wait(executing_ts - now)
                    # 有新任务提交或者等待时间已到，重新检查堆状态
                    continue

                # 弹出堆顶元素并返回
                heappop(self.queue)
                return job_item

    def put(self, job_item):
        with self.mutex:
            # 将任务压入堆内，堆以执行时间排序
            heappush(self.queue, job_item)
            # 唤醒等待条件对象的其他线程
            self.more.notify()
            logger.info("put new job: %s" % job_item)



def job():
    import requests

    url = 'http://120.92.91.126:6006/api/single_img'
    logger.info("post %s" % url)
    img_path = '/Users/lttzzlll/Desktop/safe/safe.png'
    files = {'file':open(img_path, 'rb').read()}
    resp = requests.post(url, files=files)
    data = resp.json()
    bboxes_info = data['img']['bboxes']
    # print(bboxes_info)
    

class Producer:
    
    @classmethod
    def produce(cls):
        ts = int(time.time()) + random.randint(5, 15)
        return JobItem(ts, job)
    
    


class Consumer:
    @classmethod
    def pull(cls, queue):
        from threading import Thread
        
        def run():
            while True:
                job_item = queue.get()
                if job_item:
                    job_item.job()
            
        t = Thread(target=run)
        t.start()


if __name__ == '__main__':
    queue = PriorityQueue()
    Consumer.pull(queue)
    for i in range(10):
        job_item = Producer.produce()
        queue.put(job_item)
