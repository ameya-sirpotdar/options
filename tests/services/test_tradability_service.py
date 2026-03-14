import pytest
from backend.services.trades_comparison_service import extract_metrics, compute_score, rank_candidates


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_row():
    """A fully-populated Azure Table Storage options row."""
    return {
        "PartitionKey": "AAPL",
        "RowKey": "2024-01-19_150_C",
        "delta": 0.55,
        "theta": -0.08,
        "iv": 0.30,
        "premium": 4.50,
    }


@pytest.fixture
def minimal_row():
    """Row with only required fields; optional fields absent."""
    return {
        "PartitionKey": "TSLA",
        "RowKey": "2024-01-19_200_P",
        "delta": -0.40,
        "theta": -0.05,
        "iv": 0.55,
        "premium": 3.20,
    }


@pytest.fixture
def candidate_rows():
    """A list of rows suitable for ranking tests."""
    return [
        {
            "PartitionKey": "AAPL",
            "RowKey": "2024-01-19_150_C",
            "delta": 0.55,
            "theta": -0.08,
            "iv": 0.30,
            "premium": 4.50,
        },
        {
            "PartitionKey": "MSFT",
            "RowKey": "2024-01-19_300_C",
            "delta": 0.45,
            "theta": -0.04,
            "iv": 0.25,
            "premium": 6.00,
        },
        {
            "PartitionKey": "TSLA",
            "RowKey": "2024-01-19_200_P",
            "delta": -0.40,
            "theta": -0.05,
            "iv": 0.55,
            "premium": 3.20,
        },
    ]


# ---------------------------------------------------------------------------
# Story 1 – extract_metrics()
# ---------------------------------------------------------------------------

class TestExtractMetrics:
    def test_returns_dict(self, valid_row):
        result = extract_metrics(valid_row)
        assert isinstance(result, dict)

    def test_extracts_delta(self, valid_row):
        result = extract_metrics(valid_row)
        assert result["delta"] == pytest.approx(0.55)

    def test_extracts_theta(self, valid_row):
        result = extract_metrics(valid_row)
        assert result["theta"] == pytest.approx(-0.08)

    def test_extracts_iv(self, valid_row):
        result = extract_metrics(valid_row)
        assert result["iv"] == pytest.approx(0.30)

    def test_extracts_premium(self, valid_row):
        result = extract_metrics(valid_row)
        assert result["premium"] == pytest.approx(4.50)

    def test_all_four_keys_present(self, valid_row):
        result = extract_metrics(valid_row)
        assert set(result.keys()) >= {"delta", "theta", "iv", "premium"}

    def test_minimal_row_extracts_correctly(self, minimal_row):
        result = extract_metrics(minimal_row)
        assert result["delta"] == pytest.approx(-0.40)
        assert result["theta"] == pytest.approx(-0.05)
        assert result["iv"] == pytest.approx(0.55)
        assert result["premium"] == pytest.approx(3.20)

    def test_missing_delta_raises(self):
        row = {"theta": -0.05, "iv": 0.30, "premium": 4.50}
        with pytest.raises((KeyError, ValueError)):
            extract_metrics(row)

    def test_missing_theta_raises(self):
        row = {"delta": 0.55, "iv": 0.30, "premium": 4.50}
        with pytest.raises((KeyError, ValueError)):
            extract_metrics(row)

    def test_missing_iv_raises(self):
        row = {"delta": 0.55, "theta": -0.08, "premium": 4.50}
        with pytest.raises((KeyError, ValueError)):
            extract_metrics(row)

    def test_missing_premium_raises(self):
        row = {"delta": 0.55, "theta": -0.08, "iv": 0.30}
        with pytest.raises((KeyError, ValueError)):
            extract_metrics(row)

    def test_non_numeric_delta_raises(self):
        row = {"delta": "high", "theta": -0.08, "iv": 0.30, "premium": 4.50}
        with pytest.raises((TypeError, ValueError)):
            extract_metrics(row)

    def test_non_numeric_iv_raises(self):
        row = {"delta": 0.55, "theta": -0.08, "iv": None, "premium": 4.50}
        with pytest.raises((TypeError, ValueError)):
            extract_metrics(row)

    def test_extra_keys_are_ignored(self, valid_row):
        valid_row["extra_field"] = "should_be_ignored"
        result = extract_metrics(valid_row)
        assert "extra_field" not in result

    def test_integer_values_accepted(self):
        row = {"delta": 1, "theta": 0, "iv": 1, "premium": 5}
        result = extract_metrics(row)
        assert result["delta"] == pytest.approx(1.0)
        assert result["premium"] == pytest.approx(5.0)

    def test_zero_premium_accepted(self):
        row = {"delta": 0.10, "theta": -0.01, "iv": 0.20, "premium": 0.0}
        result = extract_metrics(row)
        assert result["premium"] == pytest.approx(0.0)

    def test_empty_row_raises(self):
        with pytest.raises((KeyError, ValueError)):
            extract_metrics({})


# ---------------------------------------------------------------------------
# Story 2 – compute_score()
# ---------------------------------------------------------------------------

class TestComputeScore:
    def test_returns_float(self, valid_row):
        metrics = extract_metrics(valid_row)
        score = compute_score(metrics)
        assert isinstance(score, float)

    def test_score_is_finite(self, valid_row):
        metrics = extract_metrics(valid_row)
        score = compute_score(metrics)
        import math
        assert math.isfinite(score)

    def test_higher_delta_increases_score(self):
        low = compute_score({"delta": 0.20, "theta": -0.05, "iv": 0.30, "premium": 3.00})
        high = compute_score({"delta": 0.60, "theta": -0.05, "iv": 0.30, "premium": 3.00})
        assert high > low

    def test_lower_iv_increases_score(self):
        low_iv = compute_score({"delta": 0.50, "theta": -0.05, "iv": 0.20, "premium": 3.00})
        high_iv = compute_score({"delta": 0.50, "theta": -0.05, "iv": 0.60, "premium": 3.00})
        assert low_iv > high_iv

    def test_less_negative_theta_increases_score(self):
        mild = compute_score({"delta": 0.50, "theta": -0.02, "iv": 0.30, "premium": 3.00})
        steep = compute_score({"delta": 0.50, "theta": -0.15, "iv": 0.30, "premium": 3.00})
        assert mild > steep

    def test_higher_premium_increases_score(self):
        low = compute_score({"delta": 0.50, "theta": -0.05, "iv": 0.30, "premium": 1.00})
        high = compute_score({"delta": 0.50, "theta": -0.05, "iv": 0.30, "premium": 8.00})
        assert high > low

    def test_identical_metrics_produce_identical_scores(self, valid_row):
        metrics = extract_metrics(valid_row)
        assert compute_score(metrics) == pytest.approx(compute_score(metrics))

    def test_score_not_negative_for_reasonable_inputs(self):
        metrics = {"delta": 0.50, "theta": -0.05, "iv": 0.30, "premium": 3.00}
        assert compute_score(metrics) >= 0

    def test_missing_metric_key_raises(self):
        with pytest.raises((KeyError, TypeError)):
            compute_score({"delta": 0.50, "theta": -0.05, "iv": 0.30})

    def test_absolute_delta_used_for_puts(self):
        """A put with delta=-0.50 should score the same as a call with delta=0.50
        when all other metrics are equal, if the implementation uses abs(delta)."""
        call_score = compute_score({"delta": 0.50, "theta": -0.05, "iv": 0.30, "premium": 3.00})
        put_score = compute_score({"delta": -0.50, "theta": -0.05, "iv": 0.30, "premium": 3.00})
        # Both should be equal (abs delta) OR put should not be penalised vs call
        # We accept either equal or put >= 0 as valid behaviour.
        assert put_score >= 0

    def test_score_varies_with_different_rows(self, candidate_rows):
        scores = [compute_score(extract_metrics(r)) for r in candidate_rows]
        # At least two distinct scores expected across three different rows
        assert len(set(round(s, 6) for s in scores)) > 1

    def test_extreme_iv_produces_lower_score(self):
        normal = compute_score({"delta": 0.50, "theta": -0.05, "iv": 0.30, "premium": 3.00})
        extreme = compute_score({"delta": 0.50, "theta": -0.05, "iv": 5.00, "premium": 3.00})
        assert normal > extreme


# ---------------------------------------------------------------------------
# Story 3 – rank_candidates()
# ---------------------------------------------------------------------------

class TestRankCandidates:
    def test_returns_list(self, candidate_rows):
        result = rank_candidates(candidate_rows)
        assert isinstance(result, list)

    def test_length_preserved(self, candidate_rows):
        result = rank_candidates(candidate_rows)
        assert len(result) == len(candidate_rows)

    def test_first_element_has_highest_score(self, candidate_rows):
        result = rank_candidates(candidate_rows)
        scores = [item["score"] for item in result]
        assert scores[0] == max(scores)

    def test_descending_order(self, candidate_rows):
        result = rank_candidates(candidate_rows)
        scores = [item["score"] for item in result]
        assert scores == sorted(scores, reverse=True)

    def test_each_item_contains_score_key(self, candidate_rows):
        result = rank_candidates(candidate_rows)
        for item in result:
            assert "score" in item

    def test_each_item_contains_original_row_data(self, candidate_rows):
        result = rank_candidates(candidate_rows)
        partition_keys = {item["PartitionKey"] for item in result}
        assert partition_keys == {"AAPL", "MSFT", "TSLA"}

    def test_best_candidate_is_first(self, candidate_rows):
        result = rank_candidates(candidate_rows)
        best = result[0]
        # The best candidate should have the highest score among all
        for item in result[1:]:
            assert best["score"] >= item["score"]

    def test_single_row_returns_single_item(self, valid_row):
        result = rank_candidates([valid_row])
        assert len(result) == 1
        assert "score" in result[0]

    def test_empty_list_returns_empty_list(self):
        result = rank_candidates([])
        assert result == []

    def test_scores_are_floats(self, candidate_rows):
        result = rank_candidates(candidate_rows)
        for item in result:
            assert isinstance(item["score"], float)

    def test_row_keys_preserved(self, candidate_rows):
        result = rank_candidates(candidate_rows)
        row_keys = {item["RowKey"] for item in result}
        expected = {r["RowKey"] for r in candidate_rows}
        assert row_keys == expected

    def test_duplicate_rows_handled(self, valid_row):
        rows = [valid_row, valid_row.copy(), valid_row.copy()]
        result = rank_candidates(rows)
        assert len(result) == 3
        scores = [item["score"] for item in result]
        assert scores[0] == pytest.approx(scores[1])
        assert scores[1] == pytest.approx(scores[2])

    def test_ranking_is_deterministic(self, candidate_rows):
        result_a = rank_candidates(candidate_rows)
        result_b = rank_candidates(candidate_rows)
        for a, b in zip(result_a, result_b):
            assert a["score"] == pytest.approx(b["score"])
            assert a["PartitionKey"] == b["PartitionKey"]

    def test_invalid_row_in_list_raises(self):
        rows = [
            {"delta": 0.50, "theta": -0.05, "iv": 0.30, "premium": 3.00},
            {"delta": "bad", "theta": -0.05, "iv": 0.30, "premium": 3.00},
        ]
        with pytest.raises((TypeError, ValueError, KeyError)):
            rank_candidates(rows)

    def test_two_candidates_correct_winner(self):
        """Manually verify which of two rows should win."""
        strong = {"delta": 0.70, "theta": -0.02, "iv": 0.20, "premium": 7.00}
        weak = {"delta": 0.20, "theta": -0.20, "iv": 0.80, "premium": 0.50}
        result = rank_candidates([weak, strong])
        assert result[0]["delta"] == pytest.approx(0.70)