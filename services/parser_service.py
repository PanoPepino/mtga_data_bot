"""Re-exports everything from utils/parse_and_check.py under the services namespace.

Keeping utils/parse_and_check.py in place avoids breaking any existing imports
while making the services/ layer the canonical home for domain logic going forward.
Once all callers are updated to import from services.parser_service, the original
file can be removed.
"""
from utils.parse_and_check import (  # noqa: F401  (re-export)
    parse_runs,
    summarise_run_record,
    validate_runs_metagame,
    validate_run_ladder,
    parse_match_line,
    get_placeholder,
)
