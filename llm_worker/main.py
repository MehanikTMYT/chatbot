#!/usr/bin/env python3
"""
Main entry point for LLM Worker
Starts the LLM worker service with TensorRT optimization for RTX 4070
"""
import argparse
import asyncio
import logging
import os
import signal
import sys
import threading
import time
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src" / "python"))

from llm_worker import LLMWorker, GenerationConfig
from config.config import get_default_config, LLMWorkerConfig
from api_server import run_api_server
from monitoring import resource_monitor, health_checker, AutoRecoveryManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMWorkerService:
    """Main service class that manages the LLM worker lifecycle"""
    
    def __init__(self, config: LLMWorkerConfig):
        self.config = config
        self.worker = None
        self.api_thread = None
        self.monitoring_thread = None
        self.health_check_thread = None
        self.recovery_manager = None
        self.shutdown_event = threading.Event()
        
    def start(self):
        """Start the LLM worker service"""
        logger.info("Starting LLM Worker Service...")
        
        # Initialize the LLM worker
        self._init_worker()
        
        # Start monitoring
        self._start_monitoring()
        
        # Start API server in a separate thread
        self._start_api_server()
        
        # Start health monitoring
        self._start_health_monitoring()
        
        logger.info("LLM Worker Service started successfully")
        
    def _init_worker(self):
        """Initialize the LLM worker"""
        try:
            logger.info(f"Initializing LLM worker with model: {self.config.model_config.tensorrt_model_path}")
            
            self.worker = LLMWorker(
                model_path=self.config.model_config.tensorrt_model_path,
                tokenizer_path=self.config.model_config.tokenizer_path
            )
            self.worker.start()
            
            # Initialize recovery manager
            self.recovery_manager = AutoRecoveryManager(self.worker, health_checker)
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM worker: {e}")
            raise
    
    def _start_monitoring(self):
        """Start resource monitoring"""
        try:
            resource_monitor.start_monitoring()
            logger.info("Resource monitoring started")
        except Exception as e:
            logger.error(f"Failed to start resource monitoring: {e}")
    
    def _start_api_server(self):
        """Start the API server in a separate thread"""
        def run_server():
            try:
                run_api_server(
                    host=self.config.system_config.api_host,
                    port=self.config.system_config.api_port
                )
            except Exception as e:
                logger.error(f"API server error: {e}")
        
        self.api_thread = threading.Thread(target=run_server, daemon=True)
        self.api_thread.start()
        logger.info(f"API server started on {self.config.system_config.api_host}:{self.config.system_config.api_port}")
    
    def _start_health_monitoring(self):
        """Start health monitoring loop"""
        def health_loop():
            while not self.shutdown_event.is_set():
                try:
                    # Perform health check
                    health_result = health_checker.perform_health_check()
                    
                    # Log health status
                    if health_result['overall_status'] != 'healthy':
                        logger.warning(f"Health check failed: {health_result}")
                        
                        # Attempt recovery
                        if self.recovery_manager:
                            self.recovery_manager.monitor_and_recover()
                    else:
                        logger.debug("Health check passed")
                    
                    # Wait before next check
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    logger.error(f"Error in health monitoring loop: {e}")
                    time.sleep(10)  # Wait before retrying
        
        self.health_check_thread = threading.Thread(target=health_loop, daemon=True)
        self.health_check_thread.start()
        logger.info("Health monitoring started")
    
    def stop(self):
        """Stop the LLM worker service"""
        logger.info("Stopping LLM Worker Service...")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Stop worker
        if self.worker:
            self.worker.stop()
        
        # Stop monitoring
        resource_monitor.stop_monitoring()
        
        logger.info("LLM Worker Service stopped")
    
    def wait_for_shutdown(self):
        """Wait for the service to be properly shut down"""
        try:
            # Wait indefinitely until shutdown is signaled
            while not self.shutdown_event.wait(1):  # Check every second
                pass
        except KeyboardInterrupt:
            logger.info("Interrupt received, shutting down...")
        finally:
            self.stop()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="LLM Worker Service for RTX 4070")
    
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to configuration file"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        help="Path to TensorRT model"
    )
    parser.add_argument(
        "--tokenizer-path",
        type=str,
        help="Path to tokenizer"
    )
    parser.add_argument(
        "--api-host",
        type=str,
        default="127.0.0.1",
        help="API server host"
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8000,
        help="API server port"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    return parser.parse_args()

def setup_signal_handlers(service: LLMWorkerService):
    """Set up signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        service.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Update log level if specified
    logging.getLogger().setLevel(args.log_level)
    
    # Load configuration
    if args.config:
        config = LLMWorkerConfig.from_file(args.config)
    else:
        config = get_default_config()
    
    # Override with command line arguments if provided
    if args.model_path:
        config.model_config.tensorrt_model_path = args.model_path
    if args.tokenizer_path:
        config.model_config.tokenizer_path = args.tokenizer_path
    if args.api_host:
        config.system_config.api_host = args.api_host
    if args.api_port:
        config.system_config.api_port = args.api_port
    
    # Create and start the service
    service = LLMWorkerService(config)
    
    # Set up signal handlers for graceful shutdown
    setup_signal_handlers(service)
    
    try:
        # Start the service
        service.start()
        
        # Wait for shutdown
        service.wait_for_shutdown()
        
    except Exception as e:
        logger.error(f"Error running LLM Worker Service: {e}")
        sys.exit(1)
    finally:
        service.stop()

if __name__ == "__main__":
    main()