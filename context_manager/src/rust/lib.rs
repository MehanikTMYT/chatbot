//! Rust components for performance-critical context management operations
//! This includes optimized clustering algorithms and embedding operations

use pyo3::prelude::*;
use ndarray::{Array1, Array2};
use std::collections::HashMap;

/// A struct to handle fast semantic clustering operations
#[pyclass]
struct FastClusterer {
    #[pyo3(get, set)]
    threshold: f64,
}

#[pymethods]
impl FastClusterer {
    #[new]
    fn new(threshold: f64) -> Self {
        FastClusterer { threshold: threshold.max(0.0).min(1.0) }  // Clamp between 0 and 1
    }

    /// Perform fast agglomerative clustering on embeddings
    fn cluster(&self, embeddings: Vec<Vec<f64>>) -> PyResult<Vec<usize>> {
        // In a real implementation, this would perform optimized clustering
        // For now, we'll return a simple clustering based on similarity
        
        let n = embeddings.len();
        if n == 0 {
            return Ok(Vec::new());
        }
        
        // Create distance matrix (simplified Euclidean distance)
        let mut distances = vec![vec![0.0; n]; n];
        for i in 0..n {
            for j in i+1..n {
                let dist = euclidean_distance(&embeddings[i], &embeddings[j]);
                distances[i][j] = dist;
                distances[j][i] = dist;
            }
        }
        
        // Simple clustering algorithm: assign each point to nearest cluster
        // If distance is less than threshold, merge clusters
        let mut clusters = (0..n).collect::<Vec<_>>();
        let mut cluster_id = 0;
        
        for i in 0..n {
            if clusters[i] == i {  // Unassigned point
                clusters[i] = cluster_id;
                
                // Assign similar points to same cluster
                for j in i+1..n {
                    if distances[i][j] < self.threshold && clusters[j] == j {
                        clusters[j] = cluster_id;
                    }
                }
                
                cluster_id += 1;
            }
        }
        
        Ok(clusters)
    }

    /// Compute similarity between two embeddings
    fn compute_similarity(&self, emb1: Vec<f64>, emb2: Vec<f64>) -> PyResult<f64> {
        if emb1.len() != emb2.len() {
            return Err(pyo3::exceptions::PyValueError::new_err("Embeddings must have same dimension"));
        }
        
        Ok(cosine_similarity(&emb1, &emb2))
    }
    
    /// Batch compute similarities
    fn batch_similarities(&self, embeddings: Vec<Vec<f64>>) -> PyResult<Vec<Vec<f64>>> {
        let n = embeddings.len();
        let mut similarities = vec![vec![0.0; n]; n];
        
        for i in 0..n {
            for j in i..n {
                let sim = cosine_similarity(&embeddings[i], &embeddings[j]);
                similarities[i][j] = sim;
                similarities[j][i] = sim;
            }
        }
        
        Ok(similarities)
    }
}

/// Calculate Euclidean distance between two vectors
fn euclidean_distance(v1: &[f64], v2: &[f64]) -> f64 {
    v1.iter()
        .zip(v2.iter())
        .map(|(a, b)| (a - b).powi(2))
        .sum::<f64>()
        .sqrt()
}

/// Calculate cosine similarity between two vectors
fn cosine_similarity(v1: &[f64], v2: &[f64]) -> f64 {
    let dot_product: f64 = v1.iter().zip(v2.iter()).map(|(a, b)| a * b).sum();
    let magnitude_v1: f64 = v1.iter().map(|x| x.powi(2)).sum::<f64>().sqrt();
    let magnitude_v2: f64 = v2.iter().map(|x| x.powi(2)).sum::<f64>().sqrt();
    
    if magnitude_v1 == 0.0 || magnitude_v2 == 0.0 {
        0.0
    } else {
        dot_product / (magnitude_v1 * magnitude_v2)
    }
}

/// A struct to handle fast importance scoring operations
#[pyclass]
struct FastImportanceScorer {}

#[pymethods]
impl FastImportanceScorer {
    #[new]
    fn new() -> Self {
        FastImportanceScorer {}
    }

    /// Calculate importance scores for a batch of texts
    fn calculate_batch_scores(&self, texts: Vec<String>) -> PyResult<Vec<f64>> {
        // In a real implementation, this would use optimized text analysis
        // For now, we'll return a simple heuristic score based on text properties
        let mut scores = Vec::with_capacity(texts.len());
        
        for text in texts {
            let score = calculate_text_importance(&text);
            scores.push(score);
        }
        
        Ok(scores)
    }
}

/// Calculate a simple importance score for text
fn calculate_text_importance(text: &str) -> f64 {
    let lower_text = text.to_lowercase();
    let words: Vec<&str> = lower_text.split_whitespace().collect();
    
    // Base score components
    let emotional_keywords = [
        "excited", "happy", "sad", "angry", "frustrated", "grateful",
        "surprised", "shocked", "disappointed", "thrilled", "worried",
        "concerned", "amazed", "disgusted", "furious", "delighted"
    ];
    
    let emotional_score: f64 = emotional_keywords
        .iter()
        .map(|&word| if lower_text.contains(word) { 1.0 } else { 0.0 })
        .sum();
    
    // Factual content score (numbers, capitalized words)
    let factual_score: f64 = words
        .iter()
        .map(|word| {
            if word.chars().any(|c| c.is_digit(10)) {  // Contains numbers
                0.5
            } else if word.len() > 4 && word.chars().next().unwrap_or('a').is_uppercase() {  // Capitalized
                0.3
            } else {
                0.0
            }
        })
        .sum();
    
    // Length score (up to 1.0)
    let length_score = (text.len() as f64 / 100.0).min(1.0);
    
    // Combined score with normalization
    let total_score = (emotional_score * 0.4 + factual_score * 0.4 + length_score * 0.2).min(1.0);
    
    total_score
}

/// Main initialization function
#[pymodule]
fn context_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<FastClusterer>()?;
    m.add_class::<FastImportanceScorer>()?;
    Ok(())
}