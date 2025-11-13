# Plugin Distribution Guide

**Version:** 1.3.0-draft
**Status:** Work in Progress
**Purpose:** Guide for distributing skills via Claude Code plugin marketplace

---

## Overview

This guide documents how to package and distribute Claude Code skills as installable plugins through the marketplace system. Based on real-world implementation and testing of the Advanced Skill Creator plugin.

**Why Plugin Distribution?**

- **One-Command Install:** Users install via `/plugin marketplace add` instead of manual extraction
- **Auto-Discovery:** Skills automatically available after plugin installation
- **Team Collaboration:** Easy sharing across teams via GitHub/Git repositories
- **Version Management:** Built-in update mechanism through plugin manager
- **Professional Distribution:** Standard approach for Claude Code ecosystem

---

## Prerequisites

Before creating plugin distribution:

1. **Working skill** - Fully tested with SKILL.md in skill directory
2. **Git repository** - Hosted on GitHub or accessible Git server
3. **Repository structure** - Standard skill layout with scripts, knowledge, references
4. **License file** - Apache-2.0 recommended (matches Anthropic's skills repo)
5. **README.md** - Documentation with installation instructions

---

## Plugin Structure

### Required Files

```
your-repo/                          # Repository root
├── .claude-plugin/                 # Plugin configuration directory
│   ├── plugin.json                # Plugin manifest (REQUIRED)
│   └── marketplace.json           # Marketplace catalog (REQUIRED)
├── skills/                        # Skills directory
│   └── your-skill/               # Skill folder
│       ├── SKILL.md              # Skill definition
│       ├── knowledge/            # Knowledge base
│       ├── scripts/              # Automation scripts (if any)
│       └── references/           # Reference docs
├── LICENSE                        # License file
├── README.md                      # Documentation
└── .gitignore                     # Git ignore (include .claude/)
```

### Key Conventions

1. **Plugin root = Repository root** - `.claude-plugin/` at repo root
2. **Skills in skills/ directory** - Standard location for all skills
3. **One skill per folder** - Each skill in `skills/skill-name/` with SKILL.md
4. **Auto-discovery** - Claude Code finds all SKILL.md files in skills/*/

---

## Step 1: Create Plugin Manifest

**File:** `.claude-plugin/plugin.json`

```json
{
  "name": "your-plugin-name",
  "description": "Brief description of what your plugin does. Max 2-3 sentences.",
  "version": "1.0.0",
  "author": {
    "name": "Your Name or GitHub Username",
    "email": "your@email.com"
  },
  "homepage": "https://github.com/username/repo",
  "repository": "https://github.com/username/repo",
  "license": "Apache-2.0",
  "keywords": [
    "skill-creator",
    "automation",
    "your-domain"
  ]
}
```

**Field Guidelines:**

- `name`: kebab-case, no spaces, unique identifier
- `description`: Clear value proposition, shown in plugin browser
- `version`: Semantic versioning (MAJOR.MINOR.PATCH)
- `author.name`: GitHub username recommended for attribution
- `author.email`: Real email or username@github.com format
- `license`: Apache-2.0 recommended (Anthropic ecosystem standard)
- `keywords`: 3-6 descriptive terms for discoverability

**Validation:**

```bash
# Validate JSON syntax
python3 -m json.tool .claude-plugin/plugin.json
```

---

## Step 2: Create Marketplace Catalog

**File:** `.claude-plugin/marketplace.json`

```json
{
  "name": "your-marketplace-name",
  "owner": {
    "name": "Your Name",
    "email": "your@email.com"
  },
  "plugins": [
    {
      "name": "your-plugin-name",
      "description": "Same description as plugin.json for consistency",
      "source": "./",
      "version": "1.0.0",
      "author": {
        "name": "Your Name"
      },
      "homepage": "https://github.com/username/repo",
      "repository": "https://github.com/username/repo",
      "license": "Apache-2.0",
      "keywords": [
        "same-keywords",
        "as-plugin-json"
      ]
    }
  ]
}
```

**Important Notes:**

- `"source": "./"` - Points to repository root (correct for our structure)
- `plugins` array - Can list multiple plugins from same marketplace
- Keep metadata consistent between plugin.json and marketplace.json
- `name` in marketplace.json can differ from plugin name (marketplace identifier)

**Validation:**

```bash
# Validate JSON syntax
python3 -m json.tool .claude-plugin/marketplace.json
```

---

## Step 3: Update .gitignore

Add Claude Code local settings to `.gitignore`:

```gitignore
# Claude Code local settings
.claude/
```

**Why?** `.claude/` contains:
- `settings.local.json` - Personal permissions/settings
- `skills/` - Locally installed skills (user-specific)

These should NOT be committed to version control.

---

## Step 4: Update README.md

Add plugin installation instructions to README:

```markdown
### Installation

**Option 1: Install via Plugin (Recommended)**

```bash
# In Claude Code, add the marketplace
/plugin marketplace add username/repo-name

# Then install the plugin
/plugin install plugin-name@username
```

Or use the interactive plugin menu:
```bash
/plugin
# Select "Browse Plugins" → Find "plugin-name" → Install
```

**Option 2: Manual Installation (.skill file)**

```bash
# Extract and install (.skill files are zip archives)
unzip skill-name.skill -d ~/.claude/skills/skill-name
```
```

**Update all path references:**
- Old: `skill-name/scripts/tool.py`
- New: `skills/skill-name/scripts/tool.py`

---

## Step 5: Restructure Repository

Move existing skill to standard plugin structure:

```bash
# Create skills directory
mkdir -p skills

# Move skill (use git mv to preserve history)
git mv your-skill skills/

# Verify structure
ls skills/your-skill/
# Expected: SKILL.md, knowledge/, scripts/, references/
```

**Update all documentation paths:**
- README.md references
- Internal skill documentation
- Script path examples
- Knowledge base cross-references

---

## Step 6: Test Locally (Optional)

Before pushing, test plugin structure locally:

```bash
# Validate JSON files
python3 -m json.tool .claude-plugin/plugin.json > /dev/null
python3 -m json.tool .claude-plugin/marketplace.json > /dev/null

# Check directory structure
ls -la .claude-plugin/
ls -la skills/

# Verify SKILL.md exists
cat skills/your-skill/SKILL.md | head -20
```

---

## Step 7: Commit and Push

```bash
# Stage plugin files
git add .claude-plugin/

# Stage restructured skills
git add skills/

# Update gitignore
git add .gitignore

# Update README
git add README.md

# Commit with descriptive message
git commit -m "Add plugin distribution support

- Created .claude-plugin/ with plugin manifest and marketplace catalog
- Restructured repository with skills/ directory
- Updated README with plugin installation instructions
- Added .claude/ to gitignore for local settings"

# Push to remote
git push origin main
```

---

## Step 8: Test Installation

In a clean Claude Code session:

```bash
# Add marketplace
/plugin marketplace add username/repo-name

# Expected: Marketplace successfully added
```

```bash
# Browse plugins
/plugin

# Expected: See your plugin in the list with description
```

```bash
# Install plugin
/plugin install plugin-name@username

# Expected: Plugin installed successfully
```

**Verify skill discovery:**

```bash
# In chat, invoke skill
"[trigger phrase for your skill]"

# Expected: Skill executes and produces output
```

---

## Troubleshooting

### Issue 1: Marketplace Not Found

**Symptoms:**
```
Error: Could not find marketplace at username/repo-name
```

**Solutions:**
- Verify repository is public (or accessible with credentials)
- Check repository URL: `https://github.com/username/repo-name`
- Ensure `.claude-plugin/marketplace.json` exists at repository root
- Try with explicit HTTPS URL: `/plugin marketplace add https://github.com/username/repo`

### Issue 2: Plugin Install Fails

**Symptoms:**
```
Error: Could not install plugin
```

**Solutions:**
- Validate `.claude-plugin/plugin.json` syntax: `python3 -m json.tool`
- Check `skills/` directory exists at repository root
- Verify `SKILL.md` exists in `skills/your-skill/`
- Ensure `"source": "./"` in marketplace.json points to correct location

### Issue 3: Skill Not Discovered

**Symptoms:**
- Plugin installs successfully
- But skill not available when invoked

**Solutions:**
- Restart Claude Code to refresh skill cache
- Check plugin status: `/plugin` → Verify enabled
- Verify directory structure: `skills/skill-name/SKILL.md` (case-sensitive!)
- Check SKILL.md `name:` field in frontmatter matches expected
- Try explicit skill invocation with skill name

### Issue 4: Path References Broken

**Symptoms:**
- Skill loads but scripts fail
- Documentation links broken

**Solutions:**
- Update all paths from `skill-name/` to `skills/skill-name/`
- Search and replace in:
  - README.md
  - SKILL.md
  - Knowledge base docs
  - Script examples
- Test script paths: `python skills/skill-name/scripts/tool.py --help`

---

## Best Practices

### 1. License Consistency

**Recommendation:** Use Apache-2.0 for Claude Code skills

**Rationale:**
- Matches Anthropic's official skills repository
- Provides patent protection (important for novel automation)
- Enterprise-friendly (clear terms for commercial use)
- Compatible with MIT dependencies (one-way compatibility)

**If reusing Anthropic code:**
- MUST use Apache-2.0 (derivative works requirement)
- Include original NOTICE file
- Attribute Anthropic in README

### 2. Versioning Strategy

**Semantic Versioning:**
- `MAJOR.MINOR.PATCH` (e.g., 1.2.3)
- MAJOR: Breaking changes (restructure, removed features)
- MINOR: New features (backward compatible)
- PATCH: Bug fixes, documentation

**Keep in sync:**
- `.claude-plugin/plugin.json` version
- `.claude-plugin/marketplace.json` plugin version
- README.md version badge
- CHANGELOG.md latest version

### 3. Metadata Quality

**Good descriptions:**
- "Professional skill creation with research-driven workflow and automated validation"
- "Create comprehensive README files grounded in codebase reality"

**Bad descriptions:**
- "A tool for making skills" (too vague)
- "The best skill creator ever made" (marketing fluff)

**Keywords:**
- Use 3-6 specific, searchable terms
- Include: domain, function, key features
- Examples: `skill-creator`, `validation`, `automation`, `testing`

### 4. Documentation

**README must include:**
- Clear installation instructions (plugin + manual)
- Quick start guide with example
- Feature overview
- Link to full documentation
- Troubleshooting section

**Knowledge base:**
- Keep plugin-guide.md updated with lessons learned
- Document common issues and solutions
- Include testing procedures

### 5. Testing Before Release

**Pre-push checklist:**
- [ ] JSON files validate (no syntax errors)
- [ ] Directory structure correct (skills/ at root)
- [ ] SKILL.md exists and loads
- [ ] All paths updated (no broken references)
- [ ] .gitignore includes .claude/
- [ ] README has plugin instructions
- [ ] License file present

**Post-push testing:**
- [ ] Marketplace add works
- [ ] Plugin appears in browser
- [ ] Plugin installs successfully
- [ ] Skill auto-discovered
- [ ] Skill executes correctly

---

## Integration with Skill Creation Workflow

**Current Workflow (v1.2):**
```
Steps 1-8: Create skill → Validate → Test → Quality check
Step 9: Package skill (.skill file)
```

**Proposed Workflow (v1.3):**
```
Steps 1-8: Create skill → Validate → Test → Quality check
Step 9: Package skill (.skill file)
Step 10: [OPTIONAL] Plugin distribution setup
  - Create .claude-plugin/ files
  - Restructure to skills/ directory
  - Update documentation
  - Test plugin installation
  - Push to repository
```

**When to use plugin distribution:**
- Skill is stable and production-ready
- Want team-wide distribution
- Plan to maintain long-term
- Need version management
- Public release intended

**When to skip:**
- Quick prototype or experiment
- Single-user tool
- Embedded in specific project
- Temporary/disposable skill

---

## Real-World Example

**Repository:** github.com/rfxlamia/claude-advanced-skill-creator

**What worked:**
✅ `"source": "./"` for repository root reference
✅ `skills/advanced-skill-creator/` standard structure
✅ Apache-2.0 license (matches ecosystem)
✅ Comprehensive README with 3 install options
✅ .claude/ in .gitignore (avoid committing local settings)

**Testing results:**
- Marketplace add: Success ✅
- Plugin browser listing: Success ✅
- Plugin installation: Success ✅
- Skill discovery: Success ✅
- Skill execution: Success ✅
- 963 lines of successful execution log

**Lessons learned:**
1. Structure matters - skills/ directory must be at root
2. JSON validation catches 90% of issues early
3. Path updates needed everywhere (README, docs, examples)
4. .claude/ directory should always be gitignored
5. Real-world testing reveals edge cases (command accuracy, paths)

---

## Future Enhancements (v1.3+)

**Planned features:**

1. **Automated plugin setup script**
   - `scripts/setup_plugin.py` - Interactive setup wizard
   - Prompts for plugin name, description, author
   - Generates .claude-plugin/ files
   - Restructures repository automatically

2. **Plugin validation tool**
   - `scripts/validate_plugin.py` - Pre-push validation
   - Checks JSON syntax
   - Verifies directory structure
   - Tests path references
   - Simulates plugin installation

3. **Integration with package_skill.py**
   - Optional `--plugin` flag: `package_skill.py skill-name/ --plugin`
   - Auto-creates plugin structure if not exists
   - Prompts for missing metadata
   - Updates README with plugin instructions

4. **Testing automation**
   - Mock plugin installation locally
   - Verify skill discovery
   - Test skill execution in sandbox

5. **Multi-skill plugins**
   - Support multiple skills in skills/ directory
   - Automatic marketplace.json generation for all skills
   - Grouped distribution (related skills together)

6. **Version management**
   - Auto-sync version numbers across files
   - Changelog generation from git commits
   - Release tagging automation

---

## References

**Official Documentation:**
- Claude Code Plugin Guide: https://code.claude.com/docs/en/plugins.md
- Plugin Marketplaces: https://code.claude.com/docs/en/plugin-marketplaces.md
- Skills Guide: https://code.claude.com/docs/en/skills.md

**Related Files:**
- `SKILL.md` - Main skill definition
- `CHANGELOG.md` - Version history
- `knowledge/INDEX.md` - Knowledge base map
- `README.md` - User-facing documentation

**Tools:**
- `scripts/package_skill.py` - Skill packaging (v1.2)
- `scripts/validate_skill.py` - Structure validation
- `scripts/quality_scorer.py` - Quality assessment

---

## Changelog

**v1.3.0-draft (2025-11-14)**
- Initial plugin distribution guide
- Based on successful advanced-skill-creator plugin implementation
- Documented real-world testing results (963-line execution log)
- Included troubleshooting from actual issues encountered
- Proposed integration with v1.3 workflow

**Next Steps:**
- Implement automated setup script
- Create plugin validation tool
- Integrate with existing workflow
- Add multi-skill plugin support
- Write comprehensive testing procedures

---

## Contributing

If you've implemented plugin distribution for your skill:

1. **Share lessons learned** - Open issue or PR with insights
2. **Report issues** - Document problems and solutions
3. **Improve guide** - Submit clarifications or corrections
4. **Add examples** - Real-world implementations help everyone

**Feedback welcome:**
- GitHub Issues: Report problems or suggest improvements
- Pull Requests: Contribute fixes or enhancements
- Discussions: Share experiences and best practices

---

**Last Updated:** 2025-11-14
**Tested With:** Claude Code v2.0.37
**Status:** Draft (pending v1.3 release)
