from typing import Dict, Text, Any
from rasa_addons.core.actions.slot_rule_validator import validate_with_rule


class RequiredSlotsGraphParser:
    def __init__(self, required_slots_graph: Dict[Text, Any]) -> None:
        self.start = None
        self.nodes = {}
        for node in required_slots_graph.get("nodes", []):
            if node.get("type") == "start":
                self.start = node.get("id")
                continue
            self.nodes[node.get("id")] = node.get("slotName")
        self.edges = {}
        for edge in required_slots_graph.get("edges", []):
            source = edge.get("source")
            self.edges[source] = [*self.edges.get(source, []), edge]

    def get_required_slots(self, tracker, start=None):
        required_slots = []
        current_source = start or self.start
        current_edges = self.edges.get(current_source, [])
        for edge in sorted(current_edges, key=lambda e: e.get("condition") is None):
            target, condition = edge.get("target"), edge.get("condition")
            if self.check_condition(tracker, condition):
                required_slots.append(self.nodes.get(target))
                required_slots += self.get_required_slots(tracker, start=target)
                break # use first matching condition, that's it
            else:
                continue
        return required_slots

    def check_condition(self, tracker, condition):
        if condition is None:
            return True
        props = condition.get("properties", {})
        children = condition.get("children1", {}).values()
        if condition.get("type") == "rule":
            return self.check_atomic_condition(tracker, **props)
        conjunction_operator = any if props.get("conjunction") == "OR" else all
        polarity = (lambda p: not p) if props.get("not") else (lambda p: p)
        return polarity(
            conjunction_operator(
                self.check_condition(tracker, child) for child in children
            )
        )

    def check_atomic_condition(self, tracker, field, operator, value, **rest):
        slot = tracker.slots.get(field)
        return validate_with_rule(
            slot.value if slot else None,
            {
                "operator": operator,
                "comparatum": [*value, None][0] # value is always a singleton list
            },
        )
