# jzf-skills

A personal collection of Agent Skills — reusable automation capabilities for AI agents like Cursor and Codex.

## Skills

### create-iso-country-geohash

Generate geohash coverage data and an interactive map from one or more ISO country codes (alpha-2 or alpha-3).

**Features**:
- Accepts one or more country codes (e.g. `IND`, `DE`, `FRA`), automatically downloads Natural Earth 110m geodata
- Produces `geohash.data` — one geohash per line, deduplicated, sorted, with full 32-sibling groups compacted
- Produces `geohash.html` — a Leaflet interactive map for browser preview
- Configurable starting geohash length (default 3) and max split length (default 4)

**Quick start**:

```bash
pip install -r skills/create-iso-country-geohash/scripts/requirements.txt
python3 skills/create-iso-country-geohash/scripts/generate_country_geohash.py --iso IND,DEU
python3 skills/create-iso-country-geohash/scripts/geohash_data_to_map.py
```

See [`skills/create-iso-country-geohash/SKILL.md`](skills/create-iso-country-geohash/SKILL.md) for full usage details.

---

## Installation

First, clone this repo to your local machine:

```bash
git clone https://github.com/jiazhanfeng1989/jzf-skills.git
```

Then pick one of the following methods to install a skill into your project.

### Option 1: Add as a Cursor IDE Skill

Add the following entry to your project's `.cursor/skills/` configuration, replacing `<path-to-jzf-skills>` with the actual clone location:

```yaml
- fullPath: <path-to-jzf-skills>/skills/create-iso-country-geohash/SKILL.md
  description: Generate geohash.data and geohash.html from ISO country codes
```

### Option 2: Symlink (recommended)

Symlink the skill into your project's `.cursor/skills/` directory so it stays in sync automatically:

```bash
ln -s <path-to-jzf-skills>/skills/create-iso-country-geohash \
      your-project/.cursor/skills/create-iso-country-geohash
```

### Option 3: Copy

```bash
cp -r <path-to-jzf-skills>/skills/create-iso-country-geohash \
      your-project/.cursor/skills/create-iso-country-geohash
```

For full agent configuration details, see [`AGENTS.md`](AGENTS.md).

## Project Structure

```
jzf-skills/
├── AGENTS.md                                # Agent installation guide
├── README.md                                # This file
└── skills/
    └── create-iso-country-geohash/          # Geohash country coverage generator
        ├── SKILL.md                         # Skill descriptor (read by agents)
        └── scripts/
            ├── requirements.txt             # Python dependencies
            ├── generate_country_geohash.py  # Main generation script
            └── geohash_data_to_map.py       # Map visualization script
```

## License

Personal use.
