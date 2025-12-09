//! Common utilities for the hybrid chatbot system
//! Provides shared functionality across different components

use anyhow::Result;
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use std::time::SystemTime;

/// Timestamp utility for consistent time handling
pub fn get_current_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .unwrap()
        .as_secs()
}

/// Memory-efficient string operations
pub mod string_utils {
    /// Efficiently joins a collection of strings with a separator
    pub fn join_strings(strings: &[String], separator: &str) -> String {
        strings.join(separator)
    }

    /// Calculates similarity between two strings using Levenshtein distance
    pub fn string_similarity(s1: &str, s2: &str) -> f64 {
        let len1 = s1.chars().count();
        let len2 = s2.chars().count();
        
        if len1 == 0 && len2 == 0 {
            return 1.0;
        }
        if len1 == 0 || len2 == 0 {
            return 0.0;
        }

        let max_len = len1.max(len2);
        let distance = levenshtein_distance(s1, s2);
        
        1.0 - (distance as f64 / max_len as f64)
    }

    /// Calculates Levenshtein distance between two strings
    fn levenshtein_distance(s1: &str, s2: &str) -> usize {
        let chars1: Vec<char> = s1.chars().collect();
        let chars2: Vec<char> = s2.chars().collect();
        let len1 = chars1.len();
        let len2 = chars2.len();

        let mut matrix = vec![vec![0; len2 + 1]; len1 + 1];

        for i in 0..=len1 {
            matrix[i][0] = i;
        }
        for j in 0..=len2 {
            matrix[0][j] = j;
        }

        for i in 1..=len1 {
            for j in 1..=len2 {
                let cost = if chars1[i - 1] == chars2[j - 1] { 0 } else { 1 };
                matrix[i][j] = (matrix[i - 1][j] + 1)
                    .min(matrix[i][j - 1] + 1)
                    .min(matrix[i - 1][j - 1] + cost);
            }
        }

        matrix[len1][len2]
    }
}

/// Performance monitoring utilities
pub mod perf_utils {
    use std::time::Instant;

    /// Measures execution time of a closure
    pub fn measure_time<F, R>(operation: F) -> (R, f64)
    where
        F: FnOnce() -> R,
    {
        let start = Instant::now();
        let result = operation();
        let duration = start.elapsed().as_secs_f64();
        (result, duration)
    }
}

/// Configuration for utilities
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UtilsConfig {
    /// Log level for utilities
    pub log_level: String,
    /// Performance tracking enabled
    pub perf_tracking: bool,
}

/// Main utilities service
pub struct UtilsService {
    config: Arc<UtilsConfig>,
}

impl UtilsService {
    /// Creates a new utilities service with the given configuration
    pub fn new(config: UtilsConfig) -> Self {
        Self {
            config: Arc::new(config),
        }
    }

    /// Gets the current timestamp
    pub fn timestamp(&self) -> u64 {
        get_current_timestamp()
    }

    /// Joins strings efficiently
    pub fn join_strings(&self, strings: &[String], separator: &str) -> String {
        string_utils::join_strings(strings, separator)
    }

    /// Calculates similarity between two strings
    pub fn string_similarity(&self, s1: &str, s2: &str) -> f64 {
        string_utils::string_similarity(s1, s2)
    }

    /// Measures execution time of a closure
    pub fn measure_time<F, R>(&self, operation: F) -> (R, f64)
    where
        F: FnOnce() -> R,
    {
        perf_utils::measure_time(operation)
    }
}

/// Python bindings for utilities
#[pymodule]
fn utils(_py: Python, m: &PyModule) -> PyResult<()> {
    #[pyclass]
    struct PyUtilsService {
        service: Arc<UtilsService>,
    }

    #[pymethods]
    impl PyUtilsService {
        #[new]
        fn new(log_level: String, perf_tracking: bool) -> Self {
            let config = UtilsConfig {
                log_level,
                perf_tracking,
            };
            let service = Arc::new(UtilsService::new(config));
            
            Self { service }
        }

        fn timestamp(&self) -> u64 {
            self.service.timestamp()
        }

        fn join_strings(&self, strings: Vec<String>, separator: String) -> String {
            self.service.join_strings(&strings, &separator)
        }

        fn string_similarity(&self, s1: String, s2: String) -> f64 {
            self.service.string_similarity(&s1, &s2)
        }

        fn measure_time(&self, py: Python) -> PyResult<(PyObject, f64)> {
            // This is a simplified implementation - in practice you'd want to accept
            // a callable Python object and measure its execution time
            let result = py.None();
            Ok((result, 0.0))
        }
    }

    #[pyfn]
    fn get_timestamp() -> u64 {
        get_current_timestamp()
    }

    m.add_class::<PyUtilsService>()?;
    m.add_function(wrap_pyfunction!(get_timestamp, m)?)?;
    Ok(())
}