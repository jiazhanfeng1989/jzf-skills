# jzf-skills — Agent Skills Collection

This repository contains reusable Agent Skills. Each skill lives under `skills/<skill-name>/` with a `SKILL.md` descriptor and supporting scripts.

## Available Skills

| Skill | Path | Description |
|-------|------|-------------|
| create-iso-country-geohash | `skills/create-iso-country-geohash/` | Generate geohash coverage data and interactive maps for one or more countries by ISO code |

## How to Install a Skill

### Cursor IDE

1. Clone this repo:

```bash
git clone https://github.com/jiazhanfeng1989/jzf-skills.git
```

2. Open **Cursor Settings → Features → Docs & Skills** (or navigate to `.cursor/skills/` in your project).
3. Add a skill entry pointing to the `SKILL.md` file, replacing `<path-to-jzf-skills>` with your clone location:

```yaml
- fullPath: <path-to-jzf-skills>/skills/create-iso-country-geohash/SKILL.md
  description: Generate geohash.data and geohash.html from ISO country codes
```

### Codex / Other Agents

Copy or symlink the skill folder into your project's `.cursor/skills/` directory:

```bash
# Symlink (recommended — stays in sync)
ln -s <path-to-jzf-skills>/skills/create-iso-country-geohash \
      .cursor/skills/create-iso-country-geohash

# Or copy
cp -r <path-to-jzf-skills>/skills/create-iso-country-geohash \
      .cursor/skills/create-iso-country-geohash
```

Then reference the skill in your agent configuration:

```yaml
agent_skill:
  fullPath: .cursor/skills/create-iso-country-geohash/SKILL.md
  description: Generate geohash.data and geohash.html from ISO country codes
```

## Adding New Skills

Place each new skill under `skills/<skill-name>/` with at minimum a `SKILL.md` file following the standard frontmatter format:

```markdown
---
name: my-skill-name
description: One-line summary of what the skill does
---

# my-skill-name

(Detailed usage instructions for the agent)
```
