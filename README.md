# jzf-skills

A personal collection of Agent Skills — reusable automation capabilities for AI agents like Cursor and Codex.

## Skills

### create-iso-country-geohash

Generate geohash coverage data and an interactive Leaflet map from one or more ISO country codes (alpha-2 or alpha-3). Uses Natural Earth 110m geodata with configurable geohash precision.

See [`skills/create-iso-country-geohash/SKILL.md`](skills/create-iso-country-geohash/SKILL.md) for full usage details.

## Installation

Clone this repo and copy the skill into your project's `.cursor/skills/` directory:

```bash
git clone https://github.com/jiazhanfeng1989/jzf-skills.git

cp -r jzf-skills/skills/create-iso-country-geohash \
      your-project/.cursor/skills/create-iso-country-geohash
```

For agent configuration details, see [`AGENTS.md`](AGENTS.md).

## Project Structure

```
jzf-skills/
├── AGENTS.md
├── README.md
└── skills/
    └── create-iso-country-geohash/
        ├── SKILL.md
        └── scripts/
            ├── requirements.txt
            ├── generate_country_geohash.py
            └── geohash_data_to_map.py
```

## License

[MIT](LICENSE)
