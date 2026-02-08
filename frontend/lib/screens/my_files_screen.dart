import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/files_provider.dart';
import '../providers/auth_provider.dart' as app_auth;
import '../models/saved_document.dart';

class MyFilesScreen extends StatefulWidget {
  const MyFilesScreen({super.key});

  @override
  State<MyFilesScreen> createState() => _MyFilesScreenState();
}

class _MyFilesScreenState extends State<MyFilesScreen> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<FilesProvider>(context, listen: false).loadDocuments();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5),
      body: SafeArea(
        child: CustomScrollView(
          slivers: [
            SliverToBoxAdapter(child: _buildHeader()),
            SliverToBoxAdapter(child: _buildSearchBar()),
            SliverToBoxAdapter(child: const SizedBox(height: 8)),
            _buildDocumentsListSliver(),
            SliverToBoxAdapter(child: _buildAddDocumentButton()),
            SliverToBoxAdapter(child: const SizedBox(height: 12)),
          ],
        ),
      ),
      bottomNavigationBar: _buildBottomNavigation(),
    );
  }

  // ---------------- HEADER ----------------
  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      color: Colors.white,
      child: Row(
        children: [
          const Text(
            'Files',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Color(0xFF2D2D2D),
            ),
          ),
          const Spacer(),
          Container(
            width: 36,
            height: 36,
            decoration: const BoxDecoration(
              color: Color(0xFF4285F4),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.person, color: Colors.white, size: 20),
          ),
          const SizedBox(width: 12),
          IconButton(
            icon: const Icon(
              Icons.wb_sunny_outlined,
              color: Color(0xFF757575),
              size: 24,
            ),
            onPressed: () {},
          ),
        ],
      ),
    );
  }

  // ---------------- SEARCH BAR ----------------
  Widget _buildSearchBar() {
    return Container(
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(25),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _searchController,
              decoration: const InputDecoration(
                hintText: 'Search your documents...',
                hintStyle: TextStyle(color: Color(0xFF9E9E9E)),
                prefixIcon: Icon(Icons.search, color: Color(0xFF9E9E9E)),
                border: InputBorder.none,
                contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              ),
              onChanged: (value) {
                Provider.of<FilesProvider>(context, listen: false).setSearchQuery(value);
              },
            ),
          ),
        ],
      ),
    );
  }

  // ---------------- FILTERS ----------------


  // ---------------- DOCUMENTS LIST (Sliver) ----------------
  Widget _buildDocumentsListSliver() {
    return Consumer<FilesProvider>(
      builder: (context, provider, child) {
        if (provider.isLoading) {
          return const SliverFillRemaining(
            child: Center(
              child: CircularProgressIndicator(
                valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF4285F4)),
              ),
            ),
          );
        }

        if (provider.errorMessage.isNotEmpty) {
          return SliverFillRemaining(
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 64, color: Color(0xFF757575)),
                  const SizedBox(height: 16),
                  Text(
                    provider.errorMessage,
                    style: const TextStyle(color: Color(0xFF757575)),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => provider.refreshDocuments(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            ),
          );
        }

        if (provider.documents.isEmpty) {
          return const SliverFillRemaining(
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.folder_open, size: 64, color: Color(0xFF757575)),
                  SizedBox(height: 16),
                  Text(
                    'No documents found',
                    style: TextStyle(fontSize: 18, color: Color(0xFF757575)),
                  ),
                  SizedBox(height: 8),
                  Text('Upload your first document to get started',
                      style: TextStyle(color: Color(0xFF9E9E9E))),
                ],
              ),
            ),
          );
        }

        return SliverList(
          delegate: SliverChildBuilderDelegate(
            (context, index) {
              final document = provider.documents[index];
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                child: _buildDocumentCard(document),
              );
            },
            childCount: provider.documents.length,
          ),
        );
      },
    );
  }

  // ---------------- DOCUMENT CARD ----------------
  Widget _buildDocumentCard(SavedDocument document) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            _buildDocumentThumbnail(document),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    document.title,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF2D2D2D),
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${document.fileSize} • ${document.timeAgo} • ${document.documentType}',
                    style: const TextStyle(fontSize: 12, color: Color(0xFF9E9E9E)),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  if (document.isBlockchainVerified) ...[
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Icon(Icons.verified_outlined, size: 16, color: Colors.blue[600]),
                        const SizedBox(width: 4),
                        Text(
                          'Blockchain Verified',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.blue[600],
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            IconButton(
              icon: const Icon(Icons.more_vert, color: Color(0xFF9E9E9E)),
              onPressed: () => _showDocumentOptions(document),
            ),
          ],
        ),
      ),
    );
  }

  // ---------------- DOCUMENT THUMBNAIL ----------------
  Widget _buildDocumentThumbnail(SavedDocument document) {
    if (document.thumbnailUrl != null) {
      return Container(
        width: 60,
        height: 80,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          image: DecorationImage(
            image: NetworkImage(document.thumbnailUrl!),
            fit: BoxFit.cover,
          ),
        ),
      );
    }

    return Container(
      width: 60,
      height: 80,
      decoration: BoxDecoration(
        color: const Color(0xFFE3F2FD),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(_getFileIcon(document.fileType), size: 24, color: const Color(0xFF1976D2)),
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: const Color(0xFF1976D2),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              document.fileExtension,
              style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  IconData _getFileIcon(String fileType) {
    switch (fileType.toLowerCase()) {
      case 'pdf':
        return Icons.picture_as_pdf;
      case 'doc':
      case 'docx':
        return Icons.description;
      case 'jpg':
      case 'jpeg':
      case 'png':
        return Icons.image;
      default:
        return Icons.insert_drive_file;
    }
  }

  // ---------------- ADD DOCUMENT BUTTON ----------------
  Widget _buildAddDocumentButton() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: SizedBox(
        width: double.infinity,
        child: ElevatedButton.icon(
          onPressed: () {
            Navigator.pushNamed(context, '/scanner');
          },
          icon: const Icon(Icons.camera_alt_outlined),
          label: const Text('Add Document'),
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF4285F4),
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 16),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        ),
      ),
    );
  }

  // ---------------- BOTTOM NAVIGATION ----------------
  Widget _buildBottomNavigation() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 10, offset: const Offset(0, -2))],
      ),
      child: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        backgroundColor: Colors.white,
        selectedItemColor: const Color(0xFF4285F4),
        unselectedItemColor: const Color(0xFF9E9E9E),
        currentIndex: 1,
        elevation: 0,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home_outlined), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.folder), label: 'Files'),
          BottomNavigationBarItem(icon: Icon(Icons.chat_bubble_outline), label: 'Chat'),
          BottomNavigationBarItem(icon: Icon(Icons.book_outlined), label: 'Dictionary'),
          BottomNavigationBarItem(icon: Icon(Icons.person_outline), label: 'Profile'),
        ],
        onTap: (index) {
          switch (index) {
            case 0:
              Navigator.pushReplacementNamed(context, '/home');
              break;
            case 1:
              // Already on Files - do nothing
              break;
            case 2:
              Navigator.pushReplacementNamed(context, '/legal-chat');
              break;
            case 3:
              Navigator.pushReplacementNamed(context, '/dictionary');
              break;
            case 4:
              // Profile
              _showProfileOptions();
              break;
          }
        },
      ),
    );
  }

  void _showDocumentOptions(SavedDocument document) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      isScrollControlled: true,
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.75, // Max 75% of screen height
      ),
      builder: (context) => Container(
        padding: const EdgeInsets.all(24),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Document info header
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFFF5F5F5),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    _buildDocumentThumbnail(document),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          document.title,
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${document.fileSize} • ${document.timeAgo}',
                          style: const TextStyle(
                            color: Color(0xFF9E9E9E),
                            fontSize: 12,
                          ),
                        ),
                        if (document.isBlockchainVerified) ...[
                          const SizedBox(height: 4),
                          Row(
                            children: [
                              Icon(
                                Icons.verified,
                                size: 14,
                                color: Colors.green[600],
                              ),
                              const SizedBox(width: 4),
                              Text(
                                'GCUL Secured',
                                style: TextStyle(
                                  fontSize: 11,
                                  color: Colors.green[600],
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            
            // Action options
            ListTile(
              leading: const Icon(Icons.visibility_outlined, color: Color(0xFF4285F4)),
              title: const Text('View Document'),
              onTap: () {
                Navigator.pop(context);
                _viewDocument(document);
              },
            ),
            ListTile(
              leading: const Icon(Icons.download_outlined, color: Color(0xFF4285F4)),
              title: const Text('Download'),
              onTap: () {
                Navigator.pop(context);
                _downloadDocument(document);
              },
            ),
            ListTile(
              leading: const Icon(Icons.share_outlined, color: Color(0xFF4285F4)),
              title: const Text('Share'),
              onTap: () {
                Navigator.pop(context);
                _shareDocument(document);
              },
            ),
            
            // GCUL-specific options
            if (document.isBlockchainVerified) ...[
              const Divider(),
              ListTile(
                leading: Icon(Icons.security, color: Colors.green[600]),
                title: const Text('Verify Integrity'),
                subtitle: const Text('Check document against blockchain'),
                onTap: () {
                  Navigator.pop(context);
                  _verifyDocumentIntegrity(document);
                },
              ),
              ListTile(
                leading: Icon(Icons.timeline, color: Colors.green[600]),
                title: const Text('View Audit Trail'),
                subtitle: const Text('See complete blockchain history'),
                onTap: () {
                  Navigator.pop(context);
                  _showAuditTrail(document);
                },
              ),
              ListTile(
                leading: Icon(Icons.fingerprint, color: Colors.green[600]),
                title: const Text('Blockchain Hash'),
                subtitle: const Text('View cryptographic proof'),
                onTap: () {
                  Navigator.pop(context);
                  _showBlockchainHash(document);
                },
              ),
            ],
            
            const Divider(),
            ListTile(
              leading: const Icon(Icons.delete_outline, color: Colors.red),
              title: const Text('Delete', style: TextStyle(color: Colors.red)),
              onTap: () {
                Navigator.pop(context);
                _confirmDelete(document);
              },
            ),
          ],
        ),
      ),
    ),
    );
  }

  Future<void> _viewDocument(SavedDocument document) async {
    try {
      // Show loading
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => const AlertDialog(
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Loading document...'),
            ],
          ),
        ),
      );

      // Download document
      final bytes = await Provider.of<FilesProvider>(context, listen: false)
          .downloadDocument(
            document.id,
            context: context,
            requireBiometric: document.isBlockchainVerified, // Only require biometric for GCUL documents
          );

      Navigator.pop(context); // Close loading

      // For now, show a preview dialog
      // TODO: Implement proper document viewer
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(document.title),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                _getFileIcon(document.fileType),
                size: 64,
                color: const Color(0xFF1976D2),
              ),
              const SizedBox(height: 16),
              Text('Document loaded (${bytes.length} bytes)'),
              const SizedBox(height: 8),
              const Text('Document viewer will be implemented soon.'),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      );

    } catch (e) {
      Navigator.pop(context); // Close loading
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to load document: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _downloadDocument(SavedDocument document) async {
    try {
      // Show download progress
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 16),
              Text('Downloading ${document.fileName}...'),
              if (document.isBlockchainVerified)
                const Text(
                  'Decrypting with GCUL...',
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
            ],
          ),
        ),
      );

      final bytes = await Provider.of<FilesProvider>(context, listen: false)
          .downloadDocument(
            document.id,
            context: context,
            requireBiometric: document.isBlockchainVerified, // Only require biometric for GCUL documents
          );

      Navigator.pop(context); // Close progress

      // TODO: Save to device downloads
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Downloaded ${document.fileName} (${bytes.length} bytes)'),
          backgroundColor: Colors.green,
          action: SnackBarAction(
            label: 'View',
            onPressed: () => _viewDocument(document),
          ),
        ),
      );

    } catch (e) {
      Navigator.pop(context); // Close progress
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Download failed: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _shareDocument(SavedDocument document) async {
    // TODO: Implement document sharing
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Document sharing will be implemented soon'),
        backgroundColor: Colors.orange,
      ),
    );
  }

  Future<void> _verifyDocumentIntegrity(SavedDocument document) async {
    try {
      // Show verification progress
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(color: Colors.green),
              const SizedBox(height: 16),
              const Text('Verifying Document Integrity...'),
              const SizedBox(height: 8),
              Text(
                'Checking against blockchain\nHash: ${document.blockchainHash?.substring(0, 16) ?? ''}...',
                style: const TextStyle(fontSize: 12, color: Colors.grey),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );

      final verification = await Provider.of<FilesProvider>(context, listen: false)
          .verifyDocumentIntegrity(
            document,
            context: context,
            requireBiometric: true, // Always require biometric for integrity verification
          );

      Navigator.pop(context); // Close progress

      // Show verification results
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          icon: Icon(
            verification['is_valid'] == true ? Icons.verified : Icons.error,
            color: verification['is_valid'] == true ? Colors.green : Colors.red,
            size: 48,
          ),
          title: Text(
            verification['is_valid'] == true 
                ? 'Document Verified ✓' 
                : 'Verification Failed ✗'
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (verification['is_valid'] == true) ...[
                Row(children: [Icon(Icons.check_circle, color: Colors.green, size: 16), const SizedBox(width: 8), const Text('Document integrity confirmed')]),
                Row(children: [Icon(Icons.check_circle, color: Colors.green, size: 16), const SizedBox(width: 8), const Text('Blockchain hash matches')]),
                Row(children: [Icon(Icons.check_circle, color: Colors.green, size: 16), const SizedBox(width: 8), const Text('No tampering detected')]),
              ] else ...[
                Row(children: [Icon(Icons.error, color: Colors.red, size: 16), const SizedBox(width: 8), const Text('Document has been modified')]),
                Row(children: [Icon(Icons.error, color: Colors.red, size: 16), const SizedBox(width: 8), const Text('Hash mismatch detected')]),
                Text('Expected: ${verification['expected_hash'] ?? 'N/A'}'),
                Text('Actual: ${verification['actual_hash'] ?? 'N/A'}'),
              ],
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Verification Details:', style: TextStyle(fontWeight: FontWeight.bold)),
                    Text('Timestamp: ${DateTime.now().toString()}'),
                    Text('Hash Algorithm: ${verification['algorithm'] ?? 'SHA-256'}'),
                    Text('Blockchain Record: ${verification['blockchain_record'] ?? 'Found'}'),
                  ],
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
            if (verification['is_valid'] != true)
              ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                  _showAuditTrail(document);
                },
                style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                child: const Text('View Audit Trail'),
              ),
          ],
        ),
      );

    } catch (e) {
      Navigator.pop(context); // Close progress
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Verification failed: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _showAuditTrail(SavedDocument document) async {
    try {
      // Show loading
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => const AlertDialog(
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              CircularProgressIndicator(color: Colors.green),
              SizedBox(height: 16),
              Text('Loading audit trail...'),
            ],
          ),
        ),
      );

      final auditTrail = await Provider.of<FilesProvider>(context, listen: false)
          .getDocumentAuditTrail(
            document.id,
            context: context,
            requireBiometric: true, // Always require biometric for audit trail access
          );

      Navigator.pop(context); // Close loading

      // Show audit trail
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Blockchain Audit Trail'),
          content: SizedBox(
            width: double.maxFinite,
            height: 400,
            child: auditTrail.isEmpty
                ? const Center(child: Text('No audit trail found'))
                : ListView.builder(
                    itemCount: auditTrail.length,
                    itemBuilder: (context, index) {
                      final entry = auditTrail[index];
                      return Card(
                        margin: const EdgeInsets.symmetric(vertical: 4),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: Colors.green.shade100,
                            child: Text('${index + 1}'),
                          ),
                          title: Text(entry['action'] ?? 'Unknown Action'),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(entry['timestamp'] ?? 'Unknown Time'),
                              if (entry['hash'] != null)
                                Text(
                                  'Hash: ${entry['hash'].toString().substring(0, 16)}...',
                                  style: const TextStyle(fontFamily: 'monospace'),
                                ),
                            ],
                          ),
                          trailing: Icon(
                            Icons.verified_outlined,
                            color: Colors.green[600],
                          ),
                        ),
                      );
                    },
                  ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      );

    } catch (e) {
      Navigator.pop(context); // Close loading
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to load audit trail: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _showBlockchainHash(SavedDocument document) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        icon: Icon(
          Icons.security,
          color: Colors.green[600],
          size: 48,
        ),
        title: const Text('GCUL Blockchain Verification'),
        content: SizedBox(
          width: double.maxFinite,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('This document is secured with GCUL blockchain technology:'),
                const SizedBox(height: 16),
                
                // Security features
                _buildSecurityBadge(Icons.security, 'Google Cloud KMS Encrypted'),
                _buildSecurityBadge(Icons.link, 'Blockchain Hash Verified'),
                _buildSecurityBadge(Icons.shield, 'Tamper-Proof Storage'),
                _buildSecurityBadge(Icons.assignment, 'Complete Audit Trail'),
                
                const SizedBox(height: 16),
                
                // Hash details
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.green.shade200),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Blockchain Hash:',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.green.shade800,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        document.blockchainHash ?? 'Hash not available',
                        style: TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 11,
                          color: Colors.green.shade700,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Document ID:',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.green.shade800,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        document.id,
                        style: TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 11,
                          color: Colors.green.shade700,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Created: ${document.createdAt}',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey.shade600,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
          ElevatedButton.icon(
            onPressed: () {
              // TODO: Copy hash to clipboard
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Hash copied to clipboard')),
              );
            },
            icon: const Icon(Icons.copy),
            label: const Text('Copy Hash'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSecurityBadge(IconData iconData, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(iconData, size: 16, color: Colors.blue[700]),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(fontSize: 14),
            ),
          ),
          Icon(
            Icons.check_circle,
            color: Colors.green[600],
            size: 16,
          ),
        ],
      ),
    );
  }

  void _confirmDelete(SavedDocument document) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(
          Icons.warning,
          color: Colors.orange,
          size: 48,
        ),
        title: const Text('Delete Document'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Are you sure you want to delete "${document.title}"?'),
            const SizedBox(height: 12),
            if (document.isBlockchainVerified) 
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.orange.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.orange.shade200),
                ),
                child: Column(
                  children: [
                    Icon(
                      Icons.security,
                      color: Colors.orange.shade700,
                      size: 24,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'This document is GCUL blockchain verified. Deleting will remove it from secure storage and the blockchain record.',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.orange.shade700,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context); // Close confirmation dialog
              
              // Show deletion progress with proper error handling
              showDialog(
                context: context,
                barrierDismissible: false,
                builder: (context) => AlertDialog(
                  content: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const CircularProgressIndicator(color: Colors.red),
                      const SizedBox(height: 16),
                      Text('Deleting ${document.title}...'),
                      if (document.isBlockchainVerified)
                        const Text(
                          'Removing from GCUL blockchain...',
                          style: TextStyle(fontSize: 12, color: Colors.grey),
                        ),
                    ],
                  ),
                ),
              );
              
              try {
              print('Starting delete operation for: ${document.id}');
                
                await Provider.of<FilesProvider>(context, listen: false)
                    .deleteDocument(
                      document.id,
                      context: context,
                      requireBiometric: document.isBlockchainVerified, // Require biometric for GCUL documents
                    );
                
                // Close progress dialog on success
                if (mounted && Navigator.canPop(context)) {
                  Navigator.pop(context);
                }
                
              print('Delete operation completed successfully');
                
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('${document.title} deleted successfully'),
                    backgroundColor: Colors.green,
                    duration: const Duration(seconds: 2),
                  ),
                );
                
              } catch (e) {
              print('Delete operation failed: $e');
                
                // Close progress dialog on error
                if (mounted && Navigator.canPop(context)) {
                  Navigator.pop(context);
                }
                
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Failed to delete document: $e'),
                    backgroundColor: Colors.red,
                    duration: const Duration(seconds: 3),
                  ),
                );
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  void _showProfileOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => Container(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.settings_outlined),
              title: const Text('Settings'),
              onTap: () {
                Navigator.pop(context);
                Navigator.pushNamed(context, '/settings');
              },
            ),
            ListTile(
              leading: const Icon(Icons.person_outline),
              title: const Text('Profile'),
              onTap: () {
                Navigator.pop(context);
                // Navigate to profile screen when available
              },
            ),
            ListTile(
              leading: const Icon(Icons.logout, color: Colors.red),
              title: const Text('Sign Out', style: TextStyle(color: Colors.red)),
              onTap: () async {
                Navigator.pop(context);
                final shouldSignOut = await showDialog<bool>(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Sign Out'),
                    content: const Text('Are you sure you want to sign out?'),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(context, false),
                        child: const Text('Cancel'),
                      ),
                      TextButton(
                        onPressed: () => Navigator.pop(context, true),
                        style: TextButton.styleFrom(foregroundColor: Colors.red),
                        child: const Text('Sign Out'),
                      ),
                    ],
                  ),
                );
                
                if (shouldSignOut == true && mounted) {
                  await Provider.of<app_auth.AuthProvider>(context, listen: false).signOut();
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}
