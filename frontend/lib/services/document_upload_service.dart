import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import '../config/app_config.dart';

class DocumentUploadService {
  /// Pick and upload a document file using MCP server
  static Future<DocumentUploadResult> pickAndUploadDocument(String userEmail) async {
    try {
      // Request storage permission
      final permission = await Permission.storage.request();
      if (!permission.isGranted) {
        throw Exception('Storage permission is required to pick files');
      }
      
      // Pick file
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'],
        allowMultiple: false,
      );
      
      if (result == null || result.files.isEmpty) {
        throw Exception('No file selected');
      }
      
      final file = result.files.first;
      
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        throw Exception('File size must be less than 10MB');
      }
      
      // Get file bytes
      final bytes = file.bytes ?? await File(file.path!).readAsBytes();
      
      // Create multipart request to MCP server
      final uri = Uri.parse(AppConfig.mcpProcessDocument);
    print('🚀 UPLOAD SERVICE: Using MCP endpoint: $uri');
      final request = http.MultipartRequest('POST', uri);
      
      // Add form fields
      request.fields['user_email'] = userEmail;
      
      // Add file
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          bytes,
          filename: file.name,
        ),
      );
      
      // Send request
      final response = await request.send();
      final responseData = await response.stream.bytesToString();
      
      if (response.statusCode == 200) {
        final jsonData = json.decode(responseData);
        
        return DocumentUploadResult(
          success: true,
          filename: file.name,
          fileSize: file.size,
          processingData: jsonData['data'],
          processingTime: jsonData['processing_time'],
          source: jsonData['source'],
        );
      } else {
        final errorData = json.decode(responseData);
        throw Exception(errorData['detail'] ?? 'Upload failed');
      }
      
    } catch (e) {
      return DocumentUploadResult(
        success: false,
        error: e.toString(),
      );
    }
  }
  
  /// Get supported file types for display
  static List<String> getSupportedFileTypes() {
    return [
      'PDF documents (.pdf)',
      'Images (.jpg, .jpeg, .png)',
      'Graphics (.gif, .bmp, .tiff)',
    ];
  }
  
  /// Format file size for display
  static String formatFileSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}

class DocumentUploadResult {
  final bool success;
  final String? filename;
  final int? fileSize;
  final Map<String, dynamic>? processingData;
  final double? processingTime;
  final String? source;
  final String? error;
  
  const DocumentUploadResult({
    required this.success,
    this.filename,
    this.fileSize,
    this.processingData,
    this.processingTime,
    this.source,
    this.error,
  });
}

class DocumentUploadDialog extends StatefulWidget {
  final String userEmail;
  final Function(DocumentUploadResult) onUploadComplete;
  
  const DocumentUploadDialog({
    super.key,
    required this.userEmail,
    required this.onUploadComplete,
  });
  
  @override
  State<DocumentUploadDialog> createState() => _DocumentUploadDialogState();
}

class _DocumentUploadDialogState extends State<DocumentUploadDialog> {
  bool _isUploading = false;
  double _uploadProgress = 0.0;
  String _statusMessage = '';
  
  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Row(
        children: [
          Icon(Icons.upload_file, color: Color(0xFF4285F4)),
          SizedBox(width: 8),
          Expanded(
            child: Text('Upload Legal Document'),
          ),
        ],
      ),
      content: SizedBox(
        width: MediaQuery.of(context).size.width * 0.8,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (!_isUploading) ...[
              const Text(
                'Upload a legal document for AI analysis and simplification.',
                style: TextStyle(fontSize: 16),
              ),
              const SizedBox(height: 16),
              const Text(
                'Supported file types:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              ...DocumentUploadService.getSupportedFileTypes().map(
                (type) => Padding(
                  padding: const EdgeInsets.only(left: 16, bottom: 4),
                  child: Row(
                    children: [
                      const Icon(Icons.check_circle, 
                                color: Color(0xFF34A853), size: 16),
                      const SizedBox(width: 8),
                      Text(type),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFF0F7FF),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFF4285F4).withValues(alpha: 0.3)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.info_outline, color: Color(0xFF4285F4), size: 20),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Maximum file size: 10MB',
                        style: TextStyle(color: Color(0xFF4285F4)),
                      ),
                    ),
                  ],
                ),
              ),
            ] else ...[
              Column(
                children: [
                  const CircularProgressIndicator(),
                  const SizedBox(height: 16),
                  Text(
                    _statusMessage,
                    style: const TextStyle(fontSize: 16),
                    textAlign: TextAlign.center,
                  ),
                  if (_uploadProgress > 0) ...[
                    const SizedBox(height: 12),
                    LinearProgressIndicator(value: _uploadProgress),
                    const SizedBox(height: 8),
                    Text('${(_uploadProgress * 100).toInt()}% complete'),
                  ],
                ],
              ),
            ],
          ],
        ),
      ),
      actions: [
        if (!_isUploading) ...[
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton.icon(
            onPressed: _handleUpload,
            icon: const Icon(Icons.upload_file),
            label: const Text('Choose File'),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF4285F4),
              foregroundColor: Colors.white,
            ),
          ),
        ] else ...[
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
        ],
      ],
    );
  }
  
  Future<void> _handleUpload() async {
    setState(() {
      _isUploading = true;
      _statusMessage = 'Selecting file...';
    });
    
    try {
      setState(() {
        _statusMessage = 'Processing document...';
        _uploadProgress = 0.3;
      });
      
      final result = await DocumentUploadService.pickAndUploadDocument(widget.userEmail);
      
      setState(() {
        _uploadProgress = 1.0;
        _statusMessage = result.success ? 'Upload completed!' : 'Upload failed';
      });
      
      // Give user a moment to see completion
      await Future.delayed(const Duration(milliseconds: 500));
      
      if (mounted) {
        Navigator.of(context).pop();
        widget.onUploadComplete(result);
      }
      
    } catch (e) {
      setState(() {
        _statusMessage = 'Error: ${e.toString()}';
        _uploadProgress = 0.0;
      });
      
      // Reset after showing error
      await Future.delayed(const Duration(seconds: 2));
      if (mounted) {
        setState(() {
          _isUploading = false;
          _statusMessage = '';
        });
      }
    }
  }
}