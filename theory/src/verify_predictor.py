"""Exact finite-state checks of predictor tradeoffs and marginal attainment.

No simulation or project execution, no saved evidence files. Run directly or
through theory/run_all.sh. Fractions avoid tolerance-dependent comparisons.
"""
from fractions import Fraction as Q
from itertools import product


def verify_predictors():
    checked = 0
    rates = [Q(i, 4) for i in range(5)]
    for n in range(2, 13):
        # Reversal symmetry: 01 and 10 cells have the same count.
        for n11 in range(n + 1):
            for mixed in range((n - n11) // 2 + 1):
                n00 = n - n11 - 2 * mixed
                f, B = Q(n11 + mixed, n), Q(n11, n)
                if not 0 < f < 1:
                    continue
                J, q = f - B, 1 - 2 * f + B
                for s, a in product(rates, repeat=2):
                    # Enumerate all outcome/gate branches rather than using
                    # the closed-form numerator or denominator.
                    branches = []
                    for first, reverse, count in (
                        (1, 1, n11), (1, 0, mixed),
                        (0, 1, mixed), (0, 0, n00),
                    ):
                        mass = Q(count, n)
                        if first:
                            branches.append((mass, 1, True))
                        else:
                            gate = s if reverse else a
                            branches.extend(((mass * gate, 2, bool(reverse)),
                                             (mass * (1 - gate), 1, False)))
                    assert sum(p for p, _, _ in branches) == 1
                    success = sum(p for p, _, stop in branches if stop)
                    cost = sum(p * r for p, r, _ in branches)
                    exact = cost / success
                    assert exact == (1 + s * J + a * q) / (f + s * J)
                    oracle = (1 + J) / (f + J)
                    pair = (2 - f) / (2 * f - B)
                    assert exact - oracle == (
                        J * (1 - f) * (1 - s) + a * q * (f + J)
                    ) / ((f + s * J) * (f + J))
                    assert exact >= oracle
                    if s == a == 0:
                        assert exact == 1 / f
                    if s == a == 1:
                        assert exact == pair
                    if s == 1 and a == 0:
                        assert exact == oracle
                    for c in (Q(0), Q(1, 10), Q(1)):
                        value = (cost + c) / success
                        assert (value < 1 / f) == (s * J * (1 - f) > f * (c + a * q))
                        assert (value < pair) == (
                            (1 + c + s * J + a * q) * (2 * f - B)
                            < (2 - f) * (f + s * J)
                        )
                    checked += 1
    f = Q(1, 100)
    assert (1 + Q(4, 5) * f + Q(1, 10) * (1 - 2 * f)) / (f + Q(4, 5) * f) == Q(553, 9)
    return checked


def verify_uniform_attainment():
    checked = 0
    for n in range(2, 51):
        for a in range(1, n):
            f = Q(a, n)
            N = n // a
            survivors = set(range(n))
            expectation = Q(0)
            for t in range(N + 2):
                assert Q(len(survivors), n) == max(0, 1 - t * f)
                expectation += Q(len(survivors), n)
                fail = {u for u in range(n) if (u + t * a) % n < a}
                assert len(fail) == a  # uniform failure marginal
                survivors -= fail
            L = (N + 1) * (1 - N * f / 2)
            assert expectation == L
            delta = 1 / f - N
            assert L - (1 / f + 1) / 2 == f * delta * (1 - delta) / 2
            assert 0 <= L - (1 / f + 1) / 2 <= f / 8
            checked += 1
    return checked


if __name__ == '__main__':
    print(f'Predictor: {verify_predictors()} exact outcome/rate profiles passed')
    print(f'Uniform-marginal attainment: {verify_uniform_attainment()} rational rates passed')
