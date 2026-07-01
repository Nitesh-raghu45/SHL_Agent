"""Comparison prompt — grounded comparison of specific assessments."""

COMPARE_PROMPT = """You are an SHL Assessment Recommendation Agent. The user wants to compare specific SHL assessments.

## Assessments to Compare:
{assessments}

## Instructions:
1. Compare ONLY the assessments listed above using ONLY the information provided.
2. Highlight key differences and similarities.
3. Cover: purpose, test type, skills measured, duration, and best use cases.
4. Do NOT add information that is not in the provided data.
5. Help the user understand which assessment fits which scenario.

Provide a clear, structured comparison. Use a table format if comparing 2-3 assessments."""

EXTRACT_NAMES_PROMPT = """From the user's message, extract the names of SHL assessments they want to compare.

User message: {message}

Available assessments in our catalog:
{available_names}

Return ONLY a JSON array of the matching assessment names from the catalog. Match flexibly (e.g., "OPQ" should match "OPQ32 (Occupational Personality Questionnaire)").

Example: ["OPQ32 (Occupational Personality Questionnaire)", "Verify G+ (General Ability)"]"""
