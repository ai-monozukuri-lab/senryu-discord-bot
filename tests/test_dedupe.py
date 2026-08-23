from bot.dedupe import MessageDeduplicator


def test_check_and_mark_suppresses_a_message_until_ttl_expires() -> None:
    current = [100.0]
    dedupe = MessageDeduplicator(ttl_seconds=10, max_entries=10, clock=lambda: current[0])

    assert dedupe.check_and_mark(123) is True
    assert dedupe.check_and_mark(123) is False

    current[0] = 110.01
    assert dedupe.check_and_mark(123) is True


def test_oldest_entries_are_evicted_when_the_capacity_is_reached() -> None:
    current = [0.0]
    dedupe = MessageDeduplicator(ttl_seconds=100, max_entries=2, clock=lambda: current[0])

    assert dedupe.check_and_mark("first") is True
    current[0] += 1
    assert dedupe.check_and_mark("second") is True
    current[0] += 1
    assert dedupe.check_and_mark("third") is True

    assert dedupe.check_and_mark("first") is True
    assert dedupe.check_and_mark("second") is False

