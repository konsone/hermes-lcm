"""Summary timing guards ported from the3asic/hermes-lcm.

Two behaviours are covered:

* the spend-guard backoff is anchored at the latest dispatch even when
  concurrent reservations record out of order;
* a summarisation call never starts after the deadline, even when the
  circuit/spend checks consumed the remaining window after the loop-level
  deadline check.
"""

import hermes_lcm.escalation as escalation


def test_backoff_anchors_to_latest_dispatch_when_recording_out_of_order(monkeypatch):
    clock = [10.0]
    monkeypatch.setattr(escalation.time, "monotonic", lambda: clock[0])
    guard = escalation.SummarySpendGuard(
        max_calls=3, window_seconds=10.0, backoff_seconds=5.0
    )

    assert guard.try_record_call(now=10.0)
    assert guard.try_record_call(now=10.2)
    # A concurrent caller took its timestamp before acquiring the lock and
    # records after a later dispatch.
    assert guard.try_record_call(now=10.1)

    assert guard._backoff_until == 15.2
    assert not guard.allows(now=15.19)
    assert guard.allows(now=15.2)


def test_deadline_is_rechecked_immediately_before_dispatch(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(escalation.time, "monotonic", lambda: clock[0])
    calls = []

    def fake_invoke(*args, **kwargs):
        calls.append(kwargs.get("model"))
        return "summary"

    monkeypatch.setattr(escalation, "_invoke_summary_llm", fake_invoke)

    class SlowGuard:
        def try_record_call(self, **_kwargs):
            clock[0] = 5.0  # the checks consumed the whole window
            return True

    result = escalation._invoke_summary_llm_chain(
        "prompt",
        128,
        model="test-model",
        deadline=5.0,
        spend_guard=SlowGuard(),
    )

    assert calls == []
    assert result is None
