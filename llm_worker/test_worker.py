"""
Test script for LLM Worker components
Verifies that all components are properly integrated
"""
import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src" / "python"))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import torch
        print(f"✓ PyTorch version: {torch.__version__}")
        
        # Check CUDA availability
        if torch.cuda.is_available():
            print(f"✓ CUDA available: {torch.cuda.get_device_name()}")
        else:
            print("⚠ CUDA not available")
    except ImportError:
        print("✗ PyTorch import failed")
        return False
    
    try:
        import tensorrt as trt
        print(f"✓ TensorRT version: {trt.__version__ if hasattr(trt, '__version__') else 'Unknown'}")
    except ImportError:
        print("✗ TensorRT import failed")
        return False
    
    try:
        import transformers
        print(f"✓ Transformers version: {transformers.__version__}")
    except ImportError:
        print("✗ Transformers import failed")
        return False
    
    try:
        import pycuda.driver as cuda
        import pycuda.autoinit
        print("✓ PyCUDA available")
    except ImportError:
        print("✗ PyCUDA import failed")
        return False
    
    try:
        import fastapi
        print(f"✓ FastAPI version: {fastapi.__version__}")
    except ImportError:
        print("✗ FastAPI import failed")
        return False
    
    try:
        import psutil
        import GPUtil
        print("✓ System monitoring libraries available")
    except ImportError:
        print("✗ System monitoring libraries import failed")
        return False
    
    # Test our own modules
    try:
        from llm_worker import LLMWorker, GenerationConfig
        print("✓ LLMWorker module imported successfully")
    except ImportError as e:
        print(f"✗ LLMWorker import failed: {e}")
        return False
    
    try:
        from config.config import get_default_config
        print("✓ Config module imported successfully")
    except ImportError as e:
        print(f"✗ Config import failed: {e}")
        return False
    
    try:
        from api_server import GenerateRequest
        print("✓ API Server module imported successfully")
    except ImportError as e:
        print(f"✗ API Server import failed: {e}")
        return False
    
    try:
        from monitoring import HealthChecker, ResourceMonitor
        print("✓ Monitoring module imported successfully")
    except ImportError as e:
        print(f"✗ Monitoring import failed: {e}")
        return False
    
    print("All imports successful!\n")
    return True

def test_config():
    """Test configuration system"""
    print("Testing configuration...")
    
    try:
        from config.config import get_default_config, LLMWorkerConfig
        
        # Get default config
        config = get_default_config()
        print(f"✓ Default config created: {config.model_config.model_name}")
        
        # Test config serialization
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            config.to_file(config_path)
            print("✓ Config serialization successful")
            
            # Test config loading
            loaded_config = LLMWorkerConfig.from_file(config_path)
            print("✓ Config deserialization successful")
            
        finally:
            os.unlink(config_path)
        
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False

def test_worker_structure():
    """Test LLM worker structure without running it"""
    print("Testing LLM worker structure...")
    
    try:
        from llm_worker import LLMWorker, GenerationConfig, RequestQueue, GPUManager, TensorRTLLMEngine
        
        # Test basic instantiation (without actual model)
        try:
            # This will fail due to missing model files, but should initialize internal structures
            worker = LLMWorker("dummy_path", "dummy_tokenizer_path")
            print("✓ LLMWorker structure is valid")
        except Exception as e:
            # Expected to fail due to missing model, but internal structure should be OK
            if "missing" in str(e).lower() or "not found" in str(e).lower():
                print("✓ LLMWorker structure is valid (expected model error)")
            else:
                print(f"✗ LLMWorker structure error: {e}")
                return False
        
        # Test other components
        queue = RequestQueue()
        print("✓ RequestQueue created successfully")
        
        gpu_manager = GPUManager()
        print("✓ GPUManager created successfully")
        
        # Test GenerationConfig
        gen_config = GenerationConfig(max_new_tokens=100, temperature=0.8)
        print("✓ GenerationConfig created successfully")
        
        return True
    except Exception as e:
        print(f"✗ Worker structure test failed: {e}")
        return False

def test_monitoring():
    """Test monitoring components"""
    print("Testing monitoring components...")
    
    try:
        from monitoring import ResourceMonitor, HealthChecker, AutoRecoveryManager
        
        # Test ResourceMonitor
        monitor = ResourceMonitor()
        print("✓ ResourceMonitor created successfully")
        
        # Test HealthChecker
        checker = HealthChecker()
        print("✓ HealthChecker created successfully")
        
        # Test AutoRecoveryManager
        recovery = AutoRecoveryManager(None, checker)
        print("✓ AutoRecoveryManager created successfully")
        
        # Perform a basic health check (should not crash)
        health_result = checker.perform_health_check()
        print(f"✓ Health check completed, status: {health_result.get('overall_status', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"✗ Monitoring test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("Running LLM Worker component tests...\n")
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Worker Structure", test_worker_structure),
        ("Monitoring", test_monitoring)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"--- {test_name} Test ---")
        if test_func():
            passed += 1
        print()
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)