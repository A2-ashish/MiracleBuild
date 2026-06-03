"""Failure handler — pre-processes user prompts to handle vagueness,
conflicts, and under-specification before they enter the pipeline.
"""
from __future__ import annotations

import logging
import re

from app.schemas.intent import Assumption

logger = logging.getLogger(__name__)

# Domain-specific defaults used to enrich under-specified prompts
_DOMAIN_DEFAULTS: dict[str, str] = {
    "ecommerce": (
        "Include product catalog, shopping cart, checkout, order management, "
        "customer accounts, and payment processing."
    ),
    "crm": (
        "Include contacts, companies, deals pipeline, activity tracking, "
        "and reporting dashboards."
    ),
    "education": (
        "Include courses, lessons, student enrollment, progress tracking, "
        "quizzes, and instructor dashboards."
    ),
    "healthcare": (
        "Include patient records, appointments, prescriptions, doctor "
        "profiles, and medical history."
    ),
    "saas": (
        "Include multi-tenancy, subscription plans, billing, user "
        "management, and admin dashboard."
    ),
    "social": (
        "Include user profiles, posts, comments, likes, followers, "
        "notifications, and messaging."
    ),
    "marketplace": (
        "Include listings, buyer/seller profiles, orders, reviews, "
        "search, and payment processing."
    ),
    "fintech": (
        "Include accounts, transactions, transfers, statements, "
        "KYC verification, and compliance reporting."
    ),
    "productivity": (
        "Include projects, tasks, boards, timelines, team members, "
        "and progress dashboards."
    ),
    "logistics": (
        "Include shipments, tracking, warehouses, inventory, "
        "routes, and delivery management."
    ),
}


class FailureHandler:
    """Pre-processes prompts to compensate for vagueness, conflict, or brevity."""

    def analyze_prompt(
        self, prompt: str
    ) -> tuple[str, list[Assumption]]:
        """Analyze and enhance the user prompt.

        Returns:
            A tuple of ``(enhanced_prompt, assumptions)`` where
            *assumptions* lists every guess the system made.
        """
        assumptions: list[Assumption] = []
        enhanced = prompt.strip()

        # 1. Too short — expand generically
        if len(enhanced.split()) < 5:
            enhanced, short_assumptions = self._handle_too_short(enhanced)
            assumptions.extend(short_assumptions)

        # 2. Detect conflicting requirements
        enhanced, conflict_assumptions = self._handle_conflicts(enhanced)
        assumptions.extend(conflict_assumptions)

        # 3. Domain enrichment
        enhanced, domain_assumptions = self._handle_domain_enrichment(enhanced)
        assumptions.extend(domain_assumptions)

        if assumptions:
            logger.info(
                "FailureHandler made %d assumptions for prompt: %s…",
                len(assumptions),
                prompt[:60],
            )

        return enhanced, assumptions

    # ------------------------------------------------------------------
    # Sub-handlers
    # ------------------------------------------------------------------

    @staticmethod
    def _handle_too_short(
        prompt: str,
    ) -> tuple[str, list[Assumption]]:
        """Expand an extremely short prompt with generic defaults."""
        assumptions = [
            Assumption(
                description="Prompt was very short — expanded with generic web app defaults",
                reason=f"Only {len(prompt.split())} words provided",
                impact="high",
            ),
        ]
        enhanced = (
            f"{prompt}\n\n"
            "Additional context (auto-generated): The application should have "
            "user authentication (email + password), at least two roles (admin "
            "and regular user), a relational database with proper foreign keys, "
            "a modern responsive dashboard UI with dark theme, CRUD operations "
            "for all entities, search functionality, and export capability."
        )
        return enhanced, assumptions

    @staticmethod
    def _handle_conflicts(
        prompt: str,
    ) -> tuple[str, list[Assumption]]:
        """Detect and resolve contradictory requirements."""
        assumptions: list[Assumption] = []
        lower = prompt.lower()

        # Example: "no authentication" + "admin panel"
        no_auth = "no auth" in lower or "without auth" in lower or "no login" in lower
        needs_admin = "admin" in lower

        if no_auth and needs_admin:
            prompt = prompt + (
                "\n\nNote: Admin functionality requires authentication. "
                "Authentication will be included for admin features only."
            )
            assumptions.append(
                Assumption(
                    description="Conflict: 'no auth' with 'admin' — resolved by enabling auth for admin only",
                    reason="Admin features require authentication",
                    impact="high",
                )
            )

        # "free" + "payment"
        is_free = "free" in lower and "freemium" not in lower
        has_payment = "payment" in lower or "billing" in lower or "subscription" in lower

        if is_free and has_payment:
            prompt = prompt + (
                "\n\nNote: Interpreted as a freemium model — basic features "
                "are free, premium features require payment."
            )
            assumptions.append(
                Assumption(
                    description="Conflict: 'free' with 'payment' — resolved as freemium model",
                    reason="Both free and payment features requested",
                    impact="medium",
                )
            )

        return prompt, assumptions

    @staticmethod
    def _handle_domain_enrichment(
        prompt: str,
    ) -> tuple[str, list[Assumption]]:
        """Enrich the prompt with domain-specific defaults if a known domain is detected."""
        lower = prompt.lower()
        assumptions: list[Assumption] = []

        for domain, defaults in _DOMAIN_DEFAULTS.items():
            if domain in lower:
                prompt = prompt + f"\n\nDomain defaults ({domain}): {defaults}"
                assumptions.append(
                    Assumption(
                        description=f"Enriched with {domain} domain defaults",
                        reason=f"Detected '{domain}' domain in prompt",
                        impact="low",
                    )
                )
                break  # only apply one domain

        return prompt, assumptions
