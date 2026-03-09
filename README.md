# GaggiMate Home Assistant Integration

A Home Assistant custom integration for the [GaggiMate](https://github.com/jniebuhr/gaggimate) espresso machine controller. Monitor your boiler temperature and group head pressure in real time, and switch operating modes directly from your dashboard.

## Features

- **Real-time sensors** — current temperature, target temperature, and pressure, pushed via WebSocket (~1s updates)
- **Mode control** — switch between Standby, Brew, Steam, Hot Water, and Grind modes
- **Local push** — no cloud, no polling; connects directly to the device on your local network

## Requirements

- Home Assistant 2024.1 or later
- A GaggiMate device on the same network as your Home Assistant instance

## Installation

### HACS (recommended)

1. In HACS, go to **Integrations → Custom Repositories**
2. Add `https://github.com/michaeldwilliams/gaggimate-ha` with category **Integration**
3. Search for "GaggiMate" and install
4. Restart Home Assistant

### Manual

1. Copy `custom_components/gaggimate/` into your HA config's `custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **GaggiMate**
3. Enter the hostname or IP address of your device (default: `gaggimate.local`)

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.gaggimate_current_temperature` | Sensor | Current boiler temperature (°C) |
| `sensor.gaggimate_target_temperature` | Sensor | Target boiler temperature (°C) |
| `sensor.gaggimate_pressure` | Sensor | Current group head pressure (bar) |
| `select.gaggimate_mode` | Select | Operating mode |

## License

MIT
