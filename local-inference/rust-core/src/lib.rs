use pyo3::prelude::*;
use pyo3::types::PyDict;

mod tensorrt;
use tensorrt::TensorRTInference;

/// A Python module implemented in Rust for accelerated inference
#[pymodule]
fn chatbot_inference(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<TensorRTInference>()?;
    m.add_wrapped(wrap_pyfunction!(run_inference))?;
    Ok(())
}

/// Main inference function exposed to Python
#[pyfunction]
fn run_inference(
    py: Python,
    model_path: &str,
    input_data: &PyDict,
) -> PyResult<PyObject> {
    // Create a new TensorRT inference engine
    let mut engine = TensorRTInference::new(model_path)?;
    
    // Convert Python input to Rust types
    let input_text = input_data
        .get_item("text")
        .unwrap_or(py.None().into_ref(py))
        .extract::<String>()?;
    
    // Run the inference
    let result = engine.infer(&input_text)?;
    
    // Return result as Python object
    Ok(PyDict::new(py).into())
}

/// Performance benchmarking function
#[pyfunction]
fn benchmark_performance(iterations: usize) -> PyResult<f64> {
    // Placeholder for performance benchmarking
    // In real implementation, this would measure inference speed
    Ok(iterations as f64 * 0.01) // Placeholder
}