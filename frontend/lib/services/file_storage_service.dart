import 'dart:io';
import 'dart:typed_data';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:flutter/foundation.dart';

/// File storage service for saving files to device storage
/// Supports both Android and iOS with proper permissions
class FileStorageService {
  
  /// Get the external document path (Downloads folder for Android, Documents for iOS)
  static Future<String> getExternalDocumentPath() async {
    if (kIsWeb) {
      // Web doesn't support file system access
      throw UnsupportedError('File system access not supported on web');
    }
    
    // Check and request storage permission on Android
    if (Platform.isAndroid) {
      // For Android 11+ (API 30+), we need different permissions
      bool hasPermission = await _requestAndroidStoragePermission();
      if (!hasPermission) {
        throw Exception('Storage permission denied. Please grant storage access in app settings.');
      }
    }
    
    Directory directory;
    if (Platform.isAndroid) {
      // Try multiple Android download paths
      List<String> downloadPaths = [
        "/storage/emulated/0/Download",
        "/storage/emulated/0/Downloads", // Some devices use "Downloads"
        "/sdcard/Download",
        "/sdcard/Downloads"
      ];
      
      Directory? downloadDir;
      for (String path in downloadPaths) {
        final testDir = Directory(path);
        if (await testDir.exists()) {
          downloadDir = testDir;
        print("📁 Found Downloads directory: $path");
          break;
        }
      }
      
      if (downloadDir != null) {
        directory = downloadDir;
      } else {
        // If no Downloads folder found, use external storage
      print("📁 Downloads folder not found, using external storage");
        directory = await getExternalStorageDirectory() ?? 
                   await getApplicationDocumentsDirectory();
      }
    } else {
      // Use Documents directory on iOS and other platforms
      directory = await getApplicationDocumentsDirectory();
    }

    final exPath = directory.path;
  print("📁 Final Storage Path: $exPath");
    
    // Create directory if it doesn't exist
    await Directory(exPath).create(recursive: true);
    
    // Verify the directory is writable
    try {
      final testFile = File('${exPath}/test_write_permissions.tmp');
      await testFile.writeAsString('test');
      await testFile.delete();
    print("📁 Write permissions verified for: $exPath");
    } catch (e) {
    print("❌ Write permission test failed: $e");
      // Fallback to app documents directory
      directory = await getApplicationDocumentsDirectory();
      final fallbackPath = directory.path;
    print("📁 Using fallback path: $fallbackPath");
      return fallbackPath;
    }
    return exPath;
  }

  /// Request Android storage permissions (handles different Android versions)
  static Future<bool> _requestAndroidStoragePermission() async {
    if (!Platform.isAndroid) return true;
    
    try {
      // Check Android version and request appropriate permissions
      var status = await Permission.storage.status;
      
    print("🔐 Current storage permission status: $status");
      
      if (!status.isGranted) {
      print("🔐 Requesting storage permission...");
        status = await Permission.storage.request();
      print("🔐 Permission request result: $status");
      }
      
      // For Android 11+, also check manage external storage
      if (Platform.isAndroid) {
        var manageStatus = await Permission.manageExternalStorage.status;
      print("🔐 Manage external storage status: $manageStatus");
        
        if (!manageStatus.isGranted) {
        print("🔐 Requesting manage external storage permission...");
          manageStatus = await Permission.manageExternalStorage.request();
        print("🔐 Manage external storage result: $manageStatus");
        }
        
        // Return true if either permission is granted
        return status.isGranted || manageStatus.isGranted;
      }
      
      return status.isGranted;
    } catch (e) {
    print("❌ Error requesting permissions: $e");
      return false;
    }
  }

  /// Get the local storage path
  static Future<String> get _localPath async {
    final String directory = await getExternalDocumentPath();
    return directory;
  }

  /// Save text data to a file
  static Future<File> saveTextFile(String content, String fileName) async {
    final path = await _localPath;
    File file = File('$path/$fileName');
  print("💾 Saving text file: $fileName");
    
    // Write the text data to the file
    return file.writeAsString(content);
  }

  /// Save binary data (like PDF) to a file
  static Future<File> saveBinaryFile(Uint8List bytes, String fileName) async {
    final path = await _localPath;
    File file = File('$path/$fileName');
  print("💾 Saving binary file: $fileName (${bytes.length} bytes)");
    
    // Write the binary data to the file
    return file.writeAsBytes(bytes);
  }

  /// Check if storage permission is granted (Android only)
  static Future<bool> isStoragePermissionGranted() async {
    if (kIsWeb || !Platform.isAndroid) {
      return true; // No permission needed on web or iOS
    }
    
    final status = await Permission.storage.status;
    final manageStatus = await Permission.manageExternalStorage.status;
    return status.isGranted || manageStatus.isGranted;
  }

  /// Request storage permission (Android only)
  static Future<bool> requestStoragePermission() async {
    if (kIsWeb || !Platform.isAndroid) {
      return true; // No permission needed on web or iOS
    }
    
    return await _requestAndroidStoragePermission();
  }

  /// Get a human-readable path for display
  static Future<String> getDisplayPath(String fileName) async {
    try {
      if (Platform.isAndroid) {
        return "Downloads/$fileName";
      } else {
        return "Documents/$fileName";
      }
    } catch (e) {
      return fileName;
    }
  }
}