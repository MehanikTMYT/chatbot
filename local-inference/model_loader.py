import os
import sys
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ModelLoader:
    def __init__(self):
        self.rust_module = None
        self.rust_acceleration = os.getenv('RUST_ACCELERATION', 'true').lower() == 'true'
        self.fallback_on_error = os.getenv('RUST_FALLBACK_ON_ERROR', 'true').lower() == 'true'
        self._load_rust_module()
    
    def _load_rust_module(self):
        """Загрузка Rust-модуля с fallback на Python при ошибке"""
        if not self.rust_acceleration:
            logger.info("Rust acceleration is disabled")
            return
        
        try:
            import chatbot_inference
            self.rust_module = chatbot_inference
            logger.info("Rust module loaded successfully")
            
            # Run a quick benchmark to verify the module works
            if hasattr(chatbot_inference, 'benchmark_performance'):
                perf = chatbot_inference.benchmark_performance(1)
                logger.info(f"Rust module performance check: {perf}")
                
        except ImportError as e:
            logger.error(f"Failed to import Rust module: {e}")
            if self.fallback_on_error:
                logger.info("Falling back to Python implementation")
                self.rust_module = None
            else:
                raise e
        except Exception as e:
            logger.error(f"Error initializing Rust module: {e}")
            if self.fallback_on_error:
                logger.info("Falling back to Python implementation")
                self.rust_module = None
            else:
                raise e
    
    def load_model(self, model_path: str, **kwargs) -> Any:
        """Загрузка модели с использованием Rust или Python"""
        if self.rust_module:
            try:
                # Используем Rust для загрузки модели
                return self.rust_module.TensorRTInference(model_path)
            except Exception as e:
                logger.error(f"Rust model loading failed: {e}")
                if self.fallback_on_error:
                    logger.info("Falling back to Python model loading")
                    return self._load_python_model(model_path, **kwargs)
                else:
                    raise e
        else:
            # Используем Python для загрузки модели
            return self._load_python_model(model_path, **kwargs)
    
    def _load_python_model(self, model_path: str, **kwargs) -> Any:
        """Загрузка модели с использованием Python (fallback)"""
        logger.info(f"Loading model with Python implementation: {model_path}")
        # В реальной реализации здесь будет загрузка модели через PyTorch, Transformers и т.д.
        # Пока создаем заглушку
        class PythonModel:
            def __init__(self, path):
                self.path = path
                self.loaded = True
            
            def infer(self, input_text: str) -> str:
                return f"Python processed: {input_text}"
        
        return PythonModel(model_path)
    
    def run_inference(self, model: Any, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение инференса с использованием Rust или Python"""
        if self.rust_module and hasattr(model, 'infer'):
            try:
                # Пытаемся использовать Rust для инференса
                result = model.infer(input_data.get('text', ''))
                return {
                    'result': result,
                    'engine': 'rust',
                    'success': True
                }
            except Exception as e:
                logger.error(f"Rust inference failed: {e}")
                if self.fallback_on_error:
                    logger.info("Falling back to Python inference")
                    return self._run_python_inference(model, input_data)
                else:
                    return {
                        'result': str(e),
                        'engine': 'rust',
                        'success': False
                    }
        else:
            # Используем Python для инференса
            return self._run_python_inference(model, input_data)
    
    def _run_python_inference(self, model: Any, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение инференса с использованием Python (fallback)"""
        try:
            result = model.infer(input_data.get('text', ''))
            return {
                'result': result,
                'engine': 'python',
                'success': True
            }
        except Exception as e:
            logger.error(f"Python inference failed: {e}")
            return {
                'result': str(e),
                'engine': 'python',
                'success': False
            }
    
    def benchmark_performance(self, iterations: int = 100) -> Dict[str, float]:
        """Сравнение производительности Rust и Python реализаций"""
        if not self.rust_module:
            logger.warning("Rust module not available for benchmarking")
            return {'rust_speed': 0, 'python_speed': 0, 'improvement': 0}
        
        import time
        
        # Benchmark Rust
        start_time = time.time()
        try:
            if hasattr(self.rust_module, 'benchmark_performance'):
                rust_result = self.rust_module.benchmark_performance(iterations)
            else:
                # Fallback: run a simple test
                test_input = {"text": "test input"}
                for _ in range(iterations):
                    self.run_inference(None, test_input)  # This will use Python fallback
            rust_time = time.time() - start_time
        except:
            rust_time = float('inf')
        
        # Benchmark Python
        start_time = time.time()
        test_input = {"text": "test input"}
        for _ in range(iterations):
            self._run_python_inference(self._load_python_model("dummy"), test_input)
        python_time = time.time() - start_time
        
        improvement = ((python_time - rust_time) / python_time) * 100 if rust_time != float('inf') else 0
        
        return {
            'rust_time': rust_time,
            'python_time': python_time,
            'improvement': improvement
        }

# Singleton instance
model_loader = ModelLoader()