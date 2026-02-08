import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'package:url_launcher/url_launcher.dart';
import 'notification_service.dart';

class PDFDownloadService {
  /// Download PDF bytes to local storage with custom filename
  static Future<String> downloadPDFToLocal({
    required Uint8List pdfBytes,
    required String filename,
  }) async {
    try {
      if (kIsWeb) {
        // For web, we'll use a different approach
        throw UnimplementedError('Web downloads not implemented in mobile version');
      } else {
        // Mobile/Desktop download
        final filePath = await _downloadMobilePDF(pdfBytes, filename);
        
        // Show notification after successful download
        await _showDownloadNotification(filename, filePath, pdfBytes.length);
        
        return filePath;
      }
    } catch (e) {
      // Show error notification
      await NotificationService.showErrorNotification(
        title: 'Download Failed',
        message: 'Failed to download PDF: $e',
      );
      throw Exception('Failed to download PDF: $e');
    }
  }

  /// Download PDF on mobile/desktop platform
  static Future<String> _downloadMobilePDF(Uint8List pdfBytes, String filename) async {
    late Directory directory;
    String targetPath = '';
    
    if (Platform.isAndroid) {
      try {
        // Use public Downloads directory for better accessibility
        const downloadsPath = '/storage/emulated/0/Download';
        final downloadsDir = Directory(downloadsPath);
        
        // Check if Downloads directory exists
        if (await downloadsDir.exists()) {
          directory = downloadsDir;
          targetPath = '$downloadsPath/$filename';
        print('📁 Android: Saving to public Downloads: $targetPath');
        } else {
          throw Exception('Downloads directory not available');
        }
      } catch (e) {
      print('❌ Public Downloads failed, trying external storage: $e');
        // Fall back to external storage directory
        try {
          final externalDir = await getExternalStorageDirectory();
          if (externalDir != null) {
            // Create a LegalLens folder in external storage
            final legalLensDir = Directory('${externalDir.path}/LegalLens');
            await legalLensDir.create(recursive: true);
            directory = legalLensDir;
            targetPath = '${legalLensDir.path}/$filename';
            
          print('📁 Android fallback: Saving to external storage: $targetPath');
          } else {
            throw Exception('External storage not available');
          }
        } catch (e2) {
        print('❌ External storage also failed, using app documents: $e2');
          // Final fallback to application documents directory
          directory = await getApplicationDocumentsDirectory();
          targetPath = '${directory.path}/$filename';
        print('📁 Android final fallback: Saving to app documents: $targetPath');
        }
      }
    } else {
      // For iOS and other platforms, use application documents directory
      directory = await getApplicationDocumentsDirectory();
      targetPath = '${directory.path}/$filename';
    print('📁 iOS: Saving to app documents: $targetPath');
    }
    
    final file = File(targetPath);
    await file.writeAsBytes(pdfBytes);
    
    // Verify file was created
    final exists = await file.exists();
    final size = exists ? await file.length() : 0;
  print('✅ File created: $exists, Size: $size bytes at $targetPath');
    
    return targetPath;
  }

  /// Show download notification with file details
  static Future<void> _showDownloadNotification(String filename, String filePath, int fileSize) async {
    final fileSizeKB = (fileSize / 1024).round();
    final fileSizeMB = (fileSize / (1024 * 1024)).round();
    
    String sizeString;
    if (fileSizeMB > 0) {
      sizeString = '${fileSizeMB} MB';
    } else {
      sizeString = '${fileSizeKB} KB';
    }

    await NotificationService.showDownloadNotification(
      fileName: filename,
      filePath: filePath,
      fileSize: sizeString,
    );
  }

  /// Open downloaded PDF file
  static Future<bool> openPDFFile(String filePath) async {
    try {
      if (kIsWeb) {
        // On web, the file is automatically downloaded to browser downloads
        return true;
      } else {
        // On mobile/desktop, try to open the file
        final uri = Uri.file(filePath);
        return await launchUrl(uri);
      }
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

  /// Get user-friendly download location message
  static String getDownloadLocationMessage() {
    if (kIsWeb) {
      return 'Downloaded to your browser\'s default download folder';
    } else if (Platform.isAndroid) {
      return 'Downloaded to LegalLens folder in device storage';
    } else if (Platform.isIOS) {
      return 'Downloaded to app documents';
    } else {
      return 'Downloaded to Documents folder';
    }
  }
}