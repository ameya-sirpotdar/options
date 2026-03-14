from backend.agents.state import PipelineState
from backend.services.trades_comparison_service import TradesComparisonService

__all__ = ["TradabilityAgent"]


class TradabilityAgent:
    """
    Agent for assessing overall tradability of options contracts.

    Intended role in the pipeline:
        Receives options contracts and computed metrics from upstream agents
        and synthesises them into tradability scores using
        ``TradesComparisonService``.  The scored contracts are written back
        into the shared LangGraph state under the ``trades`` key so that
        downstream consumers (e.g. the trades router) can serve them
        directly.

    The agent delegates all scoring logic to
    :class:`~backend.services.trades_comparison_service.TradesComparisonService`,
    which consolidates the former ``tradability_service`` and
    ``ccp_calculator`` modules.
    """

    def __init__(self, trades_comparison_service: TradesComparisonService | None = None) -> None:
        """
        Initialise the agent.

        Parameters
        ----------
        trades_comparison_service:
            An optional pre-constructed :class:`TradesComparisonService`
            instance.  When *None* a default instance is created
            automatically.  Injecting a custom instance is useful for
            testing.
        """
        self._service: TradesComparisonService = (
            trades_comparison_service
            if trades_comparison_service is not None
            else TradesComparisonService()
        )

    def run(self, state: PipelineState) -> PipelineState:
        """
        Execute the tradability assessment step.

        Reads ``options_contracts`` from *state*, scores each contract via
        :meth:`TradesComparisonService.score_contracts`, and writes the
        resulting list of scored trades back into *state* under the
        ``trades`` key.

        Parameters
        ----------
        state:
            The current LangGraph shared state dictionary.

        Returns
        -------
        PipelineState
            The updated state dictionary with ``trades`` populated.
        """
        contracts = state.get("options_contracts", [])
        trades = self._service.score_contracts(contracts)
        return {**state, "trades": trades}

    def __call__(self, state: PipelineState) -> PipelineState:
        """Allow the agent to be used directly as a LangGraph node callable."""
        return self.run(state)