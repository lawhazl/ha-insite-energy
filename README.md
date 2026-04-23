# Insite Energy — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for [Insite Energy](https://my.insite-energy.co.uk) prepay heat/hot water meters (Guru Hub II systems).

## Sensors

| Sensor | Description |
|--------|-------------|
| **Active Balance** | Current credit balance (£) |
| **Debt Balance** | Outstanding debt balance (£) |
| **Debt Recovery Rate** | Percentage of each top-up applied to debt |
| **Unit Rate** | Energy unit rate (p/kWh) |
| **Standing Charge** | Daily standing charge (p/day) |
| **Last Meter Reading** | Timestamp of last meter communication |
| **Meter Out of Comms** | Whether the hub has lost contact with Guru's servers |
| **Last Poll Time** | When data was last fetched from the site |
| **Next Poll Time** | When the next fetch is scheduled |

## Installation via HACS

1. In Home Assistant, go to **HACS → Integrations**
2. Click the three-dot menu (⋮) → **Custom repositories**
3. Add your repository URL with category **Integration**
4. Click **Insite Energy** → **Download**
5. Restart Home Assistant

## Manual Installation

Copy the `custom_components/insite_energy` folder into your HA `config/custom_components/` directory, then restart.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Insite Energy**
3. Enter your `my.insite-energy.co.uk` email and password

Data is refreshed every 15 minutes by default. To change this, go to **Settings → Devices & Services → Insite Energy → Configure**. The minimum interval is 5 minutes to avoid being blocked by the site. Note that Insite Energy themselves only update the balance from the meter every 24 hours.

## Notes

- This integration scrapes the Insite Energy website — it is not an official API
- The Guru Hub II communicates over an 868MHz mesh network, not your home WiFi, so there is no local LAN API available
- If your meter shows "Out of Comms", live kWh readings will be unavailable (this is a Guru/Insite issue, not this integration)

## Disclaimer

This project is not affiliated with Insite Energy or Guru Systems Ltd.
