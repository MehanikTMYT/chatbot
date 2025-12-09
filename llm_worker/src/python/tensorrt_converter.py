"""
Advanced Model Converter for Qwen3-8B-Q5_K_M to TensorRT using TensorRT-LLM
This script properly converts the HuggingFace model to TensorRT optimized format
"""
import os
import sys
import json
import logging
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TensorRTConverter:
    """Advanced converter using TensorRT-LLM for proper LLM optimization"""
    
    def __init__(self, model_path: str, output_dir: str, config: Dict):
        self.model_path = model_path
        self.output_dir = output_dir
        self.config = config
        self.tensorrt_llm_path = self._find_tensorrt_llm()
        
    def _find_tensorrt_llm(self) -> Optional[str]:
        """Find the TensorRT-LLM installation"""
        # Try common installation paths
        possible_paths = [
            "trtllm-build",  # Command line tool
            "/opt/tensorrtllm/bin/trtllm-build",
            "./tensorrt_llm/bin/trtllm-build"
        ]
        
        for path in possible_paths:
            if os.path.exists(path) or self._command_exists(path):
                logger.info(f"Found TensorRT-LLM at: {path}")
                return path
        
        logger.warning("TensorRT-LLM not found. This is required for proper LLM conversion.")
        logger.info("Install with: pip install tensorrt-llm")
        return None
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in the system"""
        try:
            subprocess.run([command, "--version"], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=False)
            return True
        except FileNotFoundError:
            return False
    
    def validate_requirements(self) -> bool:
        """Validate that all requirements are met for conversion"""
        requirements_met = True
        
        # Check for TensorRT-LLM
        if not self.tensorrt_llm_path:
            logger.error("TensorRT-LLM is required for model conversion")
            requirements_met = False
        
        # Check for CUDA
        try:
            import torch
            if not torch.cuda.is_available():
                logger.error("CUDA is not available. TensorRT conversion requires CUDA.")
                requirements_met = False
            else:
                logger.info(f"CUDA available: {torch.cuda.get_device_name()}")
        except ImportError:
            logger.error("PyTorch with CUDA support is required")
            requirements_met = False
        
        # Check model path exists
        if not os.path.exists(self.model_path):
            logger.error(f"Model path does not exist: {self.model_path}")
            requirements_met = False
        
        return requirements_met
    
    def create_conversion_config(self) -> Dict:
        """Create TensorRT-LLM conversion configuration"""
        # Default configuration for Qwen model on RTX 4070
        config = {
            "builder_config": {
                "precision": self.config.get("precision", "float16"),
                "quantization": self.config.get("quantization", "weight_only_int8"),
                "tensor_parallel": self.config.get("tensor_parallel", 1),
                "pipeline_parallel": self.config.get("pipeline_parallel", 1),
                "strongly_typed": False
            },
            "model_config": {
                "architecture": "QWEN2ForCausalLM",  # Adjust based on actual model
                "vocab_size": 151936,  # Qwen3 vocab size
                "hidden_size": 4096,
                "num_hidden_layers": 32,
                "num_attention_heads": 32,
                "num_key_value_heads": 32,
                "hidden_act": "silu",
                "max_position_embeddings": 32768,
                "type_vocab_size": 0,
                "intermediate_size": 14336,
                "norm_epsilon": 1e-06,
                "position_embedding_type": "rope",
                "world_size": 1,
                "tp_size": 1,
                "pp_size": 1
            },
            "quantization_config": {
                "quant_algo": self.config.get("quantization", "weight_only_int8"),
                "kv_cache_quant_algo": "fp8",  # Use FP8 for KV cache if available
                "smooth_quant_alpha": 0.5
            }
        }
        
        return config
    
    def convert_model(self) -> bool:
        """Convert the model using TensorRT-LLM"""
        if not self.validate_requirements():
            logger.error("Requirements not met for model conversion")
            return False
        
        logger.info(f"Starting model conversion from {self.model_path} to {self.output_dir}")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create config file
        config_path = os.path.join(self.output_dir, "config.json")
        conversion_config = self.create_conversion_config()
        
        with open(config_path, 'w') as f:
            json.dump(conversion_config, f, indent=2)
        
        logger.info(f"Conversion configuration saved to {config_path}")
        
        try:
            # Build TensorRT engine using trtllm-build command
            cmd = [
                "trtllm-build", 
                "--checkpoint_dir", self.model_path,
                "--output_dir", self.output_dir,
                "--gemm_plugin", "float16",  # Use FP16 GEMM plugin
                "--enable_context_fmha",  # Enable fused multi-head attention
                "--remove_input_padding",  # Optimize by removing input padding
                "--max_batch_size", str(self.config.get("max_batch_size", 8)),
                "--max_input_len", str(self.config.get("max_input_len", 2048)),
                "--max_output_len", str(self.config.get("max_output_len", 2048)),
                "--max_beam_width", str(self.config.get("max_beam_width", 1))
            ]
            
            # Add quantization flags based on configuration
            quantization = self.config.get("quantization", "weight_only_int8")
            if quantization == "weight_only_int8":
                cmd.extend(["--use_weight_only", "--weight_only_precision", "int8"])
            elif quantization == "weight_only_int4":
                cmd.extend(["--use_weight_only", "--weight_only_precision", "int4"])
            elif quantization == "smooth_quant":
                cmd.extend(["--use_smooth_quant"])
            
            # For RTX 4070 optimization
            cmd.extend([
                "--enable_gemm_split_k", "true",  # Enable split K for better performance
                "--hidden_act", "silu"  # Activation function for Qwen
            ])
            
            logger.info(f"Running conversion command: {' '.join(cmd)}")
            
            # Run the conversion process
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                logger.info("Model conversion completed successfully")
                logger.info(f"Output saved to: {self.output_dir}")
                
                # Verify the output
                engine_files = [
                    os.path.join(self.output_dir, "rank0.engine"),
                    os.path.join(self.output_dir, "config.json")
                ]
                
                all_files_exist = all(os.path.exists(f) for f in engine_files)
                if all_files_exist:
                    logger.info("All output files generated successfully")
                    return True
                else:
                    logger.warning("Some output files may be missing")
                    return False
            else:
                logger.error(f"Model conversion failed with return code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Model conversion timed out")
            return False
        except Exception as e:
            logger.error(f"Error during model conversion: {e}")
            return False
    
    def optimize_for_rtx4070(self) -> bool:
        """Apply RTX 4070 specific optimizations"""
        logger.info("Applying RTX 4070 specific optimizations")
        
        # RTX 4070 specific optimizations
        optimizations = {
            "gpu_memory_fraction": 0.85,  # Use 85% of available memory
            "max_batch_size": 4,  # Optimal for RTX 4070
            "precision": "float16",  # Good balance of performance/accuracy for RTX 4070
            "use_fp8_kv_cache": True if self._supports_fp8() else False,  # Use FP8 if supported
        }
        
        logger.info(f"Applied optimizations: {optimizations}")
        
        # Update the config with RTX 4070 specific settings
        self.config.update(optimizations)
        
        return True
    
    def _supports_fp8(self) -> bool:
        """Check if the current GPU supports FP8"""
        try:
            import torch
            if torch.cuda.is_available():
                # Check compute capability - Ada Lovelace (40 series) supports FP8
                device = torch.cuda.current_device()
                major, minor = torch.cuda.get_device_capability(device)
                # Ada Lovelace (40 series) has compute capability 8.9
                return major >= 8  # FP8 support starts from compute capability 8.9
        except:
            pass
        return False

def main():
    parser = argparse.ArgumentParser(description="Convert Qwen model to TensorRT format using TensorRT-LLM")
    parser.add_argument("--model_path", type=str, required=True,
                       help="Path to the HuggingFace model directory")
    parser.add_argument("--output_dir", type=str, required=True,
                       help="Output directory for TensorRT engine")
    parser.add_argument("--precision", type=str, default="float16",
                       choices=["float16", "float32", "bfloat16"],
                       help="Precision for TensorRT engine")
    parser.add_argument("--quantization", type=str, default="weight_only_int8",
                       choices=["weight_only_int8", "weight_only_int4", "smooth_quant", "none"],
                       help="Quantization method")
    parser.add_argument("--max_batch_size", type=int, default=4,
                       help="Maximum batch size for the engine")
    parser.add_argument("--max_input_len", type=int, default=2048,
                       help="Maximum input length")
    parser.add_argument("--max_output_len", type=int, default=2048,
                       help="Maximum output length")
    
    args = parser.parse_args()
    
    # Configuration for the converter
    config = {
        "precision": args.precision,
        "quantization": args.quantization,
        "max_batch_size": args.max_batch_size,
        "max_input_len": args.max_input_len,
        "max_output_len": args.max_output_len,
        "tensor_parallel": 1,
        "pipeline_parallel": 1
    }
    
    # Create converter instance
    converter = TensorRTConverter(args.model_path, args.output_dir, config)
    
    # Apply RTX 4070 specific optimizations
    converter.optimize_for_rtx4070()
    
    # Convert the model
    success = converter.convert_model()
    
    if success:
        logger.info("Model conversion completed successfully!")
        logger.info(f"TensorRT engine saved to: {args.output_dir}")
    else:
        logger.error("Model conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()