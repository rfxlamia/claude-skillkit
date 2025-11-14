#!/usr/bin/env python3
"""
Score skill quality against best practices.
Based on comprehensive checklist from Files 01-13.

AGENT-LAYER TOOL: Called by Claude via bash_tool, outputs JSON for parsing.

This script evaluates skills across 5 categories:
- Structure (20 pts): YAML, organization, progressive disclosure
- Content (30 pts): Description, triggers, writing style, examples
- Efficiency (20 pts): Line count, token estimate, bloat detection
- Security (15 pts): No secrets, safe patterns, input validation
- Style (15 pts): Imperative form, conciseness, clear headers

Total: 100 points scoring system

References:
    File 01: Why Skills Exist
    File 02: Skills vs Subagents comparison
    File 05: Token economics
    File 07: Security concerns
    File 10: Technical architecture
    Files 01-13: Comprehensive best practices

Usage (Agent-Layer):
    python quality_scorer.py /path/to/skill --format json
    # Returns JSON: {"status": "success", "overall": {...}, "categories": {...}}

Usage (Human-Readable):
    python quality_scorer.py /path/to/skill
    python quality_scorer.py /path/to/skill --detailed
    python quality_scorer.py /path/to/skill --export report.json
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


class QualityScorer:
    """Score skill against best practices."""
    
    def __init__(self, skill_path: str, detailed: bool = False):
        """
        Initialize quality scorer.
        
        Args:
            skill_path: Path to skill directory
            detailed: If True, show detailed category breakdown
        
        References: Files 01-13 (all best practices)
        """
        self.skill_path = Path(skill_path)
        self.detailed = detailed
        self.scores = {}
        self.recommendations = []
        
        # Validate skill path
        if not self.skill_path.exists():
            raise FileNotFoundError(f"Skill directory not found: {skill_path}")
        
        if not (self.skill_path / "SKILL.md").exists():
            raise FileNotFoundError(f"SKILL.md not found in {skill_path}")
    
    # ========== SCORING CATEGORIES ==========
    
    def score_structure(self) -> Dict:
        """
        Score skill structure.
        
        Criteria (20 points):
        - YAML frontmatter valid (5 pts)
        - File organization correct (5 pts)
        - Progressive disclosure implemented (5 pts)
        - Reference files properly organized (5 pts)
        
        References: File 10 (architecture)
        """
        score = 0
        issues = []
        
        # Check YAML frontmatter
        if self._has_valid_yaml():
            score += 5
        else:
            issues.append("YAML frontmatter invalid or missing")
        
        # Check file organization
        if self._has_proper_structure():
            score += 5
        else:
            issues.append("File structure not optimal")
        
        # Check progressive disclosure
        if self._uses_progressive_disclosure():
            score += 5
        else:
            issues.append("Progressive disclosure not implemented")
        
        # Check references
        if self._references_organized():
            score += 5
        else:
            issues.append("References not properly organized")
        
        return {
            'score': score,
            'max': 20,
            'percentage': (score / 20) * 100,
            'issues': issues
        }
    
    def score_content(self) -> Dict:
        """
        Score content quality.
        
        Criteria (30 points):
        - Description includes WHAT + WHEN (10 pts)
        - Clear trigger conditions (5 pts)
        - Agent-layer writing style (10 pts)
        - Examples inline and relevant (5 pts)
        
        References: File 02 (description best practices)
        """
        score = 0
        issues = []
        
        # Check description quality
        desc_score = self._score_description()
        score += desc_score
        if desc_score < 10:
            issues.append("Description missing WHAT or WHEN")
        
        # Check trigger conditions
        if self._has_clear_triggers():
            score += 5
        else:
            issues.append("Trigger conditions unclear")
        
        # Check writing style
        style_score = self._score_writing_style()
        score += style_score
        if style_score < 10:
            issues.append("Writing style not agent-optimized")
        
        # Check examples
        if self._has_inline_examples():
            score += 5
        else:
            issues.append("Examples missing or in separate section")
        
        return {
            'score': score,
            'max': 30,
            'percentage': (score / 30) * 100,
            'issues': issues
        }
    
    def score_efficiency(self) -> Dict:
        """
        Score token efficiency.
        
        Criteria (20 points):
        - SKILL.md under 500 lines (10 pts)
        - Estimated tokens < 5,000 (5 pts)
        - No bloat detected (5 pts)
        
        References: File 05 (token economics)
        """
        score = 0
        issues = []
        
        skill_md = self.skill_path / "SKILL.md"
        with open(skill_md) as f:
            lines = f.readlines()
            line_count = len(lines)
            content = ''.join(lines)
        
        # Line count
        if line_count < 500:
            score += 10
        elif line_count < 800:
            score += 5
            issues.append(f"SKILL.md longer than ideal ({line_count} lines)")
        else:
            issues.append(f"SKILL.md too long ({line_count} lines)")
        
        # Token estimate (simplified: ~4 chars per token)
        estimated_tokens = len(content) // 4
        if estimated_tokens < 5000:
            score += 5
        else:
            issues.append(f"Estimated tokens high (~{estimated_tokens})")
        
        # Bloat detection (check for repetition)
        if not self._detect_bloat(content):
            score += 5
        else:
            issues.append("Content bloat detected")
        
        return {
            'score': score,
            'max': 20,
            'percentage': (score / 20) * 100,
            'issues': issues
        }
    
    def score_security(self) -> Dict:
        """
        Score security practices.
        
        Criteria (15 points):
        - No hardcoded secrets (5 pts)
        - No dangerous patterns (5 pts)
        - Input validation present (5 pts)
        
        References: File 07 (security concerns)
        """
        score = 0
        issues = []
        
        # Check for hardcoded secrets
        if not self._has_hardcoded_secrets():
            score += 5
        else:
            issues.append("Hardcoded secrets detected")
        
        # Check for dangerous patterns
        if not self._has_dangerous_patterns():
            score += 5
        else:
            issues.append("Dangerous code patterns detected")
        
        # Check input validation
        if self._has_input_validation():
            score += 5
        else:
            issues.append("Input validation missing or weak")
        
        return {
            'score': score,
            'max': 15,
            'percentage': (score / 15) * 100,
            'issues': issues
        }
    
    def score_style(self) -> Dict:
        """
        Score writing style.
        
        Criteria (15 points):
        - Imperative form used (5 pts)
        - Concise instructions (5 pts)
        - Clear section headers (5 pts)
        
        References: All micro-modules (agent-layer style)
        """
        score = 0
        issues = []
        
        skill_md = self.skill_path / "SKILL.md"
        with open(skill_md) as f:
            content = f.read()
        
        # Check imperative form
        imperative_ratio = self._count_imperative_sentences(content)
        if imperative_ratio > 0.5:
            score += 5
        elif imperative_ratio > 0.3:
            score += 3
            issues.append("More imperative voice recommended")
        else:
            issues.append("Not using imperative voice")
        
        # Check conciseness (sentence length)
        avg_sentence_length = self._calculate_avg_sentence_length(content)
        if avg_sentence_length < 20:
            score += 5
        elif avg_sentence_length < 30:
            score += 3
            issues.append("Sentences could be more concise")
        else:
            issues.append("Sentences too verbose")
        
        # Check headers
        if self._has_clear_headers(content):
            score += 5
        else:
            issues.append("Headers not descriptive enough")
        
        return {
            'score': score,
            'max': 15,
            'percentage': (score / 15) * 100,
            'issues': issues
        }
    
    # ========== HELPER METHODS ==========
    
    def _has_valid_yaml(self) -> bool:
        """Check if YAML frontmatter is valid."""
        skill_md = self.skill_path / "SKILL.md"
        with open(skill_md) as f:
            content = f.read()
        
        # Check for frontmatter delimiters
        if not content.startswith('---\n'):
            return False
        
        # Find end of frontmatter
        end_idx = content.find('\n---\n', 4)
        if end_idx == -1:
            return False
        
        frontmatter = content[4:end_idx]
        
        # Check for required fields
        has_name = 'name:' in frontmatter
        has_description = 'description:' in frontmatter
        
        return has_name and has_description
    
    def _has_proper_structure(self) -> bool:
        """Check if file structure is proper."""
        # Check for SKILL.md
        has_skill_md = (self.skill_path / "SKILL.md").exists()
        
        # Check if references directory exists and is used properly
        refs_dir = self.skill_path / "references"
        if refs_dir.exists():
            # Should have .md files
            has_ref_files = any(refs_dir.glob('*.md'))
            return has_skill_md and has_ref_files
        
        return has_skill_md
    
    def _uses_progressive_disclosure(self) -> bool:
        """Check if progressive disclosure is implemented."""
        skill_md = self.skill_path / "SKILL.md"
        with open(skill_md) as f:
            lines = f.readlines()
        
        # Check if SKILL.md is reasonably sized
        refs_dir = self.skill_path / "references"
        has_refs = refs_dir.exists() and any(refs_dir.glob('*.md'))
        
        # If file is short, progressive disclosure not needed
        # If file is long, should have references
        return len(lines) < 500 or has_refs
    
    def _references_organized(self) -> bool:
        """Check if references are organized."""
        refs_dir = self.skill_path / "references"
        if not refs_dir.exists():
            return True  # OK if no references needed
        
        # Check for proper filenames (lowercase, no spaces)
        for ref_file in refs_dir.glob('*.md'):
            if not ref_file.stem.replace('-', '').replace('_', '').isalnum():
                return False
            if ' ' in ref_file.stem:
                return False
        
        return True
    
    def _score_description(self) -> int:
        """Score description quality (0-10)."""
        skill_md = self.skill_path / "SKILL.md"
        with open(skill_md) as f:
            content = f.read()
        
        # Get frontmatter and first 500 chars
        relevant_section = content[:1000].lower()
        
        # Check for WHAT (task/functionality description)
        what_keywords = ['comprehensive', 'provides', 'enables', 'supports', 'tools for', 
                        'guide', 'system', 'framework', 'utility']
        has_what = any(kw in relevant_section for kw in what_keywords)
        
        # Check for WHEN (trigger conditions)
        when_keywords = ['when', 'use when', 'trigger', 'for tasks', 'invoke', 
                        'if', 'needs to', 'requires', 'working with']
        has_when = any(kw in relevant_section for kw in when_keywords)
        
        if has_what and has_when:
            return 10
        elif has_what or has_when:
            return 5
        else:
            return 0
    
    def _has_clear_triggers(self) -> bool:
        """Check for clear trigger conditions."""
        skill_md = self.skill_path / "SKILL.md"
        with open(skill_md) as f:
            content = f.read()[:1500]  # Check first 1500 chars
        
        trigger_keywords = ['use when', 'trigger', 'invoke', 'activate', 
                           'when claude needs', 'use this skill']
        return any(kw in content.lower() for kw in trigger_keywords)
    
    def _score_writing_style(self) -> int:
        """Score writing style (0-10)."""
        skill_md = self.skill_path / "SKILL.md"
        with open(skill_md) as f:
            content = f.read()
        
        score = 0
        
        # Check for structured formatting (lists, code blocks, tables)
        has_code_blocks = '```' in content
        has_lists = bool(re.search(r'^[\-\*]\s', content, re.MULTILINE))
        has_tables = '|' in content
        
        if has_code_blocks or has_lists:
            score += 3
        if has_tables:
            score += 2
        
        # Check for direct, actionable language
        action_verbs = ['use', 'run', 'execute', 'create', 'configure', 
                       'install', 'check', 'validate', 'ensure']
        verb_count = sum(content.lower().count(verb) for verb in action_verbs)
        if verb_count > 10:
            score += 3
        elif verb_count > 5:
            score += 2
        
        # Check for proper section organization
        section_headers = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
        if len(section_headers) >= 3:
            score += 2
        
        return min(score, 10)
    
    def _has_inline_examples(self) -> bool:
        """Check if examples are inline."""
        skill_md = self.skill_path / "SKILL.md"
        with open(skill_md) as f:
            content = f.read()
        
        # Check for code blocks (indicates examples present)
        has_code_blocks = '```' in content
        
        # Check if "Examples" is a separate section (bad practice)
        has_separate_examples = bool(re.search(r'^##\s+Examples?\s*$', content, re.MULTILINE))
        
        return has_code_blocks and not has_separate_examples
    
    def _detect_bloat(self, content: str) -> bool:
        """Detect content bloat."""
        # Check for very long sections
        sections = content.split('\n## ')
        for section in sections:
            section_lines = section.split('\n')
            if len(section_lines) > 150:
                return True  # Section too long
        
        # Check for excessive repetition
        lines = content.split('\n')
        if len(lines) > 100:
            # Sample check: look for repeated patterns
            line_set = set(lines)
            repetition_ratio = len(line_set) / len(lines)
            if repetition_ratio < 0.7:  # Less than 70% unique lines
                return True
        
        return False
    
    def _has_hardcoded_secrets(self) -> bool:
        """Check for hardcoded secrets."""
        patterns = [
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'bearer\s+[A-Za-z0-9\-._~+/]+=*',
        ]
        
        # Scan all files in skill directory
        for file in self.skill_path.rglob('*'):
            if file.is_file() and file.suffix in ['.md', '.py', '.sh', '.yml', '.yaml']:
                try:
                    with open(file, encoding='utf-8') as f:
                        content = f.read()
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                return True
                except:
                    continue
        
        return False
    
    def _has_dangerous_patterns(self) -> bool:
        """Check for dangerous code patterns."""
        dangerous_patterns = [
            r'\beval\s*\(',
            r'\bexec\s*\(',
            r'shell\s*=\s*True',
            r'os\.system\(',
            r'subprocess\..*shell=True',
        ]
        
        # Scan Python scripts
        for script in self.skill_path.rglob('*.py'):
            try:
                with open(script, encoding='utf-8') as f:
                    content = f.read()
                    for pattern in dangerous_patterns:
                        if re.search(pattern, content):
                            return True
            except:
                continue
        
        return False
    
    def _has_input_validation(self) -> bool:
        """Check if input validation exists."""
        validation_keywords = ['validate', 'check', 'verify', 'assert', 'raise', 
                              'isinstance', 'try:', 'except:', 'if not']
        
        # Check SKILL.md for validation mentions
        skill_md = self.skill_path / "SKILL.md"
        with open(skill_md) as f:
            skill_content = f.read()
            has_validation_docs = any(kw in skill_content.lower() for kw in validation_keywords[:3])
        
        # Check Python scripts for validation code
        has_validation_code = False
        for script in self.skill_path.rglob('*.py'):
            try:
                with open(script, encoding='utf-8') as f:
                    content = f.read()
                    if any(kw in content for kw in validation_keywords):
                        has_validation_code = True
                        break
            except:
                continue
        
        return has_validation_docs or has_validation_code
    
    def _count_imperative_sentences(self, content: str) -> float:
        """Calculate ratio of imperative sentences."""
        # Imperative verbs commonly used in documentation
        imperative_verbs = [
            'use', 'run', 'execute', 'create', 'configure', 'install',
            'check', 'validate', 'ensure', 'verify', 'set', 'define',
            'specify', 'provide', 'include', 'add', 'remove', 'update',
            'follow', 'read', 'write', 'call', 'invoke', 'load', 'scan',
            'extract', 'detect', 'discover', 'generate', 'implement'
        ]

        # Remove YAML frontmatter
        processed_content = content
        if content.startswith('---\n'):
            end_idx = content.find('\n---\n', 4)
            if end_idx != -1:
                processed_content = content[end_idx + 5:]

        # Remove code blocks to avoid counting code as sentences
        processed_content = re.sub(r'```.*?```', '', processed_content, flags=re.DOTALL)

        # Split into sentences (approximate)
        sentences = re.split(r'[.!?]\n', processed_content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not sentences:
            return 0.0

        # Count sentences with imperative verbs
        imperative_count = 0
        for sentence in sentences:
            # Strip markdown formatting (bold, italic, inline code)
            clean_sentence = re.sub(r'\*\*([^*]+)\*\*', r'\1', sentence)
            clean_sentence = re.sub(r'\*([^*]+)\*', r'\1', clean_sentence)
            clean_sentence = re.sub(r'`([^`]+)`', r'\1', clean_sentence)
            clean_sentence = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_sentence)

            # Remove special markers and colons at start
            clean_sentence = re.sub(r'^[\-\*\+]\s+', '', clean_sentence)
            clean_sentence = clean_sentence.strip()

            if not clean_sentence:
                continue

            # Get first 3 words to check for imperative
            words = clean_sentence.lower().split()
            first_words = words[:3] if len(words) >= 3 else words

            # Check if any of first 3 words is imperative verb
            has_imperative = any(
                any(word.startswith(verb) for verb in imperative_verbs)
                for word in first_words
            )

            if has_imperative:
                imperative_count += 1

        return imperative_count / len(sentences)
    
    def _calculate_avg_sentence_length(self, content: str) -> float:
        """Calculate average sentence length in words."""
        # Remove code blocks to avoid skewing results
        content_no_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        
        sentences = re.split(r'[.!?]\s+', content_no_code)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if not sentences:
            return 0.0
        
        total_words = sum(len(s.split()) for s in sentences)
        return total_words / len(sentences)
    
    def _has_clear_headers(self, content: str) -> bool:
        """Check if headers are clear and descriptive."""
        headers = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
        
        if not headers:
            return False
        
        # Check if headers are descriptive (more than 2 words or technical term)
        descriptive_count = 0
        for header in headers:
            header_clean = header.strip()
            words = header_clean.split()
            
            # Consider descriptive if: >2 words OR has technical indicators
            is_descriptive = (
                len(words) > 2 or
                any(char.isupper() for char in header_clean[1:]) or  # CamelCase
                '-' in header_clean or '_' in header_clean  # technical terms
            )
            
            if is_descriptive:
                descriptive_count += 1
        
        # At least 70% of headers should be descriptive
        return descriptive_count / len(headers) >= 0.7
    
    # ========== MAIN SCORING ==========
    
    def calculate_overall_score(self) -> Dict:
        """
        Calculate overall quality score.
        
        Combines all category scores into overall rating.
        
        Returns:
            Dict with overall score and breakdown
        """
        # Score each category
        self.scores['structure'] = self.score_structure()
        self.scores['content'] = self.score_content()
        self.scores['efficiency'] = self.score_efficiency()
        self.scores['security'] = self.score_security()
        self.scores['style'] = self.score_style()
        
        # Calculate total
        total_score = sum(s['score'] for s in self.scores.values())
        total_max = sum(s['max'] for s in self.scores.values())
        overall_percentage = (total_score / total_max) * 100
        
        # Collect all issues
        all_issues = []
        for category, data in self.scores.items():
            for issue in data['issues']:
                all_issues.append(f"{category.capitalize()}: {issue}")
        
        return {
            'score': total_score,
            'max': total_max,
            'percentage': overall_percentage,
            'grade': self._get_grade(overall_percentage),
            'issues': all_issues,
            'categories': self.scores
        }
    
    def _get_grade(self, percentage: float) -> str:
        """Convert percentage to letter grade."""
        if percentage >= 90:
            return 'A (Excellent)'
        elif percentage >= 80:
            return 'B (Good)'
        elif percentage >= 70:
            return 'C (Fair)'
        elif percentage >= 60:
            return 'D (Needs Improvement)'
        else:
            return 'F (Poor)'
    
    def display_report(self, overall: Dict):
        """Display quality report to console."""
        print("\n" + "="*60)
        print("SKILL QUALITY REPORT")
        print("="*60)
        print(f"\nSkill: {self.skill_path.name}")
        print(f"Overall Score: {overall['score']}/{overall['max']} ({overall['percentage']:.1f}%)")
        print(f"Grade: {overall['grade']}")
        
        if self.detailed:
            print("\nCategory Breakdown:")
            for category, data in self.scores.items():
                print(f"\n  {category.capitalize():12} {data['score']:2}/{data['max']:2} ({data['percentage']:5.1f}%)")
                if data['issues']:
                    for issue in data['issues']:
                        print(f"    âš ï¸  {issue}")
        
        if overall['issues']:
            print("\n" + "-"*60)
            print("Recommendations:")
            for i, issue in enumerate(overall['issues'], 1):
                print(f"  {i}. {issue}")
        
        print("\n" + "="*60)
        print("References:")
        print("  â€¢ Files 01-13: Best practices documentation")
        print("  â€¢ File 05: Token optimization")
        print("  â€¢ File 07: Security guidelines")
        print("  â€¢ File 10: Architecture standards")
        print("="*60 + "\n")
    
    def export_json(self, filepath: str, overall: Dict):
        """Export report as JSON."""
        report = {
            'skill_path': str(self.skill_path),
            'skill_name': self.skill_path.name,
            'overall': {
                'score': overall['score'],
                'max': overall['max'],
                'percentage': round(overall['percentage'], 2),
                'grade': overall['grade']
            },
            'categories': {
                category: {
                    'score': data['score'],
                    'max': data['max'],
                    'percentage': round(data['percentage'], 2),
                    'issues': data['issues']
                }
                for category, data in overall['categories'].items()
            },
            'recommendations': overall['issues']
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
    
    def export_markdown(self, filepath: str, overall: Dict):
        """Export report as Markdown."""
        lines = []
        
        lines.append("# Skill Quality Report")
        lines.append("")
        lines.append(f"**Skill:** {self.skill_path.name}")
        lines.append(f"**Path:** `{self.skill_path}`")
        lines.append("")
        
        lines.append("## Overall Score")
        lines.append("")
        lines.append(f"- **Score:** {overall['score']}/{overall['max']} ({overall['percentage']:.1f}%)")
        lines.append(f"- **Grade:** {overall['grade']}")
        lines.append("")
        
        lines.append("## Category Breakdown")
        lines.append("")
        lines.append("| Category | Score | Percentage | Status |")
        lines.append("|----------|-------|------------|--------|")
        
        for category, data in overall['categories'].items():
            status = "âœ…" if data['percentage'] >= 80 else "âš ï¸" if data['percentage'] >= 60 else "âŒ"
            lines.append(f"| {category.capitalize()} | {data['score']}/{data['max']} | {data['percentage']:.1f}% | {status} |")
        
        lines.append("")
        
        # Detailed issues per category
        if any(data['issues'] for data in overall['categories'].values()):
            lines.append("## Issues by Category")
            lines.append("")
            
            for category, data in overall['categories'].items():
                if data['issues']:
                    lines.append(f"### {category.capitalize()}")
                    lines.append("")
                    for issue in data['issues']:
                        lines.append(f"- âš ï¸ {issue}")
                    lines.append("")
        
        # Recommendations
        if overall['issues']:
            lines.append("## Recommendations")
            lines.append("")
            for i, issue in enumerate(overall['issues'], 1):
                lines.append(f"{i}. {issue}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("**References:**")
        lines.append("- Files 01-13: Best practices documentation")
        lines.append("- File 05: Token optimization")
        lines.append("- File 07: Security guidelines")
        lines.append("- File 10: Architecture standards")
        
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Score skill quality against best practices",
        epilog="References: Files 01-13 for comprehensive best practices"
    )
    parser.add_argument(
        'skill_path',
        type=str,
        help='Path to skill directory'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['text', 'json'],
        default='text',
        help='Output format: text (human-readable) or json (agent-layer)'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed category breakdown (text format only)'
    )
    parser.add_argument(
        '--export',
        type=str,
        help='Export report to file (JSON or MD format based on extension)'
    )
    
    args = parser.parse_args()
    
    try:
        scorer = QualityScorer(args.skill_path, detailed=args.detailed)
        overall = scorer.calculate_overall_score()
        
        # Agent-layer JSON output (stdout)
        if args.format == 'json':
            import sys
            report = {
                'status': 'success',
                'skill_path': str(scorer.skill_path),
                'skill_name': scorer.skill_path.name,
                'overall': {
                    'score': overall['score'],
                    'max': overall['max'],
                    'percentage': round(overall['percentage'], 2),
                    'grade': overall['grade']
                },
                'categories': {
                    category: {
                        'score': data['score'],
                        'max': data['max'],
                        'percentage': round(data['percentage'], 2),
                        'issues': data['issues']
                    }
                    for category, data in overall['categories'].items()
                },
                'recommendations': overall['issues']
            }
            print(json.dumps(report, indent=2))
            return 0
        
        # Human-readable text output (console)
        scorer.display_report(overall)
        
        if args.export:
            export_path = Path(args.export)
            
            if export_path.suffix.lower() == '.json':
                scorer.export_json(args.export, overall)
                print(f"âœ… Report exported to {args.export}")
            elif export_path.suffix.lower() in ['.md', '.markdown']:
                scorer.export_markdown(args.export, overall)
                print(f"âœ… Report exported to {args.export}")
            else:
                print(f"âš ï¸  Unknown export format. Use .json or .md extension.")
                return 1
        
        # Return exit code based on score
        if overall['percentage'] >= 70:
            return 0
        else:
            return 1
            
    except FileNotFoundError as e:
        if args.format == 'json':
            error_report = {
                'status': 'error',
                'error_type': 'FileNotFound',
                'message': str(e),
                'help': 'Ensure skill directory exists and contains SKILL.md'
            }
            print(json.dumps(error_report, indent=2))
        else:
            print(f"âŒ Error: {e}")
        return 1
    except Exception as e:
        if args.format == 'json':
            error_report = {
                'status': 'error',
                'error_type': 'UnexpectedError',
                'message': str(e),
                'help': 'Check skill structure and permissions'
            }
            print(json.dumps(error_report, indent=2))
        else:
            print(f"âŒ Unexpected error: {e}")
        return 2


if __name__ == "__main__":
    exit(main())
