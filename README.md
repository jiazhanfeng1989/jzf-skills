# jzf-skills

A personal collection of Agent Skills — reusable automation capabilities for AI agents like Cursor and Codex.

## Skills

### create-iso-country-geohash

Generate geohash coverage data and an interactive Leaflet map from one or more ISO country codes (alpha-2 or alpha-3). Uses Natural Earth geodata with configurable geohash precision.

See [`skills/create-iso-country-geohash/SKILL.md`](skills/create-iso-country-geohash/SKILL.md) for full usage details.

### filter-geohash-ids

Filter arbitrary geohash id lists by duplicate ids, optional ISO country coverage, and conservative water/river removal.

See [`skills/filter-geohash-ids/SKILL.md`](skills/filter-geohash-ids/SKILL.md) for full usage details.

## Installation

Clone this repo, then copy the skill folder to the place your agent loads skills from:

```bash
git clone https://github.com/jiazhanfeng1989/jzf-skills.git

mkdir -p your-project/.agent-skills
cp -R jzf-skills/skills/create-iso-country-geohash your-project/.agent-skills/
cp -R jzf-skills/skills/filter-geohash-ids your-project/.agent-skills/
```

Use any directory your tool supports. Common options:

```bash
# Cursor native skills
mkdir -p your-project/.cursor/skills
cp -R jzf-skills/skills/create-iso-country-geohash your-project/.cursor/skills/
cp -R jzf-skills/skills/filter-geohash-ids your-project/.cursor/skills/

# Codex or other agents that read repo instructions
mkdir -p your-project/.agent-skills
cp -R jzf-skills/skills/create-iso-country-geohash your-project/.agent-skills/
cp -R jzf-skills/skills/filter-geohash-ids your-project/.agent-skills/
```

For agents without native skill discovery, reference each `SKILL.md` from the project instruction file, such as `AGENTS.md`:

```markdown
Available skills:
- create-iso-country-geohash: .agent-skills/create-iso-country-geohash/SKILL.md
- filter-geohash-ids: .agent-skills/filter-geohash-ids/SKILL.md
```

For more details, see [`AGENTS.md`](AGENTS.md).

## Project Structure

```
jzf-skills/
├── AGENTS.md
├── README.md
└── skills/
    ├── create-iso-country-geohash/
    │   ├── SKILL.md
    │   └── scripts/
    │       ├── requirements.txt
    │       ├── generate_country_geohash.py
    │       └── geohash_data_to_map.py
    └── filter-geohash-ids/
        ├── SKILL.md
        └── scripts/
            ├── requirements.txt
            ├── filter_geohash_ids.py
            └── test_filter_geohash_ids.py
```

## License

[MIT](LICENSE)
