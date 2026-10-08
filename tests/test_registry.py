import os
import tempfile
import core.registry

def test_metric_registry():
    with tempfile.TemporaryDirectory() as tmpdir:
        original_file = core.registry.REGISTRY_FILE
        core.registry.REGISTRY_FILE = os.path.join(tmpdir, "metrics.json")
        
        # Test empty
        metrics = core.registry.load_metrics()
        assert metrics == {}
        
        # Test save
        core.registry.save_metric("Test Metric", "This is a test")
        metrics = core.registry.load_metrics()
        assert metrics["Test Metric"] == "This is a test"
        
        # Test prompt format
        prompt = core.registry.get_metrics_prompt()
        assert "BUSINESS METRIC DEFINITIONS" in prompt
        assert "Test Metric" in prompt
        
        # Test delete
        core.registry.delete_metric("Test Metric")
        assert core.registry.load_metrics() == {}
        
        core.registry.REGISTRY_FILE = original_file
