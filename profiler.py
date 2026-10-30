import time
import functools
import sys
import streamlit as st

def profile_time(name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            dur = end - start
            print(f"[PROFILE] {name} took {dur:.4f}s", file=sys.stderr)
            if dur > 1.0:
                print(f"  --> [WARNING] {name} exceeded 1s!", file=sys.stderr)
            return result
        return wrapper
    return decorator

def measure_block(name):
    @contextlib.contextmanager
    def _timer():
        start = time.perf_counter()
        yield
        end = time.perf_counter()
        dur = end - start
        print(f"[PROFILE] {name} took {dur:.4f}s", file=sys.stderr)
        if dur > 1.0:
            print(f"  --> [WARNING] {name} exceeded 1s!", file=sys.stderr)
    return _timer()
