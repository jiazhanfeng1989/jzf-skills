# jzf-skills — Agent Skills Collection

This repository contains reusable Agent Skills. Each skill lives under `skills/<skill-name>/` with a `SKILL.md` descriptor and supporting scripts.

## Available Skills

| Skill | Path | Description |
|-------|------|-------------|
| create-iso-country-geohash | `skills/create-iso-country-geohash/` | Generate geohash coverage data and interactive maps for one or more countries by ISO code |

## How to Install a Skill

Clone this repo and copy the skill folder into your project's `.cursor/skills/` directory:

```bash
git clone https://github.com/jiazhanfeng1989/jzf-skills.git

cp -r jzf-skills/skills/create-iso-country-geohash \
      your-project/.cursor/skills/create-iso-country-geohash
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
