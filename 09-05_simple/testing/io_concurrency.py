"""
example script from realpython.com comparing concurrent to non-concurrent io scripts
"""

"""

# https://realpython.com/python-concurrency/#asynchronous-version  

> A coroutine is similar to a thread but much more lightweight and cheaper to suspend or resume. That's what makes it possible to spawn many more coroutines than threads without a significant memory or performance overhead.

> But there's a catch.

> You can't have blocking function calls in your coroutines if you want to reap the full benefits of asynchronous programming. A blocking call is a synchronous one, meaning that it prevents other code from running while it's waiting for data to arrive. In contrast, a non-blocking call can voluntarily give up control and wait to be notified when the data is ready.


=> if the asyncio event loop waits for a stuck task to finish, everyone else has to wait

"""



#MARK: single-threaded

# import time

# import requests

# def main():
#     sites = [
#         "https://www.jython.org",
#         "http://olympus.realpython.org/dice",
#     ] * 80
#     start_time = time.perf_counter()
#     download_all_sites(sites)
#     duration = time.perf_counter() - start_time
#     print(f"Downloaded {len(sites)} sites in {duration} seconds") # Downloaded 160 sites in 16.713... seconds"

# def download_all_sites(sites):
#     with requests.Session() as session:
#         for url in sites:
#             download_site(url, session)

# def download_site(url, session):
#     with session.get(url) as response:
#         print(f"Read {len(response.content)} bytes from {url}")

# if __name__ == "__main__":
#     main()
    
#MARK: done in = 16.7s    





#==================================================================================================
    
    
    
    
#MARK: multi-threaded    
# import threading
# import time
# from concurrent.futures import ThreadPoolExecutor # ThreadPoolExecutor also handles thread-safety for otherwise unsafe requests.Session()

# import requests

# # thread-logal storage
# # essentially creates an object similar to a global variable, but specific to each individual thread
# # you only create one (not one per thread), it takes care of the access handling itself!
# thread_local = threading.local()


# def main():
#     sites = [
#         "https://www.jython.org",
#         "http://olympus.realpython.org/dice",
#     ] * 80
#     start_time = time.perf_counter()
#     download_all_sites(sites)
#     duration = time.perf_counter() - start_time
#     print(f"Downloaded {len(sites)} sites in {duration} seconds")

# def download_all_sites(sites):
#     with ThreadPoolExecutor(max_workers=40) as executor:
#         executor.map(download_site, sites)

# def download_site(url):
#     session = get_session_for_thread()
#     with session.get(url) as response:
#         print(f"Read {len(response.content)} bytes from {url}")

# def get_session_for_thread():
#     if not hasattr(thread_local, "session"):
#         thread_local.session = requests.Session()
#     return thread_local.session

# if __name__ == "__main__":
#     main()
    
#MARK: 5 workers = 3.6s
#  1 = 16.35s
#  2 =  8.15s
#  5 =  3.54s
# 10 =  2.47s
# 40 =  2.47s (1.46, 1.36, timeout on 4th try)
# 80 =  2.39s


#==================================================================================================
  


#MARK: async version

import asyncio
import time

import aiohttp # replaces requests (which is blocking), with one built for asyncio

async def main():
    sites = [
        "https://www.jython.org",
        "http://olympus.realpython.org/dice",
    ] * 80
    start_time = time.perf_counter()
    await download_all_sites(sites) # suspends execution here, until all sites downloaded
    duration = time.perf_counter() - start_time
    print(f"Downloaded {len(sites)} sites in {duration} seconds")

async def download_all_sites(sites):
    async with aiohttp.ClientSession() as session:
        tasks = [download_site(url, session) for url in sites] # this is really neat
        await asyncio.gather(*tasks, return_exceptions=True) # runs all tasks concurrently, waits for all of them to finish

async def download_site(url, session):
    async with session.get(url) as response:
        # split into individual operations
        response_bytes = await response.read()
        length_of_response = len(response_bytes)
        print(f"Read {length_of_response} bytes from {url}")
        
        # as the individual task finishes inside the asyncio.gather(), it prints its result
        # original version
        # print(f"Read {len(await response.read())} bytes from {url}") 

if __name__ == "__main__":
    asyncio.run(main())
    
#MARK: done in 0.66s !
# it's super fast, because it simply automatically assigns one task per site
# no need to set a number of workers like in multi-threading (possible, because tasks take far fewer resources than threads)



#==================================================================================================


#MARK: multiprocessing
# https://realpython.com/python-concurrency/#process-based-version
# can use multiple cores, by simply starting a new python interpreter to run on each of them
# takes a bit of time to start, but for cpu-bound stuff, it's obviously great  
# one big issue: communication between them is a real hassle (and slow)

# import atexit
# import multiprocessing
# import time
# from concurrent.futures import ProcessPoolExecutor

# import requests

# session: requests.Session

# def main():
#     sites = [
#         "https://www.jython.org",
#         "http://olympus.realpython.org/dice",
#     ] * 80
#     start_time = time.perf_counter()
#     download_all_sites(sites)
#     duration = time.perf_counter() - start_time
#     print(f"Downloaded {len(sites)} sites in {duration} seconds")

# def download_all_sites(sites):
#     with ProcessPoolExecutor(initializer=init_process) as executor:
#         executor.map(download_site, sites)

# def download_site(url):
#     with session.get(url) as response:
#         name = multiprocessing.current_process().name
#         print(f"{name}:Read {len(response.content)} bytes from {url}")

# def init_process():
#     global session
#     session = requests.Session()
#     atexit.register(session.close)

# if __name__ == "__main__":
#     main()