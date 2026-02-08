import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import '../config/app_config.dart';
import 'package:flutter/foundation.dart';
import 'pdf_download_service_mobile.dart';

class ComprehensiveLegalService {
  static const String baseUrl = AppConfig.apiBaseUrl;

  /// Analyze document with comprehensive legal analysis
  /// Returns summary for chat + full data for PDF report
  static Future<ComprehensiveAnalysisResult> analyzeDocument({
    required String extractedText,
    required String userEmail,
    String documentTitle = "Legal Document",
  }) async {
    try {
      final url = Uri.parse('$baseUrl/api/v1/comprehensive/comprehensive-analysis');
      
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode({
          'extracted_text': extractedText,
          'user_email': userEmail,
          'document_title': documentTitle,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return ComprehensiveAnalysisResult.fromJson(data);
      } else {
        throw Exception('Analysis failed: ${response.statusCode} - ${response.body}');
      }
    } catch (e) {
      throw Exception('Failed to analyze document: $e');
    }
  }

  /// Analyze uploaded document file directly
  static Future<ComprehensiveAnalysisResult> analyzeDocumentFile({
    required Uint8List fileBytes,
    required String fileName,
    required String userEmail,
    String documentTitle = "Legal Document",
  }) async {
    try {
      final url = Uri.parse('$baseUrl/api/v1/comprehensive/analyze-document-file');
      
      var request = http.MultipartRequest('POST', url);
      
      // Add file
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          fileBytes,
          filename: fileName,
        ),
      );
      
      // Add form data
      request.fields['user_email'] = userEmail;
      request.fields['document_title'] = documentTitle;
      
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return ComprehensiveAnalysisResult.fromJson(data);
      } else {
        throw Exception('Analysis failed: ${response.statusCode} - ${response.body}');
      }
    } catch (e) {
      throw Exception('Failed to analyze document: $e');
    }
  }

  /// Generate and download PDF report
  static Future<Uint8List> generatePDFReport({
    required ComprehensiveAnalysisResult analysisResult,
    String? filename,
  }) async {
    try {
      final url = Uri.parse('$baseUrl/api/v1/comprehensive/generate-pdf-report');
      
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/pdf',
        },
        body: jsonEncode({
          'analysis_data': analysisResult.toJson(),
          'filename': filename ?? 'legal_analysis_report.pdf',
        }),
      );

      if (response.statusCode == 200) {
        return response.bodyBytes;
      } else {
        throw Exception('PDF generation failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to generate PDF: $e');
    }
  }

  /// Generate PDF from document ID (for chat context)
  Future<Map<String, dynamic>> generatePDFFromDocumentId({
    required String documentId,
    String? documentTitle,
  }) async {
    try {
      // Get the current logged-in user's email
      final user = FirebaseAuth.instance.currentUser;
      if (user == null || user.email == null) {
        throw Exception('User not authenticated');
      }
      
      final url = Uri.parse('$baseUrl/api/v1/comprehensive/generate-pdf-from-document');
      
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'document_id': documentId,
          'document_title': documentTitle,
          'user_email': user.email, // Send the logged-in user's email
        }),
      );

      if (response.statusCode == 200) {
        // Check if the response is PDF bytes or JSON
        final contentType = response.headers['content-type'] ?? '';
        
        if (contentType.contains('application/pdf')) {
          // Response is PDF bytes, save to device storage
          final pdfBytes = response.bodyBytes;
          final filename = generatePDFFileName(documentTitle);
          
          // Save PDF to device storage with notification
          await PDFDownloadService.downloadPDFToLocal(
            pdfBytes: pdfBytes,
            filename: filename,
          );
          
        print('PDF generated and saved: $filename (${pdfBytes.length} bytes)');
          
          return {
            'success': true,
            'message': 'PDF downloaded successfully',
            'filename': filename,
            'size': pdfBytes.length,
          };
        } else {
          // Response is JSON
          return jsonDecode(response.body);
        }
      } else {
        throw Exception('PDF generation failed: ${response.statusCode} - ${response.body}');
      }
    } catch (e) {
      throw Exception('Failed to generate PDF: $e');
    }
  }

  /// Generate PDF file name from document title (6 words max)
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
    
    // Join with underscores and add prefix
    String fileName = 'result_${selectedWords.join('_')}.pdf';
    
    return fileName;
  }

  /// Clean text by removing markdown formatting
  static String cleanFormattedText(String text) {
    if (text.isEmpty) return text;
    
    // Remove ** bold formatting
    String cleaned = text.replaceAll(RegExp(r'\*\*(.*?)\*\*'), r'$1');
    
    // Remove * italic formatting  
    cleaned = cleaned.replaceAll(RegExp(r'\*(.*?)\*'), r'$1');
    
    // Remove ` code formatting
    cleaned = cleaned.replaceAll(RegExp(r'`(.*?)`'), r'$1');
    
    // Remove markdown headers but keep the text
    cleaned = cleaned.replaceAll(RegExp(r'^#{1,6}\s*', multiLine: true), '');
    
    // Clean up extra whitespace
    cleaned = cleaned.replaceAll(RegExp(r'\n\s*\n'), '\n\n');
    cleaned = cleaned.trim();
    
    return cleaned;
  }
}

class ComprehensiveAnalysisResult {
  final bool success;
  final String documentSummary;  // For chat display
  final List<LegalTerm> legalTerms;  // For PDF report
  final String riskAnalysis;  // For PDF report
  final List<RiskClause> riskAnalysisStructured;  // Gemini 3 structured output
  final List<ApplicableLaw> applicableLaws;  // For PDF report
  final Map<String, dynamic> processingMetadata;
  final List<String> gemini3FeaturesUsed;  // Track Gemini 3 features
  final String? filename;
  final String? extractedText;
  final int? textLength;
  final Map<String, dynamic>? extractionInfo;
  final String? errorMessage;

  ComprehensiveAnalysisResult({
    required this.success,
    required this.documentSummary,
    required this.legalTerms,
    required this.riskAnalysis,
    required this.riskAnalysisStructured,
    required this.applicableLaws,
    required this.processingMetadata,
    required this.gemini3FeaturesUsed,
    this.filename,
    this.extractedText,
    this.textLength,
    this.extractionInfo,
    this.errorMessage,
  });

  factory ComprehensiveAnalysisResult.fromJson(Map<String, dynamic> json) {
    final metadata = json['processing_metadata'] ?? {};
    
    // Parse structured risk analysis from Gemini 3 if available
    List<RiskClause> structuredRisks = [];
    if (metadata['risk_analysis_structured'] is Map) {
      final riskData = metadata['risk_analysis_structured'] as Map<String, dynamic>;
      structuredRisks = (riskData['clauses'] as List<dynamic>?)
              ?.map((item) => RiskClause.fromJson(item))
              .toList() ??
          [];
    }
    
    return ComprehensiveAnalysisResult(
      success: json['success'] ?? false,
      documentSummary: ComprehensiveLegalService.cleanFormattedText(json['document_summary'] ?? ''),
      legalTerms: (json['legal_terms'] as List<dynamic>?)
              ?.map((item) => LegalTerm.fromJson(item))
              .toList() ??
          [],
      riskAnalysis: ComprehensiveLegalService.cleanFormattedText(json['risk_analysis'] ?? ''),
      riskAnalysisStructured: structuredRisks,
      applicableLaws: (json['applicable_laws'] as List<dynamic>?)
              ?.map((item) => ApplicableLaw.fromJson(item))
              .toList() ??
          [],
      processingMetadata: metadata,
      gemini3FeaturesUsed: (metadata['gemini_3_features_used'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      filename: json['filename'],
      extractedText: json['extracted_text'],
      textLength: json['text_length'],
      extractionInfo: json['extraction_info'],
      errorMessage: json['error_message'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'success': success,
      'document_summary': documentSummary,
      'legal_terms_and_meanings': legalTerms.map((term) => term.toJson()).toList(),
      'risk_analysis': riskAnalysis,
      'applicable_laws': applicableLaws.map((law) => law.toJson()).toList(),
      'processing_metadata': processingMetadata,
      'filename': filename,
      'extracted_text': extractedText,
      'text_length': textLength,
      'extraction_info': extractionInfo,
    };
  }

  /// Whether Gemini 3 structured risk analysis is available
  bool get hasStructuredRiskAnalysis => riskAnalysisStructured.isNotEmpty;

  /// Get overall risk level from structured analysis
  String get overallRiskLevel {
    if (riskAnalysisStructured.isEmpty) return 'unknown';
    final highRisks = riskAnalysisStructured.where((r) => r.riskLevel == 'high').length;
    final mediumRisks = riskAnalysisStructured.where((r) => r.riskLevel == 'medium').length;
    if (highRisks > 2) return 'high';
    if (highRisks > 0 || mediumRisks > 2) return 'medium';
    return 'low';
  }
}

class LegalTerm {
  final String term;
  final String definition;
  final String source;

  LegalTerm({
    required this.term,
    required this.definition,
    required this.source,
  });

  factory LegalTerm.fromJson(Map<String, dynamic> json) {
    return LegalTerm(
      term: json['term'] ?? '',
      definition: ComprehensiveLegalService.cleanFormattedText(json['definition'] ?? ''),
      source: json['source'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'term': term,
      'definition': definition,
      'source': source,
    };
  }
}

class ApplicableLaw {
  final String law;
  final String description;

  ApplicableLaw({
    required this.law,
    required this.description,
  });

  factory ApplicableLaw.fromJson(Map<String, dynamic> json) {
    return ApplicableLaw(
      law: json['law'] ?? '',
      description: ComprehensiveLegalService.cleanFormattedText(json['description'] ?? ''),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'law': law,
      'description': description,
    };
  }
}

/// Structured risk clause from Gemini 3 structured output
class RiskClause {
  final String clause;
  final String riskLevel;
  final String explanation;
  final String recommendation;

  RiskClause({
    required this.clause,
    required this.riskLevel,
    required this.explanation,
    required this.recommendation,
  });

  factory RiskClause.fromJson(Map<String, dynamic> json) {
    return RiskClause(
      clause: json['clause'] ?? '',
      riskLevel: json['risk_level'] ?? 'unknown',
      explanation: json['explanation'] ?? '',
      recommendation: json['recommendation'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'clause': clause,
      'risk_level': riskLevel,
      'explanation': explanation,
      'recommendation': recommendation,
    };
  }

  /// Whether this is a high-risk clause
  bool get isHighRisk => riskLevel.toLowerCase() == 'high';

  /// Whether this is a medium-risk clause
  bool get isMediumRisk => riskLevel.toLowerCase() == 'medium';
}