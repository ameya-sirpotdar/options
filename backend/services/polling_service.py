import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.agents.options_agent import run_options_poll
from backend.models.options_data import OptionsContractRecord
from backend.models.run_log import RunLogRecord

logger = logging.getLogger(__name__)


class PollingService:
    def __init__(self, azure_table_service=None, schwab_client=None):
        self._azure_table_service = azure_table_service
        self._schwab_client = schwab_client

    def poll_options(self, tickers: List[str]) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        contracts_persisted = 0
        error_message: Optional[str] = None

        raw_result: Dict[str, Any] = {}
        try:
            if self._schwab_client is not None:
                for ticker in tickers:
                    chain = self._schwab_client.get_option_chain(ticker)
                    raw_result[ticker] = chain
            else:
                raw_result = run_options_poll(tickers)
        except Exception as exc:
            logger.exception("Options poll agent raised an exception: %s", exc)
            error_message = str(exc)
            raise

        if self._azure_table_service is not None:
            contracts: List[OptionsContractRecord] = []
            for ticker, data in raw_result.items():
                if not isinstance(data, dict):
                    continue
                option_chain = data.get("optionChain") or data
                calls_map: Dict[str, List[Dict[str, Any]]] = {}
                puts_map: Dict[str, List[Dict[str, Any]]] = {}

                if isinstance(option_chain, dict):
                    calls_map = option_chain.get("callExpDateMap") or {}
                    puts_map = option_chain.get("putExpDateMap") or {}

                def _extract_contracts(
                    exp_map: Dict[str, Any],
                    option_type: str,
                    underlying_symbol: str,
                    run_id_val: str,
                ) -> List[OptionsContractRecord]:
                    records: List[OptionsContractRecord] = []
                    for exp_date_key, strikes in exp_map.items():
                        if not isinstance(strikes, dict):
                            continue
                        for strike_key, contract_list in strikes.items():
                            if not isinstance(contract_list, list):
                                continue
                            for contract in contract_list:
                                if not isinstance(contract, dict):
                                    continue
                                try:
                                    record = OptionsContractRecord(
                                        runId=run_id_val,
                                        underlyingSymbol=underlying_symbol,
                                        optionType=option_type,
                                        putCall=contract.get("putCall", option_type),
                                        symbol=contract.get("symbol", ""),
                                        description=contract.get("description"),
                                        exchangeName=contract.get("exchangeName"),
                                        bidPrice=contract.get("bid"),
                                        askPrice=contract.get("ask"),
                                        lastPrice=contract.get("last"),
                                        markPrice=contract.get("mark"),
                                        bidSize=contract.get("bidSize"),
                                        askSize=contract.get("askSize"),
                                        lastSize=contract.get("lastSize"),
                                        highPrice=contract.get("highPrice"),
                                        lowPrice=contract.get("lowPrice"),
                                        openPrice=contract.get("openPrice"),
                                        closePrice=contract.get("closePrice"),
                                        totalVolume=contract.get("totalVolume"),
                                        tradeDate=contract.get("tradeDate"),
                                        tradeTimeInLong=contract.get("tradeTimeInLong"),
                                        quoteTimeInLong=contract.get("quoteTimeInLong"),
                                        netChange=contract.get("netChange"),
                                        volatility=contract.get("volatility"),
                                        delta=contract.get("delta"),
                                        gamma=contract.get("gamma"),
                                        theta=contract.get("theta"),
                                        vega=contract.get("vega"),
                                        rho=contract.get("rho"),
                                        openInterest=contract.get("openInterest"),
                                        timeValue=contract.get("timeValue"),
                                        theoreticalOptionValue=contract.get("theoreticalOptionValue"),
                                        theoreticalVolatility=contract.get("theoreticalVolatility"),
                                        strikePrice=contract.get("strikePrice"),
                                        expirationDate=contract.get("expirationDate"),
                                        daysToExpiration=contract.get("daysToExpiration"),
                                        expirationType=contract.get("expirationType"),
                                        lastTradingDay=contract.get("lastTradingDay"),
                                        multiplier=contract.get("multiplier"),
                                        settlementType=contract.get("settlementType"),
                                        deliverableNote=contract.get("deliverableNote"),
                                        percentChange=contract.get("percentChange"),
                                        markChange=contract.get("markChange"),
                                        markPercentChange=contract.get("markPercentChange"),
                                        intrinsicValue=contract.get("intrinsicValue"),
                                        extrinsicValue=contract.get("extrinsicValue"),
                                        inTheMoney=contract.get("inTheMoney"),
                                        mini=contract.get("mini"),
                                        nonStandard=contract.get("nonStandard"),
                                        pennyPilot=contract.get("pennyPilot"),
                                    )
                                    records.append(record)
                                except Exception as map_exc:
                                    logger.warning(
                                        "Failed to map contract to OptionsContractRecord: %s",
                                        map_exc,
                                    )
                    return records

                contracts.extend(
                    _extract_contracts(calls_map, "CALL", ticker, run_id)
                )
                contracts.extend(
                    _extract_contracts(puts_map, "PUT", ticker, run_id)
                )

            if contracts:
                try:
                    self._azure_table_service.upsert_options_contracts(contracts)
                    contracts_persisted = len(contracts)
                except Exception as persist_exc:
                    logger.warning(
                        "Failed to persist options contracts to Azure Table Storage: %s",
                        persist_exc,
                    )
                    error_message = error_message or str(persist_exc)

            finished_at = datetime.now(timezone.utc)
            run_log = RunLogRecord(
                runId=run_id,
                startedAt=started_at,
                finishedAt=finished_at,
                tickers=tickers,
                contractsPersisted=contracts_persisted,
                status="success" if error_message is None else "partial_failure",
                errorMessage=error_message,
            )
            try:
                self._azure_table_service.upsert_run_log(run_log)
            except Exception as log_exc:
                logger.warning(
                    "Failed to persist run log to Azure Table Storage: %s",
                    log_exc,
                )

        return raw_result
