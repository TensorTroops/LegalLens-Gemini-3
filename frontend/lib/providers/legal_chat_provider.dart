import 'package:flutter/foundation.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../models/chat_message.dart';
import '../config/app_config.dart';
import '../services/api_client.dart';
import '../services/comprehensive_legal_service.dart';

class LegalChatProvider with ChangeNotifier {
  final List<ChatMessage> _messages = [];
  bool _isLoading = false;
  bool _isSavingDemo = false; // New field for demo processing
  LegalDocumentResult? _lastProcessedDocument;
  ComprehensiveAnalysisResult? _lastComprehensiveAnalysis;  // New field for comprehensive analysis
  
  List<ChatMessage> get messages => _messages;
  bool get isLoading => _isLoading;
  bool get isSavingDemo => _isSavingDemo; // New getter
  LegalDocumentResult? get lastProcessedDocument => _lastProcessedDocument;
  ComprehensiveAnalysisResult? get lastComprehensiveAnalysis => _lastComprehensiveAnalysis;

  void addMessage(ChatMessage message) {
    _messages.add(message);
    notifyListeners();
  }

  void clearMessages() {
    _messages.clear();
    _lastProcessedDocument = null;
    _lastComprehensiveAnalysis = null;
    notifyListeners();
  }

  /// New method for comprehensive legal document analysis
  Future<void> processComprehensiveLegalDocument(String extractedText, String documentTitle) async {
    _isLoading = true;
    notifyListeners();

    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null || user.email == null) {
        throw Exception('User not authenticated');
      }

    print('COMPREHENSIVE: Starting comprehensive legal analysis');
      
      // Check if this is a demo user and add processing delay
      final isDemoUser = user.email == 'smp@gmail.com';
      if (isDemoUser) {
      print('🎯 DEMO MODE: Adding 15-second processing delay for demo user');
        // Wait for 15 seconds to simulate processing for demo
        await Future.delayed(const Duration(seconds: 15));
      }
      
      // Use the new comprehensive legal service
      final analysisResult = await ComprehensiveLegalService.analyzeDocument(
        extractedText: extractedText,
        userEmail: user.email!,
        documentTitle: documentTitle,
      );

      // Store the comprehensive analysis result
      _lastComprehensiveAnalysis = analysisResult;

      // Add only the summary to chat (not the full analysis)
      final summaryMessage = ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        message: _formatComprehensiveSummaryResponse(analysisResult),
        timestamp: DateTime.now(),
        isUser: false,
        messageType: 'comprehensive_analysis',
        metadata: {
          'hasFullReport': true,
          'documentTitle': documentTitle,
          'documentId': DateTime.now().millisecondsSinceEpoch.toString(), // Generate unique ID
          'analysisData': analysisResult.toJson(),
        },
      );

      addMessage(summaryMessage);
    print('COMPREHENSIVE: Analysis completed and summary added to chat');

    } catch (e) {
    print('Error in comprehensive analysis: $e');
      addMessage(ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        message: 'Failed to analyze document: ${e.toString()}',
        timestamp: DateTime.now(),
        isUser: false,
        messageType: 'error',
      ));
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  String _formatComprehensiveSummaryResponse(ComprehensiveAnalysisResult result) {
    return '''**Document Analysis Complete**

${result.documentSummary}

**Quick Stats:**
• Legal Terms Identified: ${result.legalTerms.length}
• Risk Assessment: ${_extractRiskLevel(result.riskAnalysis)}
• Applicable Laws: ${result.applicableLaws.length}

*Complete analysis report with detailed terms, risk analysis, and applicable laws is available for download.*''';
  }

  String _extractRiskLevel(String riskAnalysis) {
    if (riskAnalysis.contains('SAFE TO SIGN')) return 'Low Risk';
    if (riskAnalysis.contains('MODERATE RISKS')) return 'Moderate Risk';
    if (riskAnalysis.contains('HIGH RISK')) return 'High Risk';
    if (riskAnalysis.contains('SEVERE FINANCIAL RISK')) return 'Severe Risk';
    return 'Assessment Available';
  }

  Future<void> processLegalDocument(String extractedText, String documentTitle) async {
    _isLoading = true;
    notifyListeners();

    try {
      // Debug: Check Firebase Auth initialization
    print('DEBUG: Checking Firebase Auth state...');
    print('Firebase App initialized: ${Firebase.apps.isNotEmpty}');
      
      // Get current user from Firebase Auth directly
      final user = FirebaseAuth.instance.currentUser;
      
      if (user == null) {
        throw Exception('❌ No user is currently signed in. Please sign in first.');
      }
      
      if (user.email == null || user.email!.isEmpty) {
        throw Exception('❌ User email is not available. Please check your account.');
      }

    print('✅ Processing document for user: ${user.email}');
    print('🚀 FLUTTER: Using MCP endpoint: ${AppConfig.mcpProcessText}');

      // Use MCP server for comprehensive processing
      final response = await http.post(
        Uri.parse(AppConfig.mcpProcessText),
        headers: {
          'Content-Type': 'application/json',
        },
        body: json.encode({
          'text': extractedText,
          'user_email': user.email!,
          'intent': 'comprehensive_processing',
        }),
      ).timeout(const Duration(minutes: 2));

      if (response.statusCode == 200) {
        final responseData = json.decode(response.body);
      print('🔍 DEBUG: MCP Response received from: ${responseData['source']}');
        
        // Parse MCP response data
        final data = responseData['data'];
        final originalText = data['original_text'] ?? '';
        final simplifiedText = data['simplified_text'] ?? '';
        final enhancedTerms = List<Map<String, dynamic>>.from(data['enhanced_terms'] ?? []);
        final processingStats = data['processing_stats'] ?? {};
        
        // Store the processed document result
        _lastProcessedDocument = LegalDocumentResult(
          originalText: originalText,
          simplifiedText: simplifiedText,
          enhancedTerms: enhancedTerms,
          processingStats: processingStats,
        );
        
        // Format the response message like the original
        String formattedMessage = _formatMCPResponse(data);
        
        addMessage(ChatMessage(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          message: formattedMessage,
          timestamp: DateTime.now(),
          isUser: false,
          messageType: 'document_result',
        ));
      } else {
      print('🔍 DEBUG: Response status: ${response.statusCode}');
      print('🔍 DEBUG: Response body: ${response.body}');
        throw Exception('Failed to process document via MCP: ${response.statusCode}');
      }
    } catch (e) {
    print('❌ Error processing document via MCP: $e');
      
      // Add error message
      addMessage(ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        message: 'Sorry, I encountered an error while processing your document via MCP:\n${e.toString()}',
        timestamp: DateTime.now(),
        isUser: false,
        messageType: 'error',
      ));
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> sendMessage(String text) async {
    // Add user message
    addMessage(ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      message: text,
      timestamp: DateTime.now(),
      isUser: true,
    ));

    _isLoading = true;
    notifyListeners();

    try {
      // Get current user from Firebase Auth directly
      final user = FirebaseAuth.instance.currentUser;
      
      if (user == null) {
        throw Exception('❌ No user is currently signed in. Please sign in first.');
      }
      
      if (user.email == null || user.email!.isEmpty) {
        throw Exception('❌ User email is not available. Please check your account.');
      }

    print('Sending message for user: ${user.email}');
    print('FLUTTER: Using MCP endpoint for intelligent chat');

      // Determine intent based on context and question
      String intent = _determineQuestionIntent(text);
      String aiResponse = '';
      
      if (intent == 'greeting' || intent == 'general_chat') {
        // Handle conversational responses locally
        aiResponse = _generateConversationalResponse(text, intent);
        
        addMessage(ChatMessage(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          message: aiResponse,
          timestamp: DateTime.now(),
          isUser: false,
          messageType: 'chat_response',
        ));
      } else {
        // Call MCP server for legal queries and document questions
        final response = await http.post(
          Uri.parse(AppConfig.mcpProcessText),
          headers: {
            'Content-Type': 'application/json',
          },
          body: json.encode({
            'text': text,
            'user_email': user.email!,
            'intent': intent,
          }),
        ).timeout(const Duration(seconds: 30));

        if (response.statusCode == 200) {
          final responseData = json.decode(response.body);
        print('🔍 DEBUG: MCP Chat Response received');
          
          if (responseData['success'] == true) {
            final data = responseData['data'];
            if (intent == 'legal_query') {
              aiResponse = data['response'] ?? 'I apologize, but I couldn\'t generate a response to your question.';
            } else {
              aiResponse = _formatMCPChatResponse(data);
            }
          } else {
            aiResponse = 'I apologize, but I encountered an issue processing your question. Please try again.';
          }
          
          addMessage(ChatMessage(
            id: DateTime.now().millisecondsSinceEpoch.toString(),
            message: aiResponse,
            timestamp: DateTime.now(),
            isUser: false,
            messageType: 'chat_response',
          ));
        } else {
        print('🔍 DEBUG: MCP Response status: ${response.statusCode}');
          throw Exception('Failed to get response from MCP server: ${response.statusCode}');
        }
      }
    } catch (e) {
    print('❌ Error in sendMessage: $e');
      
      // Fallback to intelligent static response
      String fallbackResponse = _generateIntelligentResponse(text);
      
      addMessage(ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        message: fallbackResponse,
        timestamp: DateTime.now(),
        isUser: false,
        messageType: 'chat_response',
      ));
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  String _determineQuestionIntent(String text) {
    final question = text.toLowerCase().trim();
    
    // If user has uploaded a document, questions are about the document
    if (_lastProcessedDocument != null) {
      return 'document_question';
    }
    
    // Handle greetings and casual conversation - don't send to MCP
    if (_isGreetingOrCasual(question)) {
      return 'greeting';
    }
    
    // Check for definition requests (what is, define, explain)
    if (question.startsWith('what is ') || question.startsWith('define ') || 
        question.startsWith('explain ') || question.contains('definition of')) {
      return 'legal_query';
    }
    
    // Check for specific legal topics that need specialized handling
    if (question.contains('contract') || question.contains('agreement') || 
        question.contains('law') || question.contains('legal') ||
        question.contains('rights') || question.contains('liability') ||
        question.contains('nda') || question.contains('employment')) {
      return 'legal_query';
    }
    
    // For general conversation, handle locally
    return 'general_chat';
  }

  bool _isGreetingOrCasual(String question) {
    final greetings = [
      'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
      'how are you', 'thanks', 'thank you', 'bye', 'goodbye', 'ok', 'okay',
      'yes', 'no', 'sure', 'alright', 'cool', 'great', 'awesome'
    ];
    
    // Check if the entire message is just a greeting
    if (greetings.contains(question)) {
      return true;
    }
    
    // Check if message starts with common greetings
    for (String greeting in ['hello', 'hi', 'hey']) {
      if (question.startsWith(greeting) && question.length <= greeting.length + 10) {
        return true;
      }
    }
    
    return false;
  }

  String _formatMCPChatResponse(Map<String, dynamic> data) {
    // This can be enhanced based on different response types
    if (data.containsKey('response')) {
      return data['response'].toString();
    }
    
    return 'I received your question and processed it successfully.';
  }

  String _generateConversationalResponse(String text, String intent) {
    final question = text.toLowerCase().trim();
    
    // Greetings
    if (intent == 'greeting') {
      if (question.contains('hello') || question.contains('hi') || question.contains('hey')) {
        return 'Hello! I\'m your AI Legal Assistant. How can I help you today?\n\nI can help you with:\n• Legal term definitions\n• Document analysis\n• Contract explanations\n• General legal questions\n\nJust ask me anything like "What is a contract?" or upload a document!';
      }
      
      if (question.contains('good morning')) {
        return 'Good morning! Ready to help you with your legal questions today. What would you like to know?';
      }
      
      if (question.contains('good afternoon')) {
        return 'Good afternoon! I\'m here to assist you with legal matters. How can I help?';
      }
      
      if (question.contains('good evening')) {
        return 'Good evening! How can I assist you with your legal questions tonight?';
      }
      
      if (question.contains('thank')) {
        return 'You\'re very welcome! Feel free to ask me anything else about legal matters.';
      }
      
      if (question.contains('bye') || question.contains('goodbye')) {
        return 'Goodbye! Feel free to come back anytime you need legal assistance. Have a great day!';
      }
    }
    
    // General chat responses
    if (intent == 'general_chat') {
      if (question.contains('how are you')) {
        return 'I\'m doing great, thank you for asking! I\'m here and ready to help you with legal questions. What can I assist you with?';
      }
      
      if (question.contains('help')) {
        return 'I\'m here to help! Here\'s what I can do:\n\n• Legal Definitions: Ask "What is [legal term]?"\n• Document Analysis: Upload a document and ask questions\n• Legal Guidance: General legal information\n• Term Lookup: Explain complex legal language\n\nWhat would you like to know?';
      }
      
      // Default friendly response
      return 'I understand! I\'m your AI Legal Assistant. While I love chatting, I\'m specially designed to help with legal questions.\n\nTry asking:\n• "What is a contract?"\n• "Explain intellectual property"\n• Or upload a legal document!\n\nHow can I assist you with legal matters?';
    }
    
    return 'I\'m here to help with legal questions. What would you like to know?';
  }

  String _generateIntelligentResponse(String userQuestion) {
    final question = userQuestion.toLowerCase();
    
    // Check if user has uploaded a document
    if (_lastProcessedDocument != null) {
      return _generateDocumentContextResponse(userQuestion);
    }
    
    // Handle contract/agreement questions
    if (question.contains('contract') || question.contains('agreement')) {
      return 'About Contracts:\n\nA contract is a legally binding agreement between parties. Key elements include:\n\n• <b>Offer</b>: <u>One party proposes terms</u>\n• <b>Acceptance</b>: <u>The other party agrees to those terms</u>\n• <b>Consideration</b>: <u>Something of value exchanged</u>\n• <b>Capacity</b>: <u>Parties must be legally able to contract</u>\n\nUpload a contract document for specific analysis!';
    }
    
    // Handle legal/law questions
    if (question.contains('law') || question.contains('legal')) {
      return 'Legal Information:\n\nI\'m here to help you understand legal concepts and analyze documents. I can:\n\n• Simplify complex legal language\n• Explain legal terms and concepts\n• Analyze uploaded documents\n• Answer questions about legal topics\n\nImportant: This is for informational purposes only and does not constitute legal advice.';
    }
    
    // Handle rights/liability questions
    if (question.contains('rights') || question.contains('liability')) {
      return 'About Rights & Liability:\n\nLegal rights and liabilities vary by situation and jurisdiction. Common concepts include:\n\n• <b>Rights</b>: <u>Legal entitlements or privileges</u>\n• <b>Liability</b>: <u>Legal responsibility for damages or obligations</u>\n• <b>Breach</b>: <u>Failure to fulfill legal obligations</u>\n\nUpload a document to get specific analysis about rights and liabilities mentioned in it.';
    }
    
    // Handle upload questions
    if (question.contains('upload') || question.contains('document')) {
      return 'Document Upload:\n\nTo upload a document:\n\n1. Click the upload button below\n2. Select your PDF or image file\n3. I\'ll extract and analyze the text\n4. Ask me questions about the document!\n\nSupported formats: PDF, PNG, JPG, JPEG';
    }
    
    // Handle NDA questions
    if (question.contains('nda') || question.contains('non-disclosure') || question.contains('confidentiality')) {
      return 'Non-Disclosure Agreements (NDAs):\n\nAn NDA is a legal contract that creates confidential relationships. Key aspects:\n\n• <b>Confidential Information</b>: <u>What information must be kept secret</u>\n• <b>Parties</b>: <u>Who is sharing and receiving information</u>\n• <b>Duration</b>: <u>How long the confidentiality lasts</u>\n• <b>Exceptions</b>: <u>What information can be disclosed</u>\n\nUpload an NDA for detailed analysis!';
    }
    
    // Handle employment law questions
    if (question.contains('employment') || question.contains('job') || question.contains('workplace')) {
      return 'Employment Law:\n\nEmployment law governs workplace relationships. Common areas include:\n\n• <b>Employment Contracts</b>: <u>Terms of employment</u>\n• <b>Wages & Hours</b>: <u>Pay and working time requirements</u>\n• <b>Discrimination</b>: <u>Protection from unfair treatment</u>\n• <b>Termination</b>: <u>How employment can end</u>\n\nUpload employment documents for specific analysis!';
    }
    
    // Default intelligent response
    return 'Legal Assistant:\n\nI understand you\'re asking about "$userQuestion". I\'m here to help with legal concepts and document analysis.\n\nHow I can help:\n• Answer general legal questions\n• Analyze uploaded documents\n• Explain legal terms and concepts\n• Simplify complex legal language\n\nFor specific analysis, try uploading a legal document!\n\nNote: This is informational only, not legal advice.';
  }


  String _formatMCPResponse(Map<String, dynamic> data) {
  final enhancedTerms = List<Map<String, dynamic>>.from(data['enhanced_terms'] ?? []);
  final processingStats = data['processing_stats'] ?? {};
  final simplifiedText = data['simplified_text'] ?? '';
  final originalText = data['original_text'] ?? '';

  String message = 'Document Analysis Complete\n\n';

  // Simplified text
  if (simplifiedText.isNotEmpty && simplifiedText != originalText) {
    message += 'Simplified Version:\n$simplifiedText\n\n';
  }

  // Key terms
  if (enhancedTerms.isNotEmpty) {
    message += '\n\n------Key Legal Terms------\n';
    for (var term in enhancedTerms) {
      final termName = term['term']?.toString() ?? '';
      final definition = term['definition'] ?? '';
      if (termName.isNotEmpty && definition.isNotEmpty) {
        message += '\n<b>$termName</b>: <u>$definition</u>\n\n'; // bold + underline
      }
    }
    message += '\n';
  }

  // Processing stats
  if (processingStats.isNotEmpty) {
    final originalWordCount = processingStats['original_word_count'] ?? 0;
    final simplifiedWordCount = processingStats['simplified_word_count'] ?? 0;
    final reductionPercentage = processingStats['reduction_percentage'] ?? 0.0;
    final totalTerms = processingStats['total_terms'] ?? 0;

    message += '\n📊 Processing Summary:\n';
    message += '\n• Original words: $originalWordCount\n';
    message += '\n• Simplified words: $simplifiedWordCount\n';
    message += '\n• Text reduced by: ${reductionPercentage.toStringAsFixed(1)}%\n';
    message += '\n• Key terms identified: $totalTerms\n\n';
  }

  message += 'Processing completed successfully! ✅';
  return message;
}

String _generateDocumentContextResponse(String userQuestion) {
  final doc = _lastProcessedDocument!;
  String response = 'Based on the document you uploaded, ';

  if (userQuestion.toLowerCase().contains('terms')) {
    response += "here are the key legal terms:\n\n";
    for (var term in doc.enhancedTerms) {
      final termName = term['term']?.toString() ?? '';
      final definition = term['definition'] ?? '';
      if (termName.isNotEmpty && definition.isNotEmpty) {
        response += '• <b>$termName</b>: <u>$definition</u>\n\n'; // bold + underline
      }
    }
    response += '\n';
  } else {
    response += "I can help you understand it better.\n";
  }

  return response;
}


  Future<void> saveSummary() async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null || user.email == null) {
        throw Exception('User not authenticated');
      }

    print('🔍 DEBUG: Saving summary for user: ${user.email}');

      // Check if this is a demo user
      if (user.email == 'smp@gmail.com') {
      print('🎯 DEMO MODE: Starting demo summary save with 15-second delay');
        
        // Set demo processing state
        _isSavingDemo = true;
        notifyListeners();
        
        // Add 15-second delay for demo
        await Future.delayed(const Duration(seconds: 1));
        
        // Demo complete - reset state
        _isSavingDemo = false;
        notifyListeners();
        
      print('✅ Demo summary save completed');
        return; // Exit early for demo user
      }

      // Check if we have comprehensive analysis data first
      if (_lastComprehensiveAnalysis != null) {
        return await saveComprehensiveAnalysis();
      }

      if (_lastProcessedDocument == null) {
        throw Exception('No document to save');
      }
      
      final apiClient = ApiClient();
      
      // Prepare summary data using the correct property names
      final summaryData = {
        'original_text': _lastProcessedDocument!.originalText,
        'simplified_text': _lastProcessedDocument!.simplifiedText,
        'extracted_terms': _lastProcessedDocument!.enhancedTerms,
        'processing_status': 'completed',
        'terms_count': _lastProcessedDocument!.enhancedTerms.length,
        'processing_method': 'mcp_comprehensive_processing',
        'processing_stats': _lastProcessedDocument!.processingStats,
      };

      // Call the save summary API
      final response = await apiClient.saveSummary(
        userEmail: user.email!,
        documentTitle: 'Legal Document Summary',
        summaryData: summaryData,
      );

      if (response['success'] == true) {
        final documentId = response['document_id'];
      print('✅ Summary saved successfully with ID: $documentId');
      } else {
        throw Exception('Failed to save summary: ${response['message'] ?? 'Unknown error'}');
      }

    } catch (e) {
    print('❌ Error saving summary: $e');
      // Reset demo state on error
      _isSavingDemo = false;
      notifyListeners();
      throw Exception('Error saving summary: ${e.toString()}');
    }
  }

  Future<void> saveComprehensiveAnalysis() async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null || user.email == null) {
        throw Exception('User not authenticated');
      }

    print('🔍 DEBUG: Saving comprehensive analysis for user: ${user.email}');

      // Check if this is a demo user
      if (user.email == 'smp@gmail.com') {
      print('🎯 DEMO MODE: Starting demo comprehensive analysis save with 15-second delay');
        
        // Set demo processing state
        _isSavingDemo = true;
        notifyListeners();

        // Add 8-second delay for demo
        await Future.delayed(const Duration(seconds: 8));
        
        // Demo complete - reset state
        _isSavingDemo = false;
        notifyListeners();
        
      print('✅ Demo comprehensive analysis save completed');
        return; // Exit early for demo user
      }

      if (_lastComprehensiveAnalysis == null) {
        throw Exception('No comprehensive analysis to save');
      }
      
      final apiClient = ApiClient();
      
      // Prepare comprehensive analysis data for Firestore
      final summaryData = {
        'document_summary': _lastComprehensiveAnalysis!.documentSummary,
        'legal_terms': _lastComprehensiveAnalysis!.legalTerms,
        'risk_analysis': _lastComprehensiveAnalysis!.riskAnalysis,
        'applicable_laws': _lastComprehensiveAnalysis!.applicableLaws,
        'processing_status': 'completed',
        'analysis_type': 'comprehensive_legal_analysis',
        'created_at': DateTime.now().toIso8601String(),
      };

      // Call the save summary API
      final response = await apiClient.saveSummary(
        userEmail: user.email!,
        documentTitle: 'Comprehensive Legal Analysis',
        summaryData: summaryData,
      );

      if (response['success'] == true) {
        final documentId = response['document_id'];
      print('✅ Comprehensive analysis saved successfully with ID: $documentId');
      } else {
        throw Exception('Failed to save analysis: ${response['message'] ?? 'Unknown error'}');
      }

    } catch (e) {
    print('❌ Error saving comprehensive analysis: $e');
      // Reset demo state on error
      _isSavingDemo = false;
      notifyListeners();
      throw Exception('Error saving analysis: ${e.toString()}');
    }
  }
}

// Enhanced result class for MCP responses
class LegalDocumentResult {
  final String originalText;
  final String simplifiedText;
  final List<Map<String, dynamic>> enhancedTerms;
  final Map<String, dynamic> processingStats;
  
  LegalDocumentResult({
    required this.originalText,
    required this.simplifiedText,
    required this.enhancedTerms,
    required this.processingStats,
  });
}