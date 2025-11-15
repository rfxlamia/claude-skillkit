#!/usr/bin/env python3
"""
Skill Packager - Creates a distributable .skill file of a skill folder

v1.2 Update: Enhanced validation before packaging
- Checks for broken references
- Detects orphaned files
- Validates cross-references before packing

Usage:
    python utils/package_skill.py <path/to/skill-folder> [output-directory] [--strict]

Example:
    python utils/package_skill.py skills/public/my-skill
    python utils/package_skill.py skills/public/my-skill ./dist
    python utils/package_skill.py skills/public/my-skill ./dist --strict
"""

import sys
import zipfile
from pathlib import Path
from quick_validate import validate_skill

try:
    from utils.reference_validator import SkillPackageValidator
except ImportError:
    SkillPackageValidator = None  # Graceful fallback


def is_project_directory(path):
    """
    Check if a directory appears to be a valid project directory.

    A project directory is identified by common markers like:
    - .git (git repository)
    - package.json (Node.js project)
    - pyproject.toml or setup.py (Python project)
    - Cargo.toml (Rust project)
    - go.mod (Go project)
    - pom.xml or build.gradle (Java project)

    Args:
        path: Path object to check

    Returns:
        bool: True if directory appears to be a project directory
    """
    if not path.is_dir():
        return False

    project_markers = [
        '.git',
        'package.json',
        'pyproject.toml',
        'setup.py',
        'Cargo.toml',
        'go.mod',
        'pom.xml',
        'build.gradle',
        'composer.json',  # PHP
        'Gemfile',        # Ruby
    ]

    for marker in project_markers:
        if (path / marker).exists():
            return True

    return False


def package_skill(skill_path, output_dir=None, strict=False):
    """
    Package a skill folder into a .skill file.

    v1.2 Enhancement: Pre-packaging reference validation

    Args:
        skill_path: Path to the skill folder
        output_dir: Optional output directory for the .skill file (defaults to current directory)
        strict: If True, fail on any reference issues. If False, warn only.

    Returns:
        Path to the created .skill file, or None if error
    """
    skill_path = Path(skill_path).resolve()

    # Validate skill folder exists
    if not skill_path.exists():
        print(f"❌ Error: Skill folder not found: {skill_path}")
        return None

    if not skill_path.is_dir():
        print(f"❌ Error: Path is not a directory: {skill_path}")
        return None

    # Validate SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"❌ Error: SKILL.md not found in {skill_path}")
        return None

    # Run validation before packaging
    print("🔍 Validating skill...")
    valid, message = validate_skill(skill_path)
    if not valid:
        print(f"❌ Validation failed: {message}")
        print("   Please fix the validation errors before packaging.")
        return None
    print(f"✅ {message}\n")

    # v1.2: Enhanced reference validation before packaging
    print("🔗 Checking file references and orphaned files...")
    if SkillPackageValidator:
        try:
            pkg_validator = SkillPackageValidator(str(skill_path))
            ref_result = pkg_validator.validate_for_packaging(strict=strict)

            if ref_result.status == 'fail':
                if strict:
                    print(f"❌ Reference validation failed: {ref_result.message}")
                    print(f"   {ref_result.suggestion}")
                    return None
                else:
                    print(f"⚠️ Warning: {ref_result.message}")
                    if ref_result.missing_files:
                        print(f"   Missing files: {', '.join(ref_result.missing_files[:3])}")
                    if ref_result.orphaned_files:
                        print(f"   Orphaned files: {', '.join(ref_result.orphaned_files[:3])}")
                    print(f"   Tip: Use --strict to fail on reference issues\n")
            else:
                print(f"✅ References validated: {len(ref_result.valid_references)} files\n")
        except Exception as e:
            # Graceful fallback
            print(f"⚠️ Reference validation skipped (utility unavailable)\n")
    else:
        # Fallback if validator not available
        print(f"⚠️ Reference validation skipped (utility unavailable)\n")

    # Determine output location (hybrid approach)
    skill_name = skill_path.name
    if output_dir:
        # Priority 1: User-specified output directory
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory (user-specified): {output_path}")
    else:
        # Priority 2: Check if parent directory is a valid project directory
        parent_dir = skill_path.parent
        if is_project_directory(parent_dir):
            output_path = parent_dir
            print(f"📁 Output directory (project directory detected): {output_path}")
        else:
            # Priority 3: Use current working directory
            output_path = Path.cwd()
            print(f"📁 Output directory (current working directory): {output_path}")

    skill_filename = output_path / f"{skill_name}.skill"

    # Create the .skill file (zip format)
    try:
        print(f"\n📦 Creating archive: {skill_filename.name}")
        with zipfile.ZipFile(skill_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the skill directory
            for file_path in skill_path.rglob('*'):
                if file_path.is_file():
                    # Calculate the relative path within the zip
                    # Use skill_path (not skill_path.parent) to avoid wrapper folder
                    arcname = file_path.relative_to(skill_path)
                    zipf.write(file_path, arcname)
                    print(f"  Added: {arcname}")

        print(f"\n✅ Successfully packaged skill to: {skill_filename}")
        return skill_filename

    except Exception as e:
        print(f"❌ Error creating .skill file: {e}")
        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Package a skill folder into a distributable .skill file',
        epilog='Example: python package_skill.py skills/public/my-skill ./dist --strict'
    )
    parser.add_argument('skill_path', help='Path to the skill folder')
    parser.add_argument('output_dir', nargs='?', default=None,
                        help='Output directory for the .skill file (default: current directory)')
    parser.add_argument('--strict', action='store_true',
                        help='Fail if any reference issues found (default: warn only)')

    args = parser.parse_args()

    print(f"📦 Packaging skill: {args.skill_path}")
    if args.output_dir:
        print(f"   Output directory: {args.output_dir}")
    if args.strict:
        print(f"   Mode: STRICT (fail on reference issues)")
    print()

    result = package_skill(args.skill_path, args.output_dir, strict=args.strict)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
