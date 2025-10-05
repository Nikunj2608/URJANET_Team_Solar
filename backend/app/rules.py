from dataclasses import dataclass
from typing import Iterable


@dataclass
class Rule:
    field: str
    op: str  # 'lt' or 'gt'
    threshold: float
    severity: str
    type: str
    message: str

    def check(self, payload: dict):
        if self.field not in payload:
            return None
        value = float(payload[self.field])
        if self.op == 'lt' and value < self.threshold:
            return (value, self.threshold)
        if self.op == 'gt' and value > self.threshold:
            return (value, self.threshold)
        return None


RULES: list[Rule] = [
    Rule(field="soc", op="lt", threshold=20.0, severity="WARN", type="SOC_LOW", message="State of Charge below 20%"),
    Rule(field="voltage", op="gt", threshold=250.0, severity="HIGH", type="VOLTAGE_HIGH", message="Voltage exceeds 250V"),
    Rule(field="temperature", op="gt", threshold=60.0, severity="HIGH", type="TEMP_HIGH", message="Temperature above 60C"),
]


def evaluate(payload: dict) -> Iterable[dict]:
    for rule in RULES:
        res = rule.check(payload)
        if res:
            value, threshold = res
            yield {
                "type_": rule.type,  # align with crud.create_alert(type_="...")
                "severity": rule.severity,
                "message": rule.message,
                "value": value,
                "threshold": threshold,
            }
