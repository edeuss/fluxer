#!/usr/bin/env python3
# Keep in sync with fluxerapp/dart_sdk generate.sh patch logic.
import json
import sys
from pathlib import Path

SPEC_PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "openapi.json")

with SPEC_PATH.open() as f:
    spec = json.load(f)

schemas = spec.get("components", {}).get("schemas", {})
patches = 0


def add_field(schema_name, field_name, field_def):
    global patches
    schema = schemas.get(schema_name, {})
    props = schema.get("properties", {})
    if field_name not in props:
        props[field_name] = field_def
        patches += 1
        print(f"  Added {schema_name}.{field_name}")


def add_inline_field(schema_name, inline_prop, field_name, field_def):
    global patches
    schema = schemas.get(schema_name, {})
    inline = schema.get("properties", {}).get(inline_prop, {})
    props = inline.get("properties", {})
    if field_name not in props:
        props[field_name] = field_def
        patches += 1
        print(f"  Added {schema_name}.{inline_prop}.{field_name}")


def make_optional(schema_name, inline_prop, field_name):
    global patches
    schema = schemas.get(schema_name, {})
    inline = schema.get("properties", {}).get(inline_prop, {})
    req = inline.get("required", [])
    if field_name in req:
        req.remove(field_name)
        patches += 1
        print(f"  Made {schema_name}.{inline_prop}.{field_name} optional")


# --- WellKnownFluxerResponse patches ---

make_optional("WellKnownFluxerResponse", "features", "manual_review_enabled")

add_inline_field(
    "WellKnownFluxerResponse",
    "features",
    "presigned_attachment_uploads",
    {
        "type": "boolean",
        "description": "Whether presigned attachment uploads are enabled",
    },
)

add_field(
    "WellKnownFluxerResponse",
    "gateway",
    {
        "type": "object",
        "description": "Gateway session retry configuration",
        "properties": {
            "session_retry_min_ms": {
                "type": "integer",
                "description": "Minimum retry delay in milliseconds",
            },
            "session_retry_max_ms": {
                "type": "integer",
                "description": "Maximum retry delay in milliseconds",
            },
            "session_retry_jitter_ms": {
                "type": "integer",
                "description": "Jitter added to retry delay in milliseconds",
            },
        },
        "required": [
            "session_retry_min_ms",
            "session_retry_max_ms",
            "session_retry_jitter_ms",
        ],
    },
)

# --- UserPrivateResponse patches ---

add_field(
    "UserPrivateResponse",
    "premium_out_of_band_trial_ends_at",
    {
        "anyOf": [{"type": "string", "format": "date-time"}, {"type": "null"}],
        "description": "When the out-of-band premium trial ends",
    },
)
add_field(
    "UserPrivateResponse",
    "premium_discriminator",
    {
        "type": "boolean",
        "description": "Whether the user has a premium discriminator",
    },
)
add_field(
    "UserPrivateResponse",
    "terms_agreed_at",
    {
        "anyOf": [{"type": "string", "format": "date-time"}, {"type": "null"}],
        "description": "When the user agreed to terms of service",
    },
)
add_field(
    "UserPrivateResponse",
    "privacy_agreed_at",
    {
        "anyOf": [{"type": "string", "format": "date-time"}, {"type": "null"}],
        "description": "When the user agreed to the privacy policy",
    },
)

# --- UserSettingsResponse patches ---

add_field(
    "UserSettingsResponse",
    "sensitive_content_friend_dm_filter",
    {
        "type": "integer",
        "description": "Sensitive content filter level for friend DMs",
    },
)
add_field(
    "UserSettingsResponse",
    "sensitive_content_non_friend_dm_filter",
    {
        "type": "integer",
        "description": "Sensitive content filter level for non-friend DMs",
    },
)
add_field(
    "UserSettingsResponse",
    "sensitive_content_guild_filter",
    {
        "type": "integer",
        "description": "Sensitive content filter level for guild messages",
    },
)

# --- MessageReactionResponse patches ---

reaction = schemas.get("MessageReactionResponse", {})
me_prop = reaction.get("properties", {}).get("me")
if me_prop and "anyOf" in me_prop:
    desc = me_prop.get("description", "")
    reaction["properties"]["me"] = {
        "anyOf": [{"type": "boolean"}, {"type": "null"}],
        "description": desc,
    }
    patches += 1
    print("  Simplified MessageReactionResponse.me to nullable boolean")

with SPEC_PATH.open("w") as f:
    json.dump(spec, f, separators=(",", ":"))

print(f"Applied {patches} patch(es)")
