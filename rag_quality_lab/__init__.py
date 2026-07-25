"""Public evaluation toolkit for the AI CRM + SED showcase."""

from .metrics import answer_metrics, classification_metrics, contract_metrics, retrieval_metrics

__all__ = ["answer_metrics", "classification_metrics", "contract_metrics", "retrieval_metrics"]
__version__ = "0.1.0"
