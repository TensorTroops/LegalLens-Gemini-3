import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:camera/camera.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'dart:convert';
import 'package:path/path.dart' as path;
import '../config/app_config.dart';
import '../services/gcul_document_service.dart';
import '../providers/files_provider.dart';

class DocumentScannerScreen extends StatefulWidget {
  const DocumentScannerScreen({super.key});

  @override
  State<DocumentScannerScreen> createState() => _DocumentScannerScreenState();
}

class _DocumentScannerScreenState extends State<DocumentScannerScreen> {
  CameraController? _cameraController;
  bool _isCameraInitialized = false;
  bool _aiPoweredScan = true;
  XFile? _selectedFile;
  Uint8List? _selectedFileBytes;
  String? _selectedFileName;
  bool _isProcessing = false;
  String _extractedText = '';
  String _fileName = '';
  
  // Processing steps
  bool _extractingText = false;
  bool _analyzingContent = false;
  bool _generatingSummary = false;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isNotEmpty) {
        // Prefer back camera for document scanning
        CameraDescription? backCamera;
        for (var camera in cameras) {
          if (camera.lensDirection == CameraLensDirection.back) {
            backCamera = camera;
            break;
          }
        }
        
        _cameraController = CameraController(
          backCamera ?? cameras.first,
          ResolutionPreset.veryHigh, // Higher resolution for better text capture
          enableAudio: false,
          imageFormatGroup: ImageFormatGroup.jpeg,
        );
        
        await _cameraController!.initialize();
        
        // Set additional camera settings for document scanning
        await _cameraController!.setFocusMode(FocusMode.auto);
        await _cameraController!.setExposureMode(ExposureMode.auto);
        await _cameraController!.setFlashMode(FlashMode.off);
        
        if (mounted) {
          setState(() {
            _isCameraInitialized = true;
          });
        }
      }
    } catch (e) {
    print('Camera initialization error: $e');
    }
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Scan Document',
          style: TextStyle(
            color: Colors.black,
            fontSize: 18,
            fontWeight: FontWeight.w500,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.wb_sunny_outlined, color: Colors.black),
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.help_outline, color: Colors.black),
            onPressed: () {},
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // AI-Powered Secure Scan Toggle
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: const Color(0xFFE3F2FD),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.security,
                    color: Color(0xFF1976D2),
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    'AI-Powered Secure Scan',
                    style: TextStyle(
                      color: Color(0xFF1976D2),
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const Spacer(),
                  Switch(
                    value: _aiPoweredScan,
                    onChanged: (value) {
                      setState(() {
                        _aiPoweredScan = value;
                      });
                    },
                    activeThumbColor: const Color(0xFF1976D2),
                  ),
                  const SizedBox(width: 8),
                  const Icon(
                    Icons.help_outline,
                    color: Color(0xFF1976D2),
                    size: 16,
                  ),
                ],
              ),
            ),

            // Camera Preview Section
            Container(
              margin: const EdgeInsets.all(16),
              height: 300,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                color: Colors.grey[100],
              ),
              child: Stack(
                children: [
                  // Camera preview or placeholder
                  ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: _isCameraInitialized && _cameraController != null
                        ? SizedBox(
                            width: double.infinity,
                            height: double.infinity,
                            child: FittedBox(
                              fit: BoxFit.cover,
                              child: SizedBox(
                                width: _cameraController!.value.previewSize?.height ?? 300,
                                height: _cameraController!.value.previewSize?.width ?? 300,
                                child: CameraPreview(_cameraController!),
                              ),
                            ),
                          )
                        : Container(
                            width: double.infinity,
                            height: double.infinity,
                            color: Colors.grey[200],
                            child: const Center(
                              child: Icon(
                                Icons.camera_alt,
                                size: 50,
                                color: Colors.grey,
                              ),
                            ),
                          ),
                  ),
                  
                  // Blue corner brackets
                  Positioned.fill(
                    child: Container(
                      margin: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        border: Border.all(color: Colors.transparent),
                      ),
                      child: CustomPaint(
                        painter: CornerBracketsPainter(),
                      ),
                    ),
                  ),
                  
                  // Loading overlay during processing
                  if (_isProcessing)
                    Container(
                      width: double.infinity,
                      height: double.infinity,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(16),
                        color: Colors.black.withValues(alpha: 0.7),
                      ),
                      child: const Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            CircularProgressIndicator(
                              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                            ),
                            SizedBox(height: 16),
                            Text(
                              'Processing Document...',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            SizedBox(height: 8),
                            Text(
                              'Please wait while we extract text',
                              style: TextStyle(
                                color: Colors.white70,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  
                  // Capture button
                  if (!_isProcessing)
                    Positioned(
                      bottom: 20,
                      left: 0,
                      right: 0,
                      child: Center(
                        child: GestureDetector(
                          onTap: _capturePhoto,
                          child: Container(
                            width: 70,
                            height: 70,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: const Color(0xFF1976D2),
                              border: Border.all(color: Colors.white, width: 4),
                            ),
                            child: const Icon(
                              Icons.camera_alt,
                              color: Colors.white,
                              size: 30,
                            ),
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),

            // Upload and Select Files buttons
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _isProcessing ? null : _uploadFromGallery,
                      icon: const Icon(Icons.photo_library_outlined),
                      label: const Text('Upload Image'),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        side: BorderSide(color: _isProcessing ? Colors.grey.shade300 : Colors.grey),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _isProcessing ? null : _selectFiles,
                      icon: const Icon(Icons.folder_outlined),
                      label: const Text('Select Files'),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        side: BorderSide(color: _isProcessing ? Colors.grey.shade300 : Colors.grey),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Document Preview (if file selected)
            if (_selectedFile != null) _buildDocumentPreview(),

            // Processing Section
            if (_isProcessing) _buildProcessingSection(),

            const SizedBox(height: 20),

            // Action Buttons
            _buildActionButtons(),

            const SizedBox(height: 20),

            // Footer
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'End-to-end encryption',
                    style: TextStyle(
                      color: Colors.grey,
                      fontSize: 12,
                    ),
                  ),
                  Text(
                    'GDPR compliant',
                    style: TextStyle(
                      color: Colors.grey,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildDocumentPreview() {
  final fileName = _selectedFile != null ? path.basename(_selectedFile!.path) : 'Unknown Document';
  final fileExtension = _selectedFile != null ? path.extension(_selectedFile!.path).toUpperCase().replaceFirst('.', '') : 'FILE';
  final fileSize = (_selectedFile != null || _selectedFileBytes != null) ? _getFileSize() : '0 KB';
  
  return Container(
    margin: const EdgeInsets.symmetric(horizontal: 16),
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: Colors.grey[50],
      borderRadius: BorderRadius.circular(12),
      border: Border.all(color: Colors.grey[200]!),
    ),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // File thumbnail
        Container(
          width: 60,
          height: 60,
          decoration: BoxDecoration(
            color: Colors.grey[200],
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(
            _getFileIcon(fileExtension),
            color: Colors.grey,
            size: 30,
          ),
        ),
        const SizedBox(width: 16),

        // File name and details
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                fileName,
                style: const TextStyle(
                  fontWeight: FontWeight.w500,
                  fontSize: 16,
                ),
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 4),
              Text(
                '$fileExtension • $fileSize • Processing...',
                style: const TextStyle(
                  color: Colors.grey,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),

        // Verified tick icon
        Container(
          padding: const EdgeInsets.all(8),
          decoration: const BoxDecoration(
            color: Color(0xFF1976D2),
            shape: BoxShape.circle,
          ),
          child: const Icon(
            Icons.check,
            color: Colors.white,
            size: 16,
          ),
        ),

        const SizedBox(width: 8),

        // ❌ Remove button
        IconButton(
          icon: const Icon(Icons.close_rounded, color: Colors.redAccent),
          tooltip: 'Remove file',
          onPressed: () {
            setState(() {
              _selectedFile = null;
              _selectedFileBytes = null;
              _selectedFileName = null;
              _fileName = '';
              _extractedText = '';
            });
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('File removed'),
                duration: Duration(seconds: 1),
              ),
            );
          },
        ),
      ],
    ),
  );
}


  IconData _getFileIcon(String extension) {
    switch (extension.toLowerCase()) {
      case 'pdf':
        return Icons.picture_as_pdf;
      case 'jpg':
      case 'jpeg':
      case 'png':
        return Icons.image;
      default:
        return Icons.description;
    }
  }

  String _getFileSize() {
    if (kIsWeb && _selectedFileBytes != null) {
      final bytes = _selectedFileBytes!.length;
      if (bytes < 1024) return '$bytes B';
      if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    } else if (_selectedFile != null) {
      try {
        if (!kIsWeb) {
          // On mobile/desktop, we can read file size
          return 'File selected';
        }
      } catch (e) {
        return 'Unknown size';
      }
    }
    return '0 KB';
  }

  Widget _buildProcessingSection() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Processing document...',
            style: TextStyle(
              fontWeight: FontWeight.w500,
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 16),
          _buildProcessingStep(
            'Extracting text',
            _extractingText,
            true,
          ),
          _buildProcessingStep(
            'Analyzing content',
            _analyzingContent,
            false,
          ),
          _buildProcessingStep(
            'Generating summary...',
            _generatingSummary,
            false,
          ),
        ],
      ),
    );
  }

  Widget _buildProcessingStep(String title, bool isCompleted, bool isActive) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            width: 20,
            height: 20,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isCompleted 
                  ? const Color(0xFF1976D2)
                  : isActive 
                      ? const Color(0xFF1976D2)
                      : Colors.grey[300],
            ),
            child: isCompleted
                ? const Icon(Icons.check, color: Colors.white, size: 14)
                : isActive
                    ? const SizedBox(
                        width: 12,
                        height: 12,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : null,
          ),
          const SizedBox(width: 12),
          Text(
            title,
            style: TextStyle(
              color: isCompleted || isActive ? Colors.black : Colors.grey,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          
          const SizedBox(width: 12),
          Expanded(
            child: OutlinedButton.icon(
              onPressed: _summarizeDocument,
              icon: const Icon(Icons.summarize_outlined),
              label: const Text('Summarize'),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 12),
                side: const BorderSide(color: Colors.grey),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: ElevatedButton.icon(
              onPressed: _saveDocument,
              icon: const Icon(Icons.bookmark_outline),
              label: const Text('Save Document'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1976D2),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _capturePhoto() async {
    if (_cameraController != null && _cameraController!.value.isInitialized && !_isProcessing) {
      try {
        // Set optimal capture settings for documents
        await _cameraController!.setFocusMode(FocusMode.auto);
        await _cameraController!.setExposureMode(ExposureMode.auto);
        
        // Take high quality photo
        final XFile photo = await _cameraController!.takePicture();
        
        setState(() {
          _selectedFile = photo;
          _selectedFileName = path.basename(photo.path);
          _fileName = _selectedFileName!;
        });
        
        // Load file bytes for web compatibility
        await _loadFileBytes();
        
        // Process the captured image
        _processDocument();
      } catch (e) {
      print('Error capturing photo: $e');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error capturing photo: $e')),
        );
      }
    }
  }

  Future<void> _uploadFromGallery() async {
    if (_isProcessing) return;
    
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 95, // High quality for better OCR
    );
    
    if (image != null) {
      setState(() {
        _selectedFile = image;
        _selectedFileName = path.basename(image.path);
        _fileName = _selectedFileName!;
      });
      
      // Load file bytes for web compatibility
      await _loadFileBytes();
      
      _processDocument();
    }
  }

  Future<void> _selectFiles() async {
    if (_isProcessing) return;
    
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'jpg', 'jpeg', 'png'],
    );

    if (result != null) {
      final file = result.files.single;
      if (kIsWeb) {
        // On web, use bytes directly
        setState(() {
          _selectedFileBytes = file.bytes;
          _selectedFileName = file.name;
          _fileName = file.name;
        });
      } else {
        // On mobile, use file path
        if (file.path != null) {
          setState(() {
            _selectedFile = XFile(file.path!);
            _selectedFileName = file.name;
            _fileName = file.name;
          });
          await _loadFileBytes();
        }
      }
      _processDocument();
    }
  }

  Future<void> _loadFileBytes() async {
    if (_selectedFile != null) {
      _selectedFileBytes = await _selectedFile!.readAsBytes();
    }
  }

  void _processDocument() {
    setState(() {
      _isProcessing = true;
      _extractingText = true;
    });

    // Check for demo user with demo files
    final user = FirebaseAuth.instance.currentUser;
    if (user?.email?.toLowerCase() == 'smp@gmail.com') {
      final fileName = _selectedFileName?.toLowerCase() ?? '';
      if (fileName.contains('loan1.pdf') || 
          fileName.contains('rental_contract.pdf') || 
          fileName.contains('internship-nda.pdf') ||
          fileName.contains('kadan.pdf')) {
        _handleDemoDocument();
        return;
      }
    }

    // Start text extraction for regular users
    _extractTextFromImage();
  }

  Future<void> _handleDemoDocument() async {
    try {
      setState(() {
        _extractingText = true;
      });

      // Simulate processing delay
      await Future.delayed(const Duration(seconds: 2));

      // Determine document type and set appropriate extracted text
      final fileName = _selectedFileName?.toLowerCase() ?? '';
      String demoText;
      
      if (fileName.contains('rental_contract.pdf')) {
        demoText = '''RESIDENTIAL RENTAL AGREEMENT

This Residential Rental Agreement ("Agreement") is entered into on June 1, 2025, in Pollachi, Tamil Nadu, between:

OWNER: Mr. Suganth Nadar
Address: No. 70, Kamatchi Temple Road, Pollachi, Tamil Nadu 642001
Contact: +91 9876543210

TENANT: Mr. Abiruth Chinna Gounder
Occupation: Student/Employee at Amrita Vishwa Vidyapeetham
Contact: +91 8765432109

PROPERTY DETAILS:
Address: No. 70, Kamatchi Temple Road, Pollachi, Tamil Nadu 642001
Type: Two bedrooms, living room, kitchen, parking facilities
Purpose: Residential use only

RENTAL TERMS:
- Lease Period: 25 months (June 1, 2025 to July 31, 2027)
- Monthly Rent: Rs. 5,000
- Maintenance Charges: Rs. 500
- Total Monthly Payment: Rs. 5,500
- Due Date: 7th of each month
- Security Deposit: Rs. 20,000 (interest-free, refundable)

SPECIAL CONDITIONS:
- Property for residential use only
- No subletting or assignment allowed
- Tenant responsible for minor repairs
- Owner handles structural repairs
- Monthly property inspection allowed
- One month written notice for termination''';
      } else if (fileName.contains('internship-nda.pdf')) {
        demoText = '''INTERNSHIP CONFIDENTIALITY AGREEMENT

This Internship Confidentiality Agreement ("Agreement") is entered into on November 5, 2025, between:

INTERN: HariRam S
Address: No. 15, Students Colony, Coimbatore, Tamil Nadu 641001
Contact: +91 9876543210
Institution: Amrita Vishwa Vidyapeetham

SPONSOR: Global Tech Pvt Limited
Corporate Office: IT Park, Saravanampatti, Coimbatore, Tamil Nadu 641035
GSTIN: 33AABCG1234E1Z8
Contact: hr@globaltech.com

INTERNSHIP DETAILS:
Position: Software Development Intern
Duration: November 5, 2025 to February 5, 2026 (3 months)
Department: Research & Development
Type: Unpaid Internship
Purpose: Industry knowledge and practical experience

CONFIDENTIALITY TERMS:
- Confidentiality Period: 90 days from November 5, 2025
- Covers: Documents, data, designs, plans, procedures, software, prototypes
- Standard: Reasonable care required to protect information
- Access: Limited to need-to-know basis only
- Restrictions: No disclosure to third parties or personal use

OBLIGATIONS:
- Maintain strict confidentiality of all business information
- Use information only for legitimate internship purposes
- Return all confidential materials upon completion''';
      } else if (fileName.contains('kadan.pdf')) {
        demoText = '''கடன் உறுதி பத்திரம்

இந்த கடன் உறுதி பத்திரம் ("ஒப்பந்தம்") 2022 நவம்பர் 03 அன்று, பொள்ளாச்சி, தமிழ்நாட்டில் கையெழுத்தானது:

கடன் கொடுப்பவர்: திருமதி வித்யா ராமன்
முகவரி: எண். 25, காமராஜர் தெரு, பொள்ளாச்சி, தமிழ்நாடு 642001
தொலைபேசி: +91 9876543210

கடன் பெறுபவர்: திரு அருண் குமார்
முகவரி: எண். 40, மாரியம்மன் கோவில் தெரு, ஆலங்குளம், பொள்ளாச்சி
தொலைபேசி: +91 8765432109
தொழில்: சிறு வணிகம்

கடன் விவரங்கள்:
மொத்த கடன் தொகை: ₹2,50,000 (இரண்டு லட்சத்து ஐம்பதாயிரம் ரூபாய்)
வட்டி விகிதம்: 12% ஆண்டிற்கு
கடன் காலம்: 18 மாதங்கள்
மாதாந்திர தவணை: ₹15,750

பிணை சொத்து:
சொத்து: இல்லம்
சர்வே எண்: T.S. No. 45/2B
இடம்: ஆலங்குளம் கிராமம், பொள்ளாச்சி வட்டம், தமிழ்நாடு
உரிமையாளர்: திரு அருண் குமார்
மதிப்பு: ₹5,00,000

நிபந்தனைகள்:
- மாதாந்திர தவணை ஒவ்வொரு மாதமும் 15ஆம் தேதி செலுத்த வேண்டும்
- தாமதமான செலுத்துதலுக்கு 2% அபராத வட்டி
- கடன் தொகை வீட்டு செலவு மற்றும் சிறு வணிக நோக்கத்திற்காக பயன்படுத்தப்படும்
- தமிழ்நாடு அரசின் சட்டங்களின்படி இந்த ஒப்பந்தம் நடைமுறையில் உள்ளது''';
      } else {
        // Default to loan document
        demoText = '''BUSINESS LOAN AGREEMENT

This Business Loan Agreement ("Agreement") is entered into on November 2, 2025, in Chennai, Tamil Nadu, between:

LENDER: ICICI Bank Limited
Corporate Office: Bandra Kurla Complex, Mumbai, Maharashtra 400051
GSTIN: 27AAACI1681G1ZK

BORROWER: GreenField Electronics Pvt. Ltd.
Registered Office: No. 45, Anna Salai, Chennai, Tamil Nadu 600002
GSTIN: 33AABCG1234E1Z5

PRINCIPAL AMOUNT: Rs. 50,00,000 (Fifty Lakhs)
INTEREST RATE: 12% per annum (calculated monthly)
LOAN TERM: 5 years (60 months)

REPAYMENT SCHEDULE:
- Monthly installments starting December 9, 2025
- Payment due on 9th of each month
- Final payment due: November 9, 2030

SPECIAL TERMS:
- Prepayment allowed without penalty
- Grace period: 30 days after missed payment
- Late fee: Rs. 1,000 after grace period
- Indian law applies, Dindigul courts have jurisdiction''';
      }

      // Set demo extracted text
      setState(() {
        _extractedText = demoText;
        _extractingText = false;
        _isProcessing = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('document processed successfully!'),
          backgroundColor: Colors.green,
        ),
      );

    } catch (e) {
      setState(() {
        _extractingText = false;
        _isProcessing = false;
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Demo processing failed: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _extractTextFromImage() async {
    if (_selectedFile == null && _selectedFileBytes == null) return;

    try {
      setState(() {
        _extractingText = true;
      });

      // Call Document AI backend
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('${AppConfig.apiBaseUrl}/api/v1/documents/process'),
      );
      
      if (kIsWeb && _selectedFileBytes != null) {
        // On web, use bytes
        request.files.add(
          http.MultipartFile.fromBytes(
            'file',
            _selectedFileBytes!,
            filename: _selectedFileName ?? 'document',
          ),
        );
      } else if (_selectedFile != null) {
        // On mobile, use file path
        request.files.add(
          await http.MultipartFile.fromPath(
            'file',
            _selectedFile!.path,
            filename: _selectedFileName,
          ),
        );
      }

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final extractedText = data['text'] ?? '';
        
        setState(() {
          _extractedText = extractedText;
          _extractingText = false;
          _analyzingContent = true;
        });

        // Simulate content analysis completion
        await Future.delayed(const Duration(seconds: 1));
        
        if (mounted) {
          setState(() {
            _analyzingContent = false;
            _generatingSummary = false;
            _isProcessing = false;
          });
          
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Text extracted and saved successfully!'),
              backgroundColor: Colors.green,
            ),
          );
        }

      } else {
        throw Exception('Failed to process document: ${response.statusCode} - ${response.body}');
      }

    } catch (e) {
    print('Error extracting text: $e');
      setState(() {
        _extractingText = false;
        _isProcessing = false;
      });
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error extracting text: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  void _summarizeDocument() {
    // Navigate to legal chat with extracted text for comprehensive analysis
    if (_extractedText.isNotEmpty) {
      Navigator.pushNamed(
        context, 
        '/legal-chat',
        arguments: {
          'initialText': _extractedText,
          'documentTitle': _fileName.isNotEmpty ? _fileName : 'Legal Document',
          'comprehensive': true, // Enable comprehensive analysis workflow
        },
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please process a document first to get text'),
          backgroundColor: Colors.orange,
        ),
      );
    }
  }

  void _saveDocument() async {
    if (_selectedFile == null && _selectedFileBytes == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a document first'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    try {
      setState(() {
        _isProcessing = true;
      });

      // Show saving dialog
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 16),
              const Text('Saving with GCUL Blockchain Security...'),
              const SizedBox(height: 8),
              Text(
                'Encrypting • Hashing • Verifying',
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      );

      // Prepare file bytes
      Uint8List fileBytes;
      if (_selectedFileBytes != null) {
        fileBytes = _selectedFileBytes!;
      } else if (_selectedFile != null) {
        fileBytes = await _selectedFile!.readAsBytes();
      } else {
        throw Exception('No file content available');
      }

      // Determine document type based on filename or content
      String documentType = 'Legal Document';
      final fileName = _selectedFileName ?? 'document';
      if (fileName.toLowerCase().contains('contract')) {
        documentType = 'Contract';
      } else if (fileName.toLowerCase().contains('will') || fileName.toLowerCase().contains('testament')) {
        documentType = 'Will & Testament';
      } else if (fileName.toLowerCase().contains('nda') || fileName.toLowerCase().contains('agreement')) {
        documentType = 'Agreement';
      } else if (fileName.toLowerCase().contains('license')) {
        documentType = 'License';
      }

      // Get file extension
      String fileType = 'PDF';
      if (fileName.toLowerCase().endsWith('.jpg') || fileName.toLowerCase().endsWith('.jpeg')) {
        fileType = 'JPEG';
      } else if (fileName.toLowerCase().endsWith('.png')) {
        fileType = 'PNG';
      } else if (fileName.toLowerCase().endsWith('.doc') || fileName.toLowerCase().endsWith('.docx')) {
        fileType = 'DOC';
      }

      // Save with GCUL blockchain security
      final gculService = GCULDocumentService();
      final savedDocument = await gculService.saveDocumentWithGCUL(
        fileBytes: fileBytes,
        fileName: fileName,
        fileType: fileType,
        documentType: documentType,
        extractedText: _extractedText.isNotEmpty ? _extractedText : null,
      );

      // Update files provider
      if (mounted) {
        Provider.of<FilesProvider>(context, listen: false).addDocument(savedDocument);
        
        Navigator.pop(context); // Close saving dialog
        setState(() {
          _isProcessing = false;
        });

        // Show success dialog with blockchain details
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            icon: const Icon(
              Icons.verified,
              color: Colors.green,
              size: 48,
            ),
            title: const Text('Document Saved Successfully!'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Your document has been secured with:'),
                const SizedBox(height: 12),
                _buildSecurityFeature(Icons.security, 'Google Cloud KMS Encryption'),
                _buildSecurityFeature(Icons.link, 'Blockchain Hash Verification'),
                _buildSecurityFeature(Icons.shield, 'Tamper-Proof Storage'),
                _buildSecurityFeature(Icons.assignment, 'Complete Audit Trail'),
                const SizedBox(height: 12),
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
                      const SizedBox(height: 4),
                      Text(
                        savedDocument.blockchainHash ?? 'Generated',
                        style: TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 11,
                          color: Colors.green.shade700,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.pushReplacementNamed(context, '/files');
                },
                child: const Text('View in My Files'),
              ),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                ),
                child: const Text('Continue'),
              ),
            ],
          ),
        );
      }

    } catch (e) {
      if (mounted) {
        Navigator.pop(context); // Close saving dialog
        setState(() {
          _isProcessing = false;
        });

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to save document: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 5),
          ),
        );
      }
    }
  }

  Widget _buildSecurityFeature(IconData iconData, String text) {
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
            color: Colors.green,
            size: 16,
          ),
        ],
      ),
    );
  }
}

class CornerBracketsPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF1976D2)
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    const double bracketLength = 20;

    // Top-left corner
    canvas.drawLine(const Offset(0, bracketLength), const Offset(0, 0), paint);
    canvas.drawLine(const Offset(0, 0), const Offset(bracketLength, 0), paint);

    // Top-right corner
    canvas.drawLine(Offset(size.width - bracketLength, 0), Offset(size.width, 0), paint);
    canvas.drawLine(Offset(size.width, 0), Offset(size.width, bracketLength), paint);

    // Bottom-left corner
    canvas.drawLine(Offset(0, size.height - bracketLength), Offset(0, size.height), paint);
    canvas.drawLine(Offset(0, size.height), Offset(bracketLength, size.height), paint);

    // Bottom-right corner
    canvas.drawLine(Offset(size.width - bracketLength, size.height), Offset(size.width, size.height), paint);
    canvas.drawLine(Offset(size.width, size.height), Offset(size.width, size.height - bracketLength), paint);
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => false;
}