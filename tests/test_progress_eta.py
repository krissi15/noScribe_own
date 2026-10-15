"""Restzeit der Sprechererkennung: erst schätzen, wenn genug gemessen ist."""

from conftest import load_module

eta = load_module('noScribe/progress_eta.py')


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_no_estimate_until_enough_time_and_progress():
    clock = Clock()
    r = eta.RemainingTime(clock=clock)
    assert r.update('embeddings', 0) is None
    clock.now = 10
    assert r.update('embeddings', 5) is None      # erst 10 s gemessen
    clock.now = 30
    assert r.update('embeddings', 1) is None      # zu wenig Fortschritt


def test_linear_estimate():
    clock = Clock()
    r = eta.RemainingTime(clock=clock)
    r.update('embeddings', 10)
    clock.now = 60
    # 10 % in 60 s -> für die übrigen 80 % noch 480 s
    assert r.update('embeddings', 20) == 480


def test_new_step_restarts_measurement():
    clock = Clock()
    r = eta.RemainingTime(clock=clock)
    r.update('segmentation', 0)
    clock.now = 100
    assert r.update('embeddings', 0) is None
    clock.now = 130
    assert r.update('embeddings', 10) == 270


def test_finished_step_has_no_estimate():
    clock = Clock()
    r = eta.RemainingTime(clock=clock)
    r.update('embeddings', 0)
    clock.now = 100
    assert r.update('embeddings', 100) is None


def test_format_duration():
    assert eta.format_duration(5) == '1 min'
    assert eta.format_duration(61) == '2 min'
    assert eta.format_duration(45 * 60) == '45 min'
    assert eta.format_duration(60 * 60) == '1 h'
    assert eta.format_duration(65 * 60) == '1 h 5 min'
