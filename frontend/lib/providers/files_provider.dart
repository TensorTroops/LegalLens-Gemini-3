import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../models/saved_document.dart';
import '../services/gcul_document_service.dart';

class FilesProvider with ChangeNotifier {
  final GCULDocumentService _gculService = GCULDocumentService();
  
  List<SavedDocument> _documents = [];
  List<SavedDocument> _filteredDocuments = [];
  bool _isLoading = false;
  String _errorMessage = '';
  String _selectedFilter = 'Recent';
  String _searchQuery = '';

  // Getters
  List<SavedDocument> get documents => _filteredDocuments;
  bool get isLoading => _isLoading;
  String get errorMessage => _errorMessage;
  String get selectedFilter => _selectedFilter;
  String get searchQuery => _searchQuery;

  /// Load user documents from Firebase and GCUL
  Future<void> loadDocuments({String? userId}) async {
    _isLoading = true;
    _errorMessage = '';
    notifyListeners();

    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        throw Exception('User not authenticated');
      }

    print('📚 Loading documents from Firebase and GCUL...');
      
      // Get documents from GCUL service
      _documents = await _gculService.getUserDocuments();
      
    print('✅ Loaded ${_documents.length} documents successfully');
      
      _applyFilters();
      _isLoading = false;
      notifyListeners();
      
    } catch (e) {
    print('❌ Error loading documents: $e');
      _errorMessage = 'Failed to load documents: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Add a new document to the list (called after saving)
  void addDocument(SavedDocument document) {
    _documents.insert(0, document); // Add to beginning for recent first
    _applyFilters();
    notifyListeners();
  }

  /// Set filter for document display
  void setFilter(String filter) {
    _selectedFilter = filter;
    _applyFilters();
    notifyListeners();
  }

  /// Set search query for document filtering
  void setSearchQuery(String query) {
    _searchQuery = query;
    _applyFilters();
    notifyListeners();
  }

  /// Apply current filters and search to document list
  void _applyFilters() {
    List<SavedDocument> filtered = List.from(_documents);

    // Apply search filter
    if (_searchQuery.isNotEmpty) {
      filtered = filtered.where((doc) =>
          doc.title.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          doc.fileName.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          doc.documentType.toLowerCase().contains(_searchQuery.toLowerCase())
      ).toList();
    }

    // Apply category filter
    switch (_selectedFilter) {
      case 'Recent':
        filtered.sort((a, b) => b.createdAt.compareTo(a.createdAt));
        break;
      case 'All':
        // No additional filtering
        break;
      case 'Type':
        filtered.sort((a, b) => a.fileType.compareTo(b.fileType));
        break;
      case 'Jurisdiction':
        // Group by document type for now
        filtered.sort((a, b) => a.documentType.compareTo(b.documentType));
        break;
    }

    _filteredDocuments = filtered;
  }

  /// Delete document using GCUL service with biometric verification
  Future<void> deleteDocument(String documentId, {
    BuildContext? context,
    bool requireBiometric = true,
  }) async {
    try {
    print('🗑️ Deleting document: $documentId');
      
      // Delete from GCUL storage and blockchain with biometric verification
      await _gculService.deleteDocument(
        documentId,
        context: context,
        requireBiometric: requireBiometric,
      );
      
      // Remove from local list
      _documents.removeWhere((doc) => doc.id == documentId);
      _applyFilters();
      notifyListeners();
      
    print('✅ Document deleted successfully');
    } catch (e) {
    print('❌ Error deleting document: $e');
      _errorMessage = 'Failed to delete document: ${e.toString()}';
      notifyListeners();
      rethrow;
    }
  }

  /// Refresh documents list
  Future<void> refreshDocuments({String? userId}) async {
    await loadDocuments(userId: userId);
  }

  /// Verify document integrity using GCUL blockchain with biometric verification
  Future<Map<String, dynamic>> verifyDocumentIntegrity(SavedDocument document, {
    BuildContext? context,
    bool requireBiometric = true,
  }) async {
    try {
    print('🔍 Verifying document integrity: ${document.id}');
      
      // First download the current document with biometric verification
      final currentBytes = await _gculService.downloadDocument(
        document.id,
        context: context,
        requireBiometric: requireBiometric,
      );
      
      // Verify against blockchain with biometric verification
      final verification = await _gculService.verifyDocumentIntegrity(
        documentId: document.id,
        currentFileBytes: currentBytes,
        context: context,
        requireBiometric: requireBiometric,
      );
      
    print('✅ Document verification completed');
      return verification;
      
    } catch (e) {
    print('❌ Error verifying document: $e');
      throw Exception('Failed to verify document: $e');
    }
  }

  /// Get document audit trail from GCUL blockchain with biometric verification
  Future<List<Map<String, dynamic>>> getDocumentAuditTrail(String documentId, {
    BuildContext? context,
    bool requireBiometric = true,
  }) async {
    try {
    print('📋 Getting audit trail for: $documentId');
      
      final auditTrail = await _gculService.getDocumentAuditTrail(
        documentId,
        context: context,
        requireBiometric: requireBiometric,
      );
      
    print('✅ Retrieved audit trail with ${auditTrail.length} entries');
      return auditTrail;
      
    } catch (e) {
    print('❌ Error getting audit trail: $e');
      throw Exception('Failed to get audit trail: $e');
    }
  }

  /// Download document from GCUL storage with biometric verification
  Future<List<int>> downloadDocument(String documentId, {
    BuildContext? context,
    bool requireBiometric = true,
  }) async {
    try {
    print('📥 Downloading document: $documentId');
      
      final bytes = await _gculService.downloadDocument(
        documentId,
        context: context,
        requireBiometric: requireBiometric,
      );
      
    print('✅ Document downloaded successfully');
      return bytes;
      
    } catch (e) {
    print('❌ Error downloading document: $e');
      throw Exception('Failed to download document: $e');
    }
  }

  /// Clear error message
  void clearError() {
    _errorMessage = '';
    notifyListeners();
  }

  /// Get statistics about user documents
  Map<String, dynamic> getDocumentStatistics() {
    final blockchainVerified = _documents.where((doc) => doc.isBlockchainVerified).length;
    final totalSize = _documents.fold<double>(0, (sum, doc) {
      final sizeStr = doc.fileSize.replaceAll(RegExp(r'[^0-9.]'), '');
      final size = double.tryParse(sizeStr) ?? 0;
      final isMB = doc.fileSize.contains('MB');
      return sum + (isMB ? size * 1024 : size);
    });

    return {
      'totalDocuments': _documents.length,
      'blockchainVerified': blockchainVerified,
      'regularDocuments': _documents.length - blockchainVerified,
      'totalSizeKB': totalSize,
      'recentDocuments': _documents.where((doc) {
        final now = DateTime.now();
        final daysDiff = now.difference(doc.createdAt).inDays;
        return daysDiff <= 7;
      }).length,
    };
  }
}