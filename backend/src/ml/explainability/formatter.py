from typing import Any


class ExplanationFormatter:
    @staticmethod
    def format_for_api(shap_result: list[dict[str, Any]]) -> str:
        if not shap_result:
            return "No explanation available."

        parts = ["Risk is evaluated based on the following key factors:"]

        for i, item in enumerate(shap_result, 1):
            feat = item["feature"].replace("_", " ")
            direction = "increases" if item["direction"] == "increases_risk" else "decreases"
            parts.append(f"({i}) Your {feat} significantly {direction} the risk profile.")

        return " ".join(parts)

    @staticmethod
    def format_for_audit(
        shap_result: list[dict[str, Any]], full_feature_vector: dict[str, float]
    ) -> dict[str, Any]:
        return {"top_drivers": shap_result, "all_features": full_feature_vector}
