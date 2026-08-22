"""PHANTOM modular AI analytics package (compute plane).

Heavy inference must not run inside FastAPI HTTP handlers. Workers implement
InferenceEngine / DetectionEngine / OCRProcessor and publish normalized results
to the PHANTOM API (control/data plane).
"""
