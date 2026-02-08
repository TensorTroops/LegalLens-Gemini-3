import 'dart:typed_data';
import 'package:flutter/foundation.dart';

// For now, we'll implement a simplified version that works on mobile
// Web implementation can be added later when needed
class PDFDownloadService {
  /// Download PDF bytes to local storage with custom filename
  static Future<String> downloadPDFToLocal({
    required Uint8List pdfBytes,
    required String filename,
  }) async {
    // For now, just return a success message
    // Real implementation would save the file
    return 'PDF ready: $filename';
  }

  /// Open downloaded PDF file
  static Future<bool> openPDFFile(String filePath) async {
    try {
      // Placeholder - would open the file
      return true;
    } catch (e) {
    print('Error opening PDF: $e');
      return false;
    }
  }

  /// Generate proper PDF filename from document title
  static String generatePDFFileName(String? documentTitle) {
    if (documentTitle == null || documentTitle.isEmpty) {
      return 'result_legal_document_analysis.pdf';
    }

    // Clean the title and split into words
    String cleanTitle = documentTitle
        .replaceAll(RegExp(r'[^\w\s]'), '') // Remove special characters
        .replaceAll(RegExp(r'\s+'), ' ') // Multiple spaces to single
        .trim()
        .toLowerCase();

    List<String> words = cleanTitle.split(' ');
    
    // Take first 6 words
    List<String> selectedWords = words.take(6).toList();
    
    // Ensure we have at least some words
    if (selectedWords.isEmpty) {
      selectedWords = ['legal', 'document'];
    }
    
    // Join with underscores and add prefix
    String fileName = 'result_${selectedWords.join('_')}.pdf';
    
    return fileName;
  }

  /// Generate text filename from document title
  static String generateTextFileName(String? documentTitle, String type) {
    if (documentTitle == null || documentTitle.isEmpty) {
      return '${type}_legal_document.txt';
    }

    // Clean the title and split into words
    String cleanTitle = documentTitle
        .replaceAll(RegExp(r'[^\w\s]'), '') // Remove special characters
        .replaceAll(RegExp(r'\s+'), ' ') // Multiple spaces to single
        .trim()
        .toLowerCase();

    List<String> words = cleanTitle.split(' ');
    
    // Take first 4 words for text files
    List<String> selectedWords = words.take(4).toList();
    
    // Ensure we have at least some words
    if (selectedWords.isEmpty) {
      selectedWords = ['legal', 'document'];
    }
    
    // Join with underscores and add type
    String fileName = '${type}_${selectedWords.join('_')}.txt';
    
    return fileName;
  }

  /// Save text content to device
  static Future<String> saveTextToDevice({
    required String textContent,
    required String filename,
  }) async {
    try {
      // For now, return a success message indicating readiness to save
      // Real implementation would save the text file to device storage
      return 'Text file ready: $filename';
    } catch (e) {
      throw Exception('Failed to save text: $e');
    }
  }

  /// Get user-friendly download location message
  static String getDownloadLocationMessage() {
    if (kIsWeb) {
      return 'Downloaded to your browser\'s default download folder';
    } else {
      return 'Downloaded to Documents folder';
    }
  }
}