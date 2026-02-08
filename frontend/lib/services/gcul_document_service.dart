import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';
import '../config/app_config.dart';
import '../models/saved_document.dart';
import '../providers/auth_provider.dart' as auth_provider;
import '../services/biometric_service.dart';

/// Enhanced GCUL Document Service with Biometric Security
/// 
/// Handles Google Cloud Universal Ledger document operations with biometric verification:
/// - Document encryption and secure storage
/// - Blockchain-like hash verification with biometric authentication
/// - Document integrity validation with fingerprint verification
/// - Audit trail management with biometric access logs
class GCULDocumentService {
  static const String _baseUrl = AppConfig.apiBaseUrl;
  
  /// Save document with GCUL blockchain security and optional biometric verification
  /// 
  /// This method:
  /// 1. Optionally verifies biometric authentication for enhanced security
  /// 2. Encrypts document using Google Cloud KMS
  /// 3. Stores encrypted document in Google Cloud Storage
  /// 4. Creates hash record in Cloud Spanner blockchain tables
  /// 5. Returns document metadata with blockchain verification
  Future<SavedDocument> saveDocumentWithGCUL({
    required Uint8List fileBytes,
    required String fileName,
    required String fileType,
    required String documentType,
    String? extractedText,
    BuildContext? context,
    bool requireBiometric = false,
  }) async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        throw Exception('User not authenticated');
      }

      // Biometric verification for enhanced security (if requested and available)
      if (requireBiometric && context != null) {
      print('🔐 GCUL: Performing biometric verification for document save');
        final authProvider = Provider.of<auth_provider.AuthProvider>(context, listen: false);
        
        if (authProvider.isBiometricEnabled) {
          final biometricResult = await authProvider.verifyBiometricForGCUL('save document');
          
          if (biometricResult != BiometricVerificationResult.success && 
              biometricResult != BiometricVerificationResult.notEnrolled) {
            throw Exception('Biometric verification required for secure document operations');
          }
          
          if (biometricResult == BiometricVerificationResult.success) {
          print('GCUL: Biometric verification successful for document save');
          }
        }
      }

      // Create multipart request for document storage
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$_baseUrl/api/v1/mcp/store-document'),
      );

      // Add file
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          fileBytes,
          filename: fileName,
        ),
      );

      // Add metadata
      request.fields['user_email'] = user.email!;
      request.fields['file_name'] = fileName;
      request.fields['file_type'] = fileType;
      request.fields['document_type'] = documentType;
      request.fields['enable_gcul'] = 'true';
      
      if (extractedText != null) {
        request.fields['extracted_text'] = extractedText;
      }

    print('🔐 GCUL: Saving document with blockchain security...');
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        if (data['success'] == true) {
        print('GCUL: Document saved successfully with blockchain verification');
          return SavedDocument.fromJson(data['document']);
        } else {
          throw Exception(data['error'] ?? 'Failed to save document');
        }
      } else {
        throw Exception('HTTP ${response.statusCode}: ${response.body}');
      }

    } catch (e) {
    print('GCUL: Document save failed: $e');
      throw Exception('Failed to save document with GCUL: $e');
    }
  }

  /// Retrieve all user documents from Firebase and GCUL
  Future<List<SavedDocument>> getUserDocuments() async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        throw Exception('User not authenticated');
      }

      final response = await http.get(
        Uri.parse('$_baseUrl/api/v1/mcp/user-documents'),
        headers: {
          'Content-Type': 'application/json',
          'user-email': user.email!,
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        if (data['success'] == true) {
          final List<dynamic> documentsJson = data['documents'] ?? [];
          return documentsJson
              .map((json) => SavedDocument.fromJson(json))
              .toList();
        } else {
          throw Exception(data['error'] ?? 'Failed to load documents');
        }
      } else {
        throw Exception('HTTP ${response.statusCode}: ${response.body}');
      }

    } catch (e) {
    print('Error loading user documents: $e');
      throw Exception('Failed to load documents: $e');
    }
  }

  /// Verify document integrity using GCUL blockchain with biometric verification
  Future<Map<String, dynamic>> verifyDocumentIntegrity({
    required String documentId,
    required Uint8List currentFileBytes,
    BuildContext? context,
    bool requireBiometric = false,
  }) async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        throw Exception('User not authenticated');
      }

      // Biometric verification for sensitive operations
      if (requireBiometric && context != null) {
      print('🔐 GCUL: Performing biometric verification for document verification');
        final authProvider = Provider.of<auth_provider.AuthProvider>(context, listen: false);
        
        if (authProvider.isBiometricEnabled) {
          final biometricResult = await authProvider.verifyBiometricForGCUL('verify document integrity');
          
          if (biometricResult != BiometricVerificationResult.success && 
              biometricResult != BiometricVerificationResult.notEnrolled) {
            throw Exception('Biometric verification required for document integrity checks');
          }
          
          if (biometricResult == BiometricVerificationResult.success) {
          print('GCUL: Biometric verification successful for document verification');
          }
        }
      }

      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$_baseUrl/api/v1/mcp/verify-document'),
      );

      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          currentFileBytes,
          filename: 'verification_file',
        ),
      );

      request.fields['document_id'] = documentId;

    print('🔍 GCUL: Verifying document integrity...');
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
      print('GCUL: Document verification completed');
        return data['verification'];
      } else {
        throw Exception('HTTP ${response.statusCode}: ${response.body}');
      }

    } catch (e) {
    print('GCUL: Document verification failed: $e');
      throw Exception('Failed to verify document: $e');
    }
  }

  /// Get document audit trail from GCUL blockchain with biometric verification
  Future<List<Map<String, dynamic>>> getDocumentAuditTrail(String documentId, {
    BuildContext? context,
    bool requireBiometric = true,
  }) async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        throw Exception('User not authenticated');
      }

      // Biometric verification for audit trail access (highly sensitive)
      if (requireBiometric && context != null) {
      print('🔐 GCUL: Performing biometric verification for audit trail access');
        final authProvider = Provider.of<auth_provider.AuthProvider>(context, listen: false);
        
        if (authProvider.isBiometricEnabled) {
          final biometricResult = await authProvider.verifyBiometricForGCUL('view audit trail');
          
          if (biometricResult != BiometricVerificationResult.success && 
              biometricResult != BiometricVerificationResult.notEnrolled) {
            throw Exception('Biometric verification required for accessing audit trail data');
          }
          
          if (biometricResult == BiometricVerificationResult.success) {
          print('GCUL: Biometric verification successful for audit trail access');
          }
        }
      }

      final response = await http.post(
        Uri.parse('$_baseUrl/api/v1/mcp/get-audit-trail'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'text': documentId, // Using text field for document_id
          'user_email': user.email!,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        if (data['success'] == true) {
          return List<Map<String, dynamic>>.from(data['audit_trail'] ?? []);
        } else {
          throw Exception(data['error'] ?? 'Failed to get audit trail');
        }
      } else {
        throw Exception('HTTP ${response.statusCode}: ${response.body}');
      }

    } catch (e) {
    print('Error getting audit trail: $e');
      throw Exception('Failed to get audit trail: $e');
    }
  }

  /// Download and decrypt document from GCUL storage with biometric verification
  Future<Uint8List> downloadDocument(String documentId, {
    BuildContext? context,
    bool requireBiometric = false,
  }) async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        throw Exception('User not authenticated');
      }

      // Biometric verification for sensitive document access
      if (requireBiometric && context != null) {
      print('🔐 GCUL: Performing biometric verification for document download');
        final authProvider = Provider.of<auth_provider.AuthProvider>(context, listen: false);
        
        if (authProvider.isBiometricEnabled) {
          final biometricResult = await authProvider.verifyBiometricForGCUL('download document');
          
          if (biometricResult != BiometricVerificationResult.success && 
              biometricResult != BiometricVerificationResult.notEnrolled) {
            throw Exception('Biometric verification required for secure document access');
          }
          
          if (biometricResult == BiometricVerificationResult.success) {
          print('GCUL: Biometric verification successful for document download');
          }
        }
      }

      final response = await http.get(
        Uri.parse('$_baseUrl/api/v1/mcp/download-document/$documentId'),
        headers: {
          'Content-Type': 'application/json',
          'user-email': user.email!,
        },
      );

      if (response.statusCode == 200) {
      print('GCUL: Document downloaded and decrypted');
        return response.bodyBytes;
      } else {
        throw Exception('HTTP ${response.statusCode}: ${response.body}');
      }

    } catch (e) {
    print('GCUL: Document download failed: $e');
      throw Exception('Failed to download document: $e');
    }
  }

  /// Delete document from GCUL storage and blockchain with biometric verification
  Future<void> deleteDocument(String documentId, {
    BuildContext? context,
    bool requireBiometric = true,
  }) async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        throw Exception('User not authenticated');
      }

      // Biometric verification for document deletion (critical operation)
      if (requireBiometric && context != null) {
      print('🔐 GCUL: Performing biometric verification for document deletion');
        final authProvider = Provider.of<auth_provider.AuthProvider>(context, listen: false);
        
        if (authProvider.isBiometricEnabled) {
          final biometricResult = await authProvider.verifyBiometricForGCUL('delete document');
          
          if (biometricResult != BiometricVerificationResult.success && 
              biometricResult != BiometricVerificationResult.notEnrolled) {
            throw Exception('Biometric verification required for deleting secure documents');
          }
          
          if (biometricResult == BiometricVerificationResult.success) {
          print('GCUL: Biometric verification successful for document deletion');
          }
        }
      }

      final response = await http.delete(
        Uri.parse('$_baseUrl/api/v1/mcp/document/$documentId'),
        headers: {
          'Content-Type': 'application/json',
          'user-email': user.email!,
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        if (data['success'] != true) {
          throw Exception(data['error'] ?? 'Failed to delete document');
        }
        
      print('GCUL: Document deleted successfully');
      } else {
        throw Exception('HTTP ${response.statusCode}: ${response.body}');
      }

    } catch (e) {
    print('GCUL: Document deletion failed: $e');
      throw Exception('Failed to delete document: $e');
    }
  }

  /// Get document metadata only (without file content)
  Future<SavedDocument> getDocumentMetadata(String documentId) async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        throw Exception('User not authenticated');
      }

      final response = await http.get(
        Uri.parse('$_baseUrl/api/v1/mcp/document-metadata/$documentId'),
        headers: {
          'Content-Type': 'application/json',
          'user-email': user.email!,
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        if (data['success'] == true) {
          return SavedDocument.fromJson(data['document']);
        } else {
          throw Exception(data['error'] ?? 'Failed to get document metadata');
        }
      } else {
        throw Exception('HTTP ${response.statusCode}: ${response.body}');
      }

    } catch (e) {
    print('Error getting document metadata: $e');
      throw Exception('Failed to get document metadata: $e');
    }
  }
}