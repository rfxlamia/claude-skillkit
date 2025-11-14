#!/usr/bin/env python3
"""
Decision helper for Skills vs Subagents - AGENT-LAYER TOOL.
Called by Claude to provide instant recommendations based on use case analysis.

This script implements the 8-question decision tree from Files 02-03 and returns
structured JSON output for Claude to parse and explain to users.

Usage by Claude:
    # Mode 1: Pre-answered questions (preferred)
    python decision_helper.py --answers /tmp/answers.json [--format json]

    # Mode 2: Keyword-based analysis (fallback)
    python decision_helper.py --analyze "code review with validation" [--format json]

    # Mode 3: Show decision criteria (reference)
    python decision_helper.py --show-criteria [--format json]

References:
- File 02: Skills vs Subagents conceptual differences
- File 03: Decision tree logic and scoring
- File 05: Token economics analysis

Author: Claude Skills Research Project
Version: 1.1 (Agent-Layer with text mode support)
"""

import json
import sys
import argparse
from typing import Dict, List, Optional
from pathlib import Path

# Import shared utilities for standardized output
try:
    from utils.output_formatter import add_format_argument
except ImportError:
    # Fallback if utils not in path
    sys.path.insert(0, str(Path(__file__).parent))
    from utils.output_formatter import add_format_argument


class DecisionHelper:
    """
    Agent-layer decision helper for Skills vs Subagents.
    
    Designed to be called by Claude via bash_tool, not by humans directly.
    All input/output is JSON for programmatic parsing.
    """
    
    def __init__(self):
        """Initialize decision helper with question definitions."""
        self.answers: Dict[str, bool] = {}
        self.score: int = 0
        self.reasoning: List[str] = []
        self.questions = self._define_questions()
    
    def _define_questions(self) -> Dict:
        """
        Define 8 decision questions with keywords for inference.
        
        Returns:
            Dict mapping question IDs to question data
            
        References: File 03 (decision tree questions)
        """
        return {
            "utility_task": {
                "question": "Is it a utility/conversion/template task?",
                "examples": [
                    "Format conversion (JSON to CSV)",
                    "Data extraction from documents",
                    "Template application"
                ],
                "skill_keywords": [
                    "convert", "transform", "template", "format",
                    "extract", "parse", "utility", "validation"
                ],
                "score_if_yes": +1,
                "score_if_no": -1
            },
            "multi_step": {
                "question": "Does it need multiple steps of reasoning?",
                "examples": [
                    "Code review with validation loops",
                    "Data analysis with hypothesis testing",
                    "Iterative refinement processes"
                ],
                "subagent_keywords": [
                    "review", "analyze", "validate", "iterate",
                    "hypothesis", "decision", "multiple", "steps",
                    "refinement", "exploration"
                ],
                "score_if_yes": -1,
                "score_if_no": +1
            },
            "reusable": {
                "question": "Will it be reused as building block?",
                "examples": [
                    "Document converter used by multiple workflows",
                    "Data parser for common formats",
                    "Shared utility function"
                ],
                "skill_keywords": [
                    "reusable", "utility", "helper", "common",
                    "shared", "library", "building block"
                ],
                "score_if_yes": +1,
                "score_if_no": -1
            },
            "specialized_personality": {
                "question": "Does it need specialized personality?",
                "examples": [
                    "Security auditor with paranoid perspective",
                    "Code reviewer with strict standards",
                    "Domain expert with specific tone"
                ],
                "subagent_keywords": [
                    "personality", "persona", "role", "expert",
                    "specialized", "tone", "perspective", "auditor"
                ],
                "score_if_yes": -1,
                "score_if_no": +1
            },
            "missing_knowledge": {
                "question": "Is it knowledge Claude doesn't have?",
                "examples": [
                    "Company-specific procedures",
                    "Proprietary methodologies",
                    "Organizational standards"
                ],
                "skill_keywords": [
                    "company", "proprietary", "organizational",
                    "internal", "procedure", "standard", "policy"
                ],
                "score_if_yes": +1,
                "score_if_no": 0  # Neutral if Claude knows it
            },
            "coordination": {
                "question": "Does it coordinate operations with decision points?",
                "examples": [
                    "Multi-stage validation with branching",
                    "Orchestration with conditional logic",
                    "Workflow coordination"
                ],
                "subagent_keywords": [
                    "coordinate", "orchestrate", "workflow", "pipeline",
                    "branching", "conditional", "decision points"
                ],
                "score_if_yes": -1,
                "score_if_no": +1
            },
            "isolated_context": {
                "question": "Does it need isolated context?",
                "examples": [
                    "Long debugging session",
                    "Extensive exploration",
                    "Separate conversation thread"
                ],
                "subagent_keywords": [
                    "isolated", "separate", "context", "independent",
                    "debugging", "exploration", "extensive"
                ],
                "score_if_yes": -1,
                "score_if_no": +1
            },
            "clutter_chat": {
                "question": "Would it clutter main chat with intermediate steps?",
                "examples": [
                    "Security scan with 50+ findings",
                    "Comprehensive code analysis",
                    "Verbose intermediate output"
                ],
                "subagent_keywords": [
                    "verbose", "detailed", "comprehensive", "extensive",
                    "many", "multiple outputs", "clutter"
                ],
                "score_if_yes": -1,
                "score_if_no": +1
            }
        }
    
    def analyze_from_answers(self, answers: Dict[str, bool]) -> Dict:
        """
        Analyze use case from pre-provided answers.
        
        Args:
            answers: Dict with Q1-Q8 answers as boolean values
            
        Returns:
            Dict with status, recommendation, score, confidence, reasoning
            
        This is the PRIMARY mode when Claude has extracted clear answers.
        """
        # Validate input
        required_keys = list(self.questions.keys())
        missing = [k for k in required_keys if k not in answers]
        
        if missing:
            return {
                "status": "error",
                "error_type": "InvalidInput",
                "message": f"Missing required answers: {', '.join(missing)}",
                "help": "Provide complete answers for all 8 questions",
                "required_keys": required_keys
            }
        
        # Validate types
        invalid_types = []
        for key, value in answers.items():
            if not isinstance(value, bool):
                invalid_types.append(f"{key}={type(value).__name__}")
        
        if invalid_types:
            return {
                "status": "error",
                "error_type": "InvalidType",
                "message": f"All answers must be boolean: {', '.join(invalid_types)}",
                "help": "Use true/false for all answer values"
            }
        
        # Store answers and calculate scores
        self.answers = answers
        self._calculate_scores()
        
        return self._build_recommendation()
    
    def analyze_from_description(self, description: str) -> Dict:
        """
        Infer answers from natural language description.
        
        Args:
            description: User's use case description
            
        Returns:
            Dict with recommendation + inference metadata
            
        FALLBACK mode when Claude doesn't have clear answers.
        Lower confidence due to inference.
        """
        if not description or len(description.strip()) < 3:
            return {
                "status": "error",
                "error_type": "InvalidInput",
                "message": "Description too short or empty",
                "help": "Provide detailed use case description (at least 3 characters)"
            }
        
        # Infer answers from keywords
        inference_result = self._infer_answers_from_keywords(description)
        
        # Analyze with inferred answers
        result = self.analyze_from_answers(inference_result['answers'])
        
        if result['status'] == 'success':
            # Add inference metadata
            result['inference_mode'] = True
            result['inference_note'] = "Answers inferred from keywords. For more accurate results, provide explicit answers."
            result['detected_keywords'] = inference_result['detected']
            
            # Reduce confidence for inference
            result['confidence'] = round(result['confidence'] * 0.85, 2)
        
        return result
    
    def show_criteria(self) -> Dict:
        """
        Return decision criteria for Claude's reference.
        
        Used when Claude needs to explain the decision framework to users.
        
        Returns:
            Dict with all questions and score interpretation table
        """
        criteria = {}
        for q_id, q_data in self.questions.items():
            criteria[q_id] = {
                "question": q_data["question"],
                "examples": q_data["examples"],
                "scoring": {
                    "yes": q_data["score_if_yes"],
                    "no": q_data["score_if_no"]
                }
            }
        
        return {
            "status": "success",
            "criteria": criteria,
            "score_interpretation": {
                "+6 to +8": {
                    "recommendation": "Strong Skill",
                    "confidence": "90-95%",
                    "characteristics": "Utility functions, procedures, templates",
                    "token_overhead": "30-50 tokens"
                },
                "+3 to +5": {
                    "recommendation": "Moderate Skill",
                    "confidence": "75-85%",
                    "characteristics": "Mostly procedural with some logic",
                    "token_overhead": "Low overhead"
                },
                "-1 to +2": {
                    "recommendation": "Hybrid Approach",
                    "confidence": "60-70%",
                    "characteristics": "Mix of utility and orchestration",
                    "token_overhead": "Optimized balance"
                },
                "-3 to -5": {
                    "recommendation": "Moderate Subagent",
                    "confidence": "75-85%",
                    "characteristics": "Multi-step workflows with some complexity",
                    "token_overhead": "15Ã— multiplier"
                },
                "-6 to -8": {
                    "recommendation": "Strong Subagent",
                    "confidence": "90-95%",
                    "characteristics": "Complex workflows, specialized expertise",
                    "token_overhead": "High (justified by complexity)"
                }
            },
            "references": {
                "conceptual": "File 02: Skills vs Subagents comparison",
                "decision_tree": "File 03: Complete decision tree details",
                "costs": "File 05: Token economics analysis"
            }
        }
    
    def _calculate_scores(self):
        """
        Calculate score based on answers.
        
        Score range: -8 (Strong Subagent) to +8 (Strong Skill)
        Uses exact logic from File 03.
        """
        self.score = 0
        self.reasoning = []
        
        for q_id, q_data in self.questions.items():
            answer = self.answers[q_id]
            
            if answer:
                # YES answer
                score_change = q_data["score_if_yes"]
                direction = "favors Skill" if score_change > 0 else "favors Subagent"
                self.reasoning.append(
                    f"{q_data['question']} â†’ YES ({direction})"
                )
            else:
                # NO answer
                score_change = q_data["score_if_no"]
                if score_change != 0:
                    direction = "favors Skill" if score_change > 0 else "favors Subagent"
                    self.reasoning.append(
                        f"{q_data['question']} â†’ NO ({direction})"
                    )
                else:
                    self.reasoning.append(
                        f"{q_data['question']} â†’ NO (neutral)"
                    )
            
            self.score += score_change
    
    def _build_recommendation(self) -> Dict:
        """
        Generate final recommendation with confidence.
        
        Returns:
            Structured JSON for Claude to parse and explain
        """
        # Interpret score (exact File 03 logic)
        if self.score >= 6:
            recommendation = "Strong Skill"
            confidence = 0.90 + (self.score - 6) * 0.025  # 90-95%
        elif self.score >= 3:
            recommendation = "Moderate Skill"
            confidence = 0.75 + (self.score - 3) * 0.033  # 75-85%
        elif self.score >= -1:
            recommendation = "Hybrid Approach"
            confidence = 0.60 + (self.score + 1) * 0.033  # 60-70%
        elif self.score >= -5:
            recommendation = "Moderate Subagent"
            confidence = 0.75 + (abs(self.score) - 3) * 0.05  # 75-85%
        else:
            recommendation = "Strong Subagent"
            confidence = 0.90 + (abs(self.score) - 6) * 0.025  # 90-95%
        
        return {
            "status": "success",
            "recommendation": recommendation,
            "score": self.score,
            "confidence": round(confidence, 2),
            "reasoning": self.reasoning,
            "token_analysis": self._calculate_token_impact(),
            "pattern_suggestions": self._generate_pattern_suggestions(),
            "references": {
                "conceptual": "File 02: Skills vs Subagents comparison",
                "decision_tree": "File 03: Complete decision tree",
                "costs": "File 05: Token economics"
            }
        }
    
    def _calculate_token_impact(self) -> Dict:
        """
        Calculate estimated token costs for each approach.
        
        Based on File 05 research findings:
        - Skills: ~50 token overhead (progressive disclosure)
        - Subagents: 15Ã— multiplier vs Skills
        
        Returns:
            Dict with token cost estimates and recommendations
        """
        # Base estimates from File 05
        if self.score >= 3:
            # Skill-leaning recommendation
            skill_cost = 500  # Typical skill invocation
            subagent_cost = skill_cost * 15
            note = "Skill approach significantly more token-efficient"
        elif self.score <= -3:
            # Subagent-leaning recommendation
            subagent_cost = 7500  # Complex workflow
            skill_cost = subagent_cost // 15
            note = "High token cost justified for complex workflows"
        else:
            # Hybrid zone
            skill_cost = 500
            subagent_cost = 7500
            note = "Consider hybrid: balance efficiency and capability"
        
        return {
            "skill_approach_tokens": skill_cost,
            "subagent_approach_tokens": subagent_cost,
            "cost_multiplier": round(subagent_cost / skill_cost, 1),
            "recommendation_note": note
        }
    
    def _generate_pattern_suggestions(self) -> List[str]:
        """
        Generate actionable pattern suggestions.
        
        Based on File 04 (Hybrid Patterns) and score interpretation.
        
        Returns:
            List of actionable next-step suggestions
        """
        suggestions = []
        
        if self.score >= 6:
            # Strong Skill
            suggestions.append("Implement as pure Skill")
            suggestions.append("Focus on clear YAML description for auto-discovery")
            suggestions.append("Keep SKILL.md under 500 lines for efficiency")
        
        elif self.score >= 3:
            # Moderate Skill
            suggestions.append("Implement as Skill")
            suggestions.append("Consider extracting complex logic to scripts/")
            suggestions.append("Use progressive disclosure for larger content")
        
        elif -1 <= self.score <= 2:
            # Hybrid Zone
            suggestions.append("Consider Hybrid: Subagent orchestration + Skill utilities")
            suggestions.append("Extract reusable parts to Skills")
            suggestions.append("Use Subagent for main workflow coordination")
            suggestions.append("See File 04 for hybrid pattern examples")
        
        elif self.score >= -5:
            # Moderate Subagent
            suggestions.append("Implement as Subagent")
            suggestions.append("Consider if any utilities can become Skills")
            suggestions.append("Use isolated context for clean reasoning")
        
        else:
            # Strong Subagent
            suggestions.append("Implement as Subagent")
            suggestions.append("Full isolated context and specialized personality needed")
            suggestions.append("High token cost justified by complexity and value")
        
        return suggestions
    
    def _infer_answers_from_keywords(self, text: str) -> Dict:
        """
        Keyword-based answer inference from description.
        
        Args:
            text: Natural language use case description
            
        Returns:
            Dict with inferred answers and detected keywords
        """
        text_lower = text.lower()
        detected = {}
        inferred_answers = {}
        
        for q_id, q_data in self.questions.items():
            # Check for skill-favoring keywords
            skill_keywords = q_data.get("skill_keywords", [])
            skill_matches = [k for k in skill_keywords if k in text_lower]
            
            # Check for subagent-favoring keywords
            subagent_keywords = q_data.get("subagent_keywords", [])
            subagent_matches = [k for k in subagent_keywords if k in text_lower]
            
            detected[q_id] = {
                "skill_keywords": skill_matches,
                "subagent_keywords": subagent_matches
            }
            
            # Infer answer based on keyword presence
            if skill_matches and not subagent_matches:
                inferred_answers[q_id] = True
            elif subagent_matches and not skill_matches:
                inferred_answers[q_id] = False
            elif len(skill_matches) > len(subagent_matches):
                inferred_answers[q_id] = True
            elif len(subagent_matches) > len(skill_matches):
                inferred_answers[q_id] = False
            else:
                # Default based on question type
                # Questions that favor Skills by default: utility, reusable, missing_knowledge
                default_yes = q_id in ["utility_task", "reusable", "missing_knowledge"]
                inferred_answers[q_id] = default_yes
        
        return {
            "answers": inferred_answers,
            "detected": detected
        }


def main():
    """CLI entry point for agent-layer usage."""
    parser = argparse.ArgumentParser(
        description="Decision helper for Skills vs Subagents (Agent-Layer Tool)",
        epilog="References: Files 02 (comparison), 03 (decision tree), 05 (token economics)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Mutually exclusive modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    
    mode_group.add_argument(
        '--answers',
        type=str,
        metavar='FILE',
        help='JSON file with pre-answered questions (Mode 1 - Preferred)'
    )
    
    mode_group.add_argument(
        '--analyze',
        type=str,
        metavar='DESCRIPTION',
        help='Analyze use case from description (Mode 2 - Fallback)'
    )
    
    mode_group.add_argument(
        '--show-criteria',
        action='store_true',
        help='Show decision criteria (Mode 3 - Reference)'
    )

    # Add --format argument (JSON is default for agent-layer tool)
    add_format_argument(parser, default='json')

    args = parser.parse_args()
    
    helper = DecisionHelper()
    result = None
    
    try:
        if args.answers:
            # Mode 1: Pre-answered questions
            answers_path = Path(args.answers)
            
            if not answers_path.exists():
                result = {
                    "status": "error",
                    "error_type": "FileNotFound",
                    "message": f"Answers file not found: {args.answers}",
                    "help": "Check file path or use --analyze mode"
                }
            else:
                with open(answers_path, 'r') as f:
                    answers = json.load(f)
                result = helper.analyze_from_answers(answers)
        
        elif args.analyze:
            # Mode 2: Keyword-based inference
            result = helper.analyze_from_description(args.analyze)
        
        elif args.show_criteria:
            # Mode 3: Show criteria
            result = helper.show_criteria()
    
    except json.JSONDecodeError as e:
        result = {
            "status": "error",
            "error_type": "InvalidJSON",
            "message": f"Invalid JSON in answers file: {str(e)}",
            "help": "Ensure answers.json contains valid JSON"
        }
    
    except Exception as e:
        result = {
            "status": "error",
            "error_type": "UnexpectedError",
            "message": str(e),
            "help": "Contact support if this persists"
        }
    
    # Output based on format
    if args.format == 'json':
        # JSON output (default for agent-layer)
        print(json.dumps(result, indent=2))
    else:
        # Text output (for debugging/human reading)
        print_text_format(result)

    # Exit code based on status
    return 0 if result and result.get('status') == 'success' else 1


def print_text_format(result: Dict):
    """Format result as human-readable text."""
    if result.get('status') == 'error':
        print(f"\n❌ Error: {result.get('error_type')}")
        print(f"   {result.get('message')}")
        if result.get('help'):
            print(f"\n💡 Help: {result.get('help')}")
        return

    # Success - show recommendation
    print(f"\n{'='*70}")
    print(f"Decision: {result.get('recommendation')}")
    print(f"{'='*70}\n")

    print(f"Score: {result.get('score')} (Range: -8 to +8)")
    print(f"Confidence: {result.get('confidence', 0)*100:.0f}%\n")

    if result.get('reasoning'):
        print("Reasoning:")
        for i, reason in enumerate(result.get('reasoning', []), 1):
            print(f"  {i}. {reason}")
        print()

    if result.get('token_analysis'):
        ta = result['token_analysis']
        print("Token Impact:")
        print(f"  Skill approach: ~{ta.get('skill_approach_tokens')} tokens")
        print(f"  Subagent approach: ~{ta.get('subagent_approach_tokens')} tokens")
        print(f"  Cost multiplier: {ta.get('cost_multiplier')}x")
        print(f"  Note: {ta.get('recommendation_note')}\n")

    if result.get('pattern_suggestions'):
        print("Next Steps:")
        for i, suggestion in enumerate(result.get('pattern_suggestions', []), 1):
            print(f"  {i}. {suggestion}")
        print()

    if result.get('references'):
        print("References:")
        for key, val in result.get('references', {}).items():
            print(f"  - {val}")
        print()


if __name__ == "__main__":
    sys.exit(main())
