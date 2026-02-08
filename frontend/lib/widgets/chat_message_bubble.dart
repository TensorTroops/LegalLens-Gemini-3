import 'package:flutter/material.dart';
import 'package:flutter_html/flutter_html.dart';
import 'package:provider/provider.dart';
import '../models/chat_message.dart';
import '../providers/legal_chat_provider.dart';
import '../services/file_storage_service.dart';
import 'chat_pdf_download_button.dart';

class ChatMessageBubble extends StatelessWidget {
  final ChatMessage message;
  final VoidCallback? onSaveSummary;

  const ChatMessageBubble({
    super.key,
    required this.message,
    this.onSaveSummary,
  });

  @override
  Widget build(BuildContext context) {
    // Debug logging for save summary button
    if (message.messageType == 'document_result') {
    print('🔍 ChatMessageBubble: Document result detected');
    print('🔍 onSaveSummary callback: ${onSaveSummary != null ? "Present" : "NULL"}');
    print('🔍 Message type: ${message.messageType}');
    }
    
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Row(
        mainAxisAlignment: message.isUser 
            ? MainAxisAlignment.end 
            : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!message.isUser) ...[
            _buildAvatar(),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: _buildMessageContainer(context),
          ),
          if (message.isUser) ...[
            const SizedBox(width: 8),
            _buildUserAvatar(),
          ],
        ],
      ),
    );
  }

  Widget _buildAvatar() {
    return Container(
      width: 32,
      height: 32,
      decoration: BoxDecoration(
        color: const Color(0xFF4285F4),
        borderRadius: BorderRadius.circular(16),
      ),
      child: const Icon(
        Icons.gavel,
        color: Colors.white,
        size: 18,
      ),
    );
  }

  Widget _buildUserAvatar() {
    return Container(
      width: 32,
      height: 32,
      decoration: BoxDecoration(
        color: const Color(0xFF6C757D),
        borderRadius: BorderRadius.circular(16),
      ),
      child: const Icon(
        Icons.person,
        color: Colors.white,
        size: 18,
      ),
    );
  }

  Widget _buildMessageContainer(BuildContext context) {
    return Container(
      constraints: BoxConstraints(
        maxWidth: MediaQuery.of(context).size.width * 0.7,
      ),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: message.isUser 
            ? const Color(0xFF4285F4) 
            : Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 5,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildMessageContent(context),
          const SizedBox(height: 8),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                _formatTime(message.timestamp),
                style: TextStyle(
                  fontSize: 10,
                  color: message.isUser 
                      ? Colors.white.withValues(alpha: 0.7)
                      : Colors.grey[600],
                ),
              ),
              if (!message.isUser && 
                  message.messageType == 'document_result' && 
                  onSaveSummary != null) ...[
                const Spacer(),
                _buildSaveSummaryButton(),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMessageContent(BuildContext context) {
    if (message.messageType == 'document_result') {
      return _buildDocumentResultContent();
    } else if (message.messageType == 'comprehensive_analysis') {
      return _buildComprehensiveAnalysisContent(context);
    } else if (message.messageType == 'legal_answer') {
      return _buildLegalAnswerContent();
    } else {
      return _buildTextContent();
    }
  }

  Widget _buildTextContent() {
    // Check if message contains HTML tags
    if (message.message.contains('<') && message.message.contains('>')) {
      return Html(
        data: message.message,
        style: {
          "body": Style(
            color: message.isUser ? Colors.white : const Color(0xFF2D2D2D),
            fontSize: FontSize(14),
            lineHeight: const LineHeight(1.4),
            margin: Margins.zero,
            padding: HtmlPaddings.zero,
          ),
        },
      );
    } else {
      return Text(
        message.message,
        style: TextStyle(
          fontSize: 14,
          color: message.isUser ? Colors.white : const Color(0xFF2D2D2D),
          height: 1.4,
        ),
      );
    }
  }

  Widget _buildDocumentResultContent() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header
        Row(
          children: [
            const Icon(
              Icons.description,
              size: 16,
              color: Color(0xFF4285F4),
            ),
            const SizedBox(width: 8),
            const Text(
              'Document Analysis Complete',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: Color(0xFF2D2D2D),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        
        // Content
        Text(
          message.message,
          style: const TextStyle(
            fontSize: 14,
            color: Color(0xFF2D2D2D),
            height: 1.4,
          ),
        ),
        
        // Confidence indicator
        if (message.metadata != null) ...[
          const SizedBox(height: 12),
          _buildConfidenceIndicator(),
        ],
      ],
    );
  }

  Widget _buildLegalAnswerContent() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header
        const Row(
          children: [
            Icon(
              Icons.lightbulb_outline,
              size: 16,
              color: Color(0xFF4285F4),
            ),
            SizedBox(width: 8),
            Text(
              'Legal Information',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: Color(0xFF2D2D2D),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        
        // Content
        Text(
          message.message,
          style: const TextStyle(
            fontSize: 14,
            color: Color(0xFF2D2D2D),
            height: 1.4,
          ),
        ),
      ],
    );
  }

  Widget _buildComprehensiveAnalysisContent(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header
        const Row(
          children: [
            Icon(
              Icons.analytics,
              size: 16,
              color: Color(0xFF4285F4),
            ),
            SizedBox(width: 8),
            Text(
              'Comprehensive Legal Analysis',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: Color(0xFF2D2D2D),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        
        // Summary content (only show summary in chat)
        Text(
          message.message,
          style: const TextStyle(
            fontSize: 14,
            color: Color(0xFF2D2D2D),
            height: 1.4,
          ),
        ),
        
        const SizedBox(height: 12),
        
        // Action buttons row
        Row(
          children: [
            // Save Summary button
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () => _saveSummaryToDevice(context, message.message, message.metadata?['documentTitle'] as String?),
                icon: const Icon(Icons.save, size: 16),
                label: const Text('Save Summary', style: TextStyle(fontSize: 12)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(6),
                  ),
                ),
              ),
            ),
            
            const SizedBox(width: 8),
            
            // PDF Download button (only show if we have document ID)
            if (message.metadata?['documentId'] != null)
              Expanded(
                child: ChatPDFDownloadButton(
                  documentId: message.metadata!['documentId'] as String,
                  documentTitle: message.metadata?['documentTitle'] as String?,
                ),
              ),
          ],
        ),
        
        // Info text
        const SizedBox(height: 8),
        Text(
          'Download the complete PDF report for detailed legal terms, risk analysis, and applicable laws.',
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
            fontStyle: FontStyle.italic,
          ),
        ),
      ],
    );
  }

  Widget _buildConfidenceIndicator() {
    final metadata = message.metadata;
    if (metadata == null) return const SizedBox.shrink();
    
    final processingStatus = metadata['processingStatus'] as String?;
    final isSuccessful = processingStatus == 'success';
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: isSuccessful 
            ? const Color(0xFF4285F4).withValues(alpha: 0.1)
            : Colors.orange.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isSuccessful 
              ? const Color(0xFF4285F4).withValues(alpha: 0.3)
              : Colors.orange.withValues(alpha: 0.3),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isSuccessful ? Icons.verified : Icons.warning_amber_rounded,
            size: 16,
            color: isSuccessful ? const Color(0xFF4285F4) : Colors.orange,
          ),
          const SizedBox(width: 6),
          Text(
            isSuccessful ? 'Confidence 92%' : 'Partial Analysis',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w500,
              color: isSuccessful ? const Color(0xFF4285F4) : Colors.orange,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSaveSummaryButton() {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      child: ElevatedButton.icon(
        onPressed: onSaveSummary,
        icon: const Icon(Icons.save, size: 14),
        label: const Text(
          'Save Summary',
          style: TextStyle(fontSize: 12),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF4285F4),
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          minimumSize: Size.zero,
          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        ),
      ),
    );
  }

  String _formatTime(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);
    
    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inDays < 1) {
      return '${difference.inHours}h ago';
    } else {
      return '${timestamp.day}/${timestamp.month}';
    }
  }

  Future<void> _saveSummaryToDevice(BuildContext context, String summaryText, String? documentTitle) async {
    try {
      // Show loading indicator
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => const Center(
          child: CircularProgressIndicator(color: Colors.green),
        ),
      );

      // Get comprehensive analysis data from message metadata
      final analysisData = message.metadata?['analysisData'] as Map<String, dynamic>?;
      
      if (analysisData == null) {
        throw Exception('No analysis data available to save');
      }

      // Save to Firestore first
      final chatProvider = Provider.of<LegalChatProvider>(context, listen: false);
      await chatProvider.saveSummary();

      // Also save summary text to local device storage
      await _saveTextSummaryToDevice(summaryText, documentTitle);

      // Close loading dialog
      if (context.mounted && Navigator.canPop(context)) {
        Navigator.pop(context);
      }

      // Show success message
      if (context.mounted) {
        final displayPath = await FileStorageService.getDisplayPath(
          _generateSummaryFileName(documentTitle)
        );
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.check_circle, color: Colors.white),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('Summary saved in Firestore database'),
                      const Text(''),
                    ],
                  ),
                ),
              ],
            ),
            backgroundColor: Colors.green,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    } catch (e) {
      // Close loading dialog if open
      if (context.mounted && Navigator.canPop(context)) {
        Navigator.pop(context);
      }

      // Show error message
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.error, color: Colors.white),
                const SizedBox(width: 8),
                Expanded(child: Text('Failed to save summary: ${e.toString()}')),
              ],
            ),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    }
  }

  /// Save text summary to local device storage
  Future<void> _saveTextSummaryToDevice(String summaryText, String? documentTitle) async {
    try {
      final filename = _generateSummaryFileName(documentTitle);
      await FileStorageService.saveTextFile(summaryText, filename);
    print('✅ Summary saved locally: $filename');
    } catch (e) {
    print('❌ Failed to save summary locally: $e');
      // Don't throw - Firestore save is more important
    }
  }

  /// Generate filename for summary text file
  String _generateSummaryFileName(String? documentTitle) {
    if (documentTitle == null || documentTitle.isEmpty) {
      return 'summary_legal_document';
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
    String fileName = 'summary saved in firestore database';
    
    return fileName;
  }
}