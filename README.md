# Printer Page Plan Monitor for HP Instant Ink

**Printer Page Plan Monitor for HP Instant Ink** is an unofficial Home Assistant custom integration for tracking page allowance, rollover pages, renewal cycles, and ink levels on compatible HP Instant Ink printers using local EWS/LEDM data.

It was developed and tested with an **HP OfficeJet 8010 series printer enrolled in HP Instant Ink**, using the local `SubscriptionImpressions` counter exposed by the printer. Other compatible HP printers exposing the same LEDM data may also work.

> **Unofficial project:** this project is independent and is not affiliated with, sponsored by, or endorsed by HP Inc. HP and Instant Ink are trademarks of HP Inc. Those names are used only to identify compatible products and services. This project does not use the HP logo or HP visual branding.

## Features

- Reads `SubscriptionImpressions` directly from the printer over the local network.
- Tracks all pages used in the current billing cycle, including usage beyond the monthly allowance.
- Separates monthly pages and rollover pages.
- Shows total remaining pages.
- Handles monthly renewal and carries unused monthly pages into rollover up to a user-configured cap.
- Reads black, cyan, magenta and yellow ink levels when exposed by the printer.
- Polls locally every 120 seconds.
- Persists billing state across Home Assistant restarts.
- Supports manual realignment from the integration options.
- Provides diagnostics and removes its own stored billing state when the config entry is deleted.
- Includes original vendor-neutral branding locally in the integration.

## How it works

The integration does **not** sign in to any vendor cloud account. It reads the printer's local endpoint:

```text
http://PRINTER_IP/DevMgmt/ProductUsageDyn.xml
```

The XML must contain:

```xml
<SubscriptionImpressions>...</SubscriptionImpressions>
```

Ink-level sensors additionally use `ConsumableRawPercentageLevelRemaining` for Black, Cyan, Magenta and Yellow consumables.

The subscription page balance itself is initialized from the values the user sees in the subscription account. From that point onward, local page-counter deltas update the Home Assistant sensors.

## Installation with HACS

Until this repository is included in the default HACS catalog:

1. Open HACS.
2. Add `https://github.com/paolofaz/printer-page-plan-monitor` as a **Custom repository**.
3. Select category **Integration**.
4. Install **Printer Page Plan Monitor for HP Instant Ink**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration → Printer Page Plan Monitor for HP Instant Ink**.

## Manual installation

Copy:

```text
custom_components/printer_page_plan_monitor
```

into:

```text
/config/custom_components/printer_page_plan_monitor
```

Restart Home Assistant and add **Printer Page Plan Monitor for HP Instant Ink** from **Settings → Devices & services**.

## Initial configuration

The setup asks for:

- printer IP address or hostname;
- monthly renewal day;
- pages included in the monthly plan;
- monthly-plan pages already used in the current cycle;
- total rollover allowance shown for the current cycle;
- rollover pages already used in the current cycle;
- maximum rollover balance for the plan.

This mirrors the information commonly shown by the subscription account and avoids having to infer the split between monthly and rollover usage.

### Example

If the account shows:

```text
Monthly plan: 3 used of 50
Rollover:     0 used of 73
Rollover cap: 150
```

enter:

```text
Monthly pages:       50
Monthly used:         3
Rollover total:      73
Rollover used:        0
Rollover maximum:   150
```

The integration anchors those values to the printer's current local counter. If two more pages are printed, the cycle usage becomes 5 and the monthly pages remaining become 45.

If monthly usage reaches 50 and another 20 rollover pages are consumed, **Pages used in current cycle** reports 70; it does not stop at the monthly allowance.

## Sensors

The integration creates:

- Subscription page counter
- Pages used in current cycle
- Monthly pages remaining
- Rollover pages remaining
- Total pages remaining
- Next renewal
- Black ink
- Cyan ink
- Magenta ink
- Yellow ink

Sensor names are localized in English and Italian.

## Renewal behavior

On the configured renewal day:

1. the current cycle is closed using the most recently observed printer counter;
2. unused monthly pages are added to the remaining rollover balance;
3. rollover is capped at the configured maximum;
4. a fresh monthly allowance is created;
5. **Pages used in current cycle** returns to `0`.

If Home Assistant is offline across the renewal boundary, the integration cannot know exactly how pages printed during the outage should be split between the old and new cycles. It therefore marks the renewal as uncertain in diagnostics rather than claiming false precision.

## Realignment

Use the integration **Options** whenever the subscription account and Home Assistant need to be realigned, for example after changing plan or correcting a balance. Saving the options creates a new anchor at the printer's current local counter.

## Privacy and network access

Printer polling is local. The integration does not authenticate to HP, scrape the HP website, or access the HP Instant Ink cloud account.

## Compatibility

Confirmed working during initial development with:

- HP OfficeJet 8010 series

A printer is a candidate for compatibility if `ProductUsageDyn.xml` is reachable locally and contains `SubscriptionImpressions`.

## Known limits

- Subscription rules can differ by plan, country, or future provider changes. The rollover cap is therefore configurable rather than hard-coded.
- If the printer does not expose `SubscriptionImpressions`, subscription-page monitoring cannot work with this integration.
- Ink sensors only appear with values when the corresponding LEDM consumable data is available.

# 🍺 Support the Project

If you found this project useful and want to support my work, you can offer me a beer:

[![Buy Me a Beer](https://img.shields.io/badge/Buy%20Me%20a%20Beer-0070ba?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/PaoloFazari)


## Contributions
Contributions are welcome

## License

MIT License. See [LICENSE](LICENSE).
