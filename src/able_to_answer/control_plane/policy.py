"""Policy evaluation for the Control Plane.

Built-in profiles
-----------------
default     Require human approval for all side-effect actions; allow others.
strict      Deny all side-effect actions outright.
permissive  Allow all actions without approval.
"""
from __future__ import annotations

from able_to_answer.control_plane.models import ActionEnvelope, PolicyDecision, PolicyProfile

# Actions that have side-effects outside the sandbox (must be gated).
SIDE_EFFECT_ACTIONS: frozenset[str] = frozenset(
    {"GIT_PUSH", "DEPLOY", "SECRET_ACCESS", "OUTBOUND_NETWORK", "PUBLISH_DOCS"}
)

BUILTIN_PROFILES: dict[str, PolicyProfile] = {
    "default": PolicyProfile(
        profile_id="default",
        description=(
            "Require human approval for side-effect actions; allow all others."
        ),
        side_effect_actions=sorted(SIDE_EFFECT_ACTIONS),
        deny_action_types=[],
        require_approval_for=sorted(SIDE_EFFECT_ACTIONS),
        default_decision=PolicyDecision.allow,
    ),
    "strict": PolicyProfile(
        profile_id="strict",
        description="Deny all side-effect actions; allow all others.",
        side_effect_actions=sorted(SIDE_EFFECT_ACTIONS),
        deny_action_types=sorted(SIDE_EFFECT_ACTIONS),
        require_approval_for=[],
        default_decision=PolicyDecision.allow,
    ),
    "permissive": PolicyProfile(
        profile_id="permissive",
        description="Allow all actions without requiring approval.",
        side_effect_actions=sorted(SIDE_EFFECT_ACTIONS),
        deny_action_types=[],
        require_approval_for=[],
        default_decision=PolicyDecision.allow,
    ),
}


def get_policy_profile(profile_id: str) -> PolicyProfile | None:
    """Return a built-in policy profile by ID, or None if unknown."""
    return BUILTIN_PROFILES.get(profile_id)


def evaluate_action(envelope: ActionEnvelope) -> tuple[PolicyDecision, str]:
    """Evaluate an action envelope and return *(decision, reason)*.

    Decision precedence:
    1. Unknown profile → deny.
    2. Action in deny_action_types → deny.
    3. Action in require_approval_for → pending_approval.
    4. Otherwise → profile's default_decision.
    """
    profile = BUILTIN_PROFILES.get(envelope.policy_profile_id)
    if profile is None:
        return (
            PolicyDecision.deny,
            f"Unknown policy profile '{envelope.policy_profile_id}'; defaulting to deny.",
        )

    action_type = envelope.requested_action.type

    if action_type in profile.deny_action_types:
        return (
            PolicyDecision.deny,
            (
                f"Action '{action_type}' is explicitly denied "
                f"by profile '{profile.profile_id}'."
            ),
        )

    if action_type in profile.require_approval_for:
        return (
            PolicyDecision.pending_approval,
            (
                f"Action '{action_type}' requires human approval "
                f"per profile '{profile.profile_id}'."
            ),
        )

    return (
        profile.default_decision,
        f"Action '{action_type}' allowed by profile '{profile.profile_id}'.",
    )
