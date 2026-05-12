# jzf-skills — Agent Skills Collection

This repository contains reusable Agent Skills. Each skill lives under `skills/<skill-name>/` with a `SKILL.md` descriptor and supporting scripts.

## Available Skills

| Skill | Path | Description |
|-------|------|-------------|
| create-iso-country-geohash | `skills/create-iso-country-geohash/` | Generate geohash coverage data and interactive maps for one or more countries by ISO code |
| filter-geohash-ids | `skills/filter-geohash-ids/` | Filter geohash id lists by duplicates, optional ISO country coverage, and conservative water/river removal |

## How to Install Skills

Each skill is portable: copy the full skill directory, including `SKILL.md` and `scripts/`, into a directory your agent can read.

```bash
git clone https://github.com/jiazhanfeng1989/jzf-skills.git

mkdir -p your-project/.agent-skills
cp -R jzf-skills/skills/create-iso-country-geohash your-project/.agent-skills/
cp -R jzf-skills/skills/filter-geohash-ids your-project/.agent-skills/
```

Tool-specific examples:

```bash
# Cursor native skills
mkdir -p your-project/.cursor/skills
cp -R jzf-skills/skills/create-iso-country-geohash your-project/.cursor/skills/
cp -R jzf-skills/skills/filter-geohash-ids your-project/.cursor/skills/
```

For Codex or any agent that reads repository instructions, keep the copied skills in a stable repo path such as `.agent-skills/` and reference them from `AGENTS.md`:

```markdown
Available skills:
- create-iso-country-geohash: .agent-skills/create-iso-country-geohash/SKILL.md
- filter-geohash-ids: .agent-skills/filter-geohash-ids/SKILL.md
```

If your agent has its own skill directory or configuration format, use the same copied folder and point it at the corresponding `SKILL.md`.

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
