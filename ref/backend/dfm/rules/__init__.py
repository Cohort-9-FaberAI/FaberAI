"""Rule registry — maps a manufacturing process to its evaluator classes.

Adding a process (CNC, sheet metal) means: create ``rules/<process>/`` with one
module per rule, add the process to ``ProcessType``, and register the list here.
The engine, scoring and AI layers need no changes.
"""

from typing import Dict, List, Type

from ..base import RuleEvaluator
from ..models import ProcessType
from .injection_molding import INJECTION_MOLDING_RULES
from .printing import PRINTING_RULES

RULES_BY_PROCESS: Dict[ProcessType, List[Type[RuleEvaluator]]] = {
    ProcessType.injection_molding: INJECTION_MOLDING_RULES,
    ProcessType.printing: PRINTING_RULES,
}


def rules_for(process: ProcessType) -> List[Type[RuleEvaluator]]:
    return RULES_BY_PROCESS.get(process, [])


__all__ = ["RULES_BY_PROCESS", "rules_for", "INJECTION_MOLDING_RULES", "PRINTING_RULES"]
