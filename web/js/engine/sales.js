/** Pipeline forecast, mirroring funilab.sales.forecast_table. */

/**
 * Expected won amount from open deals.
 * @param deals open deals: {stage, amount, days_in_stage, won}
 * @param probabilities stage -> probability
 * @param options.staleAfter stage -> days after which a deal is stale (null disables)
 * @param options.staleFactor multiplier on staleAfter (1 = the 85th percentile of won deals)
 */
export function forecast(deals, probabilities, { staleAfter = null, staleFactor = 1 } = {}) {
  let expected = 0;
  let actual = 0;
  let staleCount = 0;
  let staleAmount = 0;
  for (const deal of deals) {
    const limit = staleAfter ? staleAfter[deal.stage] * staleFactor : Infinity;
    const stale = deal.days_in_stage > limit;
    if (stale) {
      staleCount += 1;
      staleAmount += deal.amount;
    } else {
      expected += deal.amount * (probabilities[deal.stage] ?? 0);
    }
    if (deal.won) actual += deal.amount;
  }
  return {
    forecast: expected,
    actual,
    error: actual ? expected / actual - 1 : NaN,
    staleCount,
    staleAmount,
  };
}
