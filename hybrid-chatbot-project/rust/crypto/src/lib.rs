//! Cryptographic utilities for secure tunneling in the hybrid chatbot system
//! Provides encryption/decryption, key management, and secure communication protocols

use anyhow::Result;
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use ring::{aead, aead::LessSafeKey, aead::UnboundKey, aead::Nonce, aead::Aad};

/// Represents an encrypted message with associated metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncryptedMessage {
    /// Encrypted data payload
    pub data: Vec<u8>,
    /// Initialization vector for decryption
    pub iv: Vec<u8>,
    /// Authentication tag for AEAD ciphers
    pub tag: Option<Vec<u8>>,
    /// Timestamp of encryption
    pub timestamp: u64,
}

/// Configuration for cryptographic operations
#[derive(Debug, Clone)]
pub struct CryptoConfig {
    /// Encryption key
    pub key: Vec<u8>,
    /// Algorithm to use
    pub algorithm: CryptoAlgorithm,
}

/// Available cryptographic algorithms
#[derive(Debug, Clone)]
pub enum CryptoAlgorithm {
    Aes256Gcm,
    ChaCha20Poly1305,
}

/// Main cryptographic service
pub struct CryptoService {
    config: Arc<CryptoConfig>,
}

impl CryptoService {
    /// Creates a new cryptographic service with the given configuration
    pub fn new(config: CryptoConfig) -> Self {
        Self {
            config: Arc::new(config),
        }
    }

    /// Encrypts data using the configured algorithm
    pub fn encrypt(&self, data: &[u8]) -> Result<EncryptedMessage> {
        let key_bytes = &self.config.key;
        let alg = match self.config.algorithm {
            CryptoAlgorithm::Aes256Gcm => &aead::AES_256_GCM,
            CryptoAlgorithm::ChaCha20Poly1305 => &aead::CHACHA20_POLY1305,
        };
        
        let unbound_key = UnboundKey::new(alg, key_bytes)?;
        let key = LessSafeKey::new(unbound_key);
        
        // Generate random nonce (IV)
        let mut nonce_bytes = [0u8; 12];  // 96-bit nonce for AES-GCM
        get_random_bytes(&mut nonce_bytes);
        let nonce = Nonce::try_assume_unique_for_key(nonce_bytes)?;
        
        // Create additional authenticated data (AAD)
        let aad = Aad::from(&[]);
        
        // Prepare buffer for encryption (data + tag)
        let mut in_out = data.to_vec();
        let tag = key.seal_in_place_append_tag(nonce, aad, &mut in_out)?;
        
        Ok(EncryptedMessage {
            data: in_out,
            iv: nonce_bytes.to_vec(),
            tag: Some(tag.as_ref().to_vec()),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        })
    }

    /// Decrypts data using the configured algorithm
    pub fn decrypt(&self, encrypted: &EncryptedMessage) -> Result<Vec<u8>> {
        let key_bytes = &self.config.key;
        let alg = match self.config.algorithm {
            CryptoAlgorithm::Aes256Gcm => &aead::AES_256_GCM,
            CryptoAlgorithm::ChaCha20Poly1305 => &aead::CHACHA20_POLY1305,
        };
        
        let unbound_key = UnboundKey::new(alg, key_bytes)?;
        let key = LessSafeKey::new(unbound_key);
        
        // Reconstruct nonce from IV
        let mut nonce_bytes = [0u8; 12];
        if encrypted.iv.len() != 12 {
            return Err(anyhow::anyhow!("Invalid IV length"));
        }
        nonce_bytes.copy_from_slice(&encrypted.iv);
        let nonce = Nonce::try_assume_unique_for_key(nonce_bytes)?;
        
        // Create additional authenticated data (AAD)
        let aad = Aad::from(&[]);
        
        // Prepare buffer for decryption (data + tag)
        let mut in_out = encrypted.data.clone();
        
        // Decrypt and verify
        let plaintext = key.open_in_place(nonce, aad, &mut in_out)?;
        
        Ok(plaintext.to_vec())
    }
}

/// Helper function to generate random bytes
fn get_random_bytes(bytes: &mut [u8]) {
    use ring::rand::{SecureRandom, SystemRandom};
    let rng = SystemRandom::new();
    rng.fill(bytes).unwrap();
}

/// Python bindings for the cryptographic service
#[pymodule]
fn crypto(_py: Python, m: &PyModule) -> PyResult<()> {
    #[pyclass]
    struct PyCryptoService {
        service: Arc<CryptoService>,
    }

    #[pymethods]
    impl PyCryptoService {
        #[new]
        fn new(key: Vec<u8>) -> Self {
            let config = CryptoConfig {
                key,
                algorithm: CryptoAlgorithm::Aes256Gcm,
            };
            let service = Arc::new(CryptoService::new(config));
            
            Self { service }
        }

        fn encrypt(&self, data: Vec<u8>) -> PyResult<Vec<u8>> {
            let encrypted = self
                .service
                .encrypt(&data)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyException, _>(e.to_string()))?;
            
            // Serialize the EncryptedMessage to bytes for Python
            let mut result = Vec::new();
            result.extend_from_slice(&encrypted.iv);
            if let Some(tag) = &encrypted.tag {
                result.extend_from_slice(tag);
            }
            result.extend_from_slice(&encrypted.data);
            
            Ok(result)
        }

        fn decrypt(&self, data: Vec<u8>) -> PyResult<Vec<u8>> {
            // Parse the encrypted data: IV (12 bytes) + Tag (16 bytes for AES-GCM) + ciphertext
            if data.len() < 28 {  // At least IV + tag
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Encrypted data too short"));
            }
            
            let iv = data[0..12].to_vec();
            let tag = Some(data[12..28].to_vec());
            let ciphertext = data[28..].to_vec();
            
            let encrypted_msg = EncryptedMessage {
                data: ciphertext,
                iv,
                tag,
                timestamp: std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_secs(),
            };
            
            let decrypted = self
                .service
                .decrypt(&encrypted_msg)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyException, _>(e.to_string()))?;
            
            Ok(decrypted)
        }
    }

    m.add_class::<PyCryptoService>()?;
    Ok(())
}