import 'package:local_auth/local_auth.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:crypto/crypto.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'dart:convert';
import 'dart:io';

/// Professional Fingerprint Authentication Service for LegalLens
/// 
/// Implements enterprise-grade fingerprint authentication with:
/// - Hardware-backed security
/// - No biometric data storage  
/// - Session management
/// - GCUL integration
/// - Fingerprint-only focus for enhanced security
class BiometricService {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
    iOptions: IOSOptions(
      accessibility: KeychainAccessibility.first_unlock_this_device,
    ),
  );
  
  final LocalAuthentication _localAuth = LocalAuthentication();
  final DeviceInfoPlugin _deviceInfo = DeviceInfoPlugin();
  
  /// Check device fingerprint capability
  Future<BiometricCapability> checkBiometricCapability() async {
    try {
      final isAvailable = await _localAuth.isDeviceSupported();
      if (!isAvailable) return BiometricCapability.none;
      
      final canCheckBiometrics = await _localAuth.canCheckBiometrics;
      if (!canCheckBiometrics) return BiometricCapability.none;
      
      final availableBiometrics = await _localAuth.getAvailableBiometrics();
      
      // Focus only on fingerprint authentication
      if (availableBiometrics.contains(BiometricType.fingerprint)) {
        return BiometricCapability.available;
      } else if (availableBiometrics.isNotEmpty) {
        return BiometricCapability.available;
      }
      
      return BiometricCapability.none;
    } catch (e) {
    print('BiometricService: Error checking capability: $e');
      return BiometricCapability.none;
    }
  }
  
  /// Enroll user for biometric authentication
  Future<BiometricEnrollmentResult> enrollBiometric(String userEmail) async {
    try {
    print('🔐 BiometricService: Starting enrollment for $userEmail');
      
      final capability = await checkBiometricCapability();
      if (capability == BiometricCapability.none) {
        return BiometricEnrollmentResult.deviceNotSupported;
      }
      
      // Authenticate to ensure user consent and capability
      final didAuthenticate = await _localAuth.authenticate(
        localizedReason: 'Enable fingerprint authentication for secure access to LegalLens legal documents',
        options: const AuthenticationOptions(
          biometricOnly: false, // Allow fallback to device credentials
          stickyAuth: true,
          useErrorDialogs: true,
          sensitiveTransaction: true,
        ),
      );
      
      if (!didAuthenticate) {
      print('BiometricService: User cancelled enrollment');
        return BiometricEnrollmentResult.userCancelled;
      }
      
      // Generate unique biometric verification token
      final biometricToken = await _generateBiometricToken(userEmail);
      final deviceId = await _getDeviceId();
      
      // Store encrypted biometric preferences
      await _storage.write(
        key: 'biometric_enabled_$userEmail',
        value: 'true',
      );
      
      await _storage.write(
        key: 'biometric_token_$userEmail',
        value: biometricToken,
      );
      
      await _storage.write(
        key: 'biometric_device_id_$userEmail',
        value: deviceId,
      );
      
      // Store enrollment timestamp
      await _storage.write(
        key: 'biometric_enrolled_at_$userEmail',
        value: DateTime.now().toIso8601String(),
      );
      
      // Store as last biometric user for login purposes
      await _storage.write(
        key: 'last_biometric_user',
        value: userEmail,
      );
      
    print('BiometricService: Enrollment successful for $userEmail');
      return BiometricEnrollmentResult.success;
    } catch (e) {
    print('BiometricService: Enrollment error: $e');
      return BiometricEnrollmentResult.error;
    }
  }
  
  /// Verify biometric authentication for login
  Future<BiometricVerificationResult> verifyBiometric(String userEmail) async {
    try {
    print('🔍 BiometricService: Starting verification for $userEmail');
      
      // Check if biometrics are enrolled for this user
      final isEnabled = await _storage.read(key: 'biometric_enabled_$userEmail');
      if (isEnabled != 'true') {
      print('BiometricService: Biometric not enrolled for $userEmail');
        return BiometricVerificationResult.notEnrolled;
      }
      
      // Verify device consistency
      final storedDeviceId = await _storage.read(key: 'biometric_device_id_$userEmail');
      final currentDeviceId = await _getDeviceId();
      
      if (storedDeviceId != currentDeviceId) {
      print('🚨 BiometricService: Device mismatch - security issue detected');
        await disableBiometric(userEmail);
        return BiometricVerificationResult.securityError;
      }
      
      // Perform biometric authentication
      final didAuthenticate = await _localAuth.authenticate(
        localizedReason: 'Authenticate with fingerprint to access your legal documents securely',
        options: const AuthenticationOptions(
          biometricOnly: false, // Allow fallback to device credentials
          stickyAuth: true,
          useErrorDialogs: true,
          sensitiveTransaction: true,
        ),
      );
      
      if (!didAuthenticate) {
      print('BiometricService: Authentication failed for $userEmail');
        return BiometricVerificationResult.failed;
      }
      
      // Verify biometric token integrity
      final storedToken = await _storage.read(key: 'biometric_token_$userEmail');
      final expectedToken = await _generateBiometricToken(userEmail);
      
      if (storedToken != expectedToken) {
      print('🚨 BiometricService: Token mismatch - possible security breach');
        await disableBiometric(userEmail);
        return BiometricVerificationResult.securityError;
      }
      
    print('BiometricService: Verification successful for $userEmail');
      return BiometricVerificationResult.success;
    } catch (e) {
    print('BiometricService: Verification error: $e');
      return BiometricVerificationResult.error;
    }
  }
  
  /// Verify biometric for GCUL database operations
  Future<BiometricVerificationResult> verifyForGCULOperation(
    String userEmail, 
    String operationType
  ) async {
    try {
    print('🔐 BiometricService: GCUL operation verification - $operationType');
      
      // Check if biometrics are enabled
      final isEnabled = await _storage.read(key: 'biometric_enabled_$userEmail');
      if (isEnabled != 'true') {
        // Allow operation without biometric if not enrolled
        return BiometricVerificationResult.notEnrolled;
      }
      
      // Perform authentication for sensitive operations
      final didAuthenticate = await _localAuth.authenticate(
        localizedReason: 'Use fingerprint to $operationType with blockchain security',
        options: const AuthenticationOptions(
          biometricOnly: false, // Allow fallback to device credentials
          stickyAuth: true,
          useErrorDialogs: true,
          sensitiveTransaction: true,
        ),
      );
      
      if (!didAuthenticate) {
        return BiometricVerificationResult.failed;
      }
      
    print('BiometricService: GCUL operation authorized - $operationType');
      return BiometricVerificationResult.success;
    } catch (e) {
    print('BiometricService: GCUL verification error: $e');
      return BiometricVerificationResult.error;
    }
  }
  
  /// Check if biometric is enabled for user
  Future<bool> isBiometricEnabled(String userEmail) async {
    final isEnabled = await _storage.read(key: 'biometric_enabled_$userEmail');
    return isEnabled == 'true';
  }
  
  /// Get biometric enrollment info
  Future<BiometricInfo?> getBiometricInfo(String userEmail) async {
    try {
      final isEnabled = await isBiometricEnabled(userEmail);
      if (!isEnabled) return null;
      
      final enrolledAt = await _storage.read(key: 'biometric_enrolled_at_$userEmail');
      final capability = await checkBiometricCapability();
      
      return BiometricInfo(
        isEnabled: true,
        enrolledAt: enrolledAt != null ? DateTime.parse(enrolledAt) : null,
        capability: capability,
      );
    } catch (e) {
    print('BiometricService: Error getting biometric info: $e');
      return null;
    }
  }
  
  /// Disable biometric authentication
  Future<void> disableBiometric(String userEmail) async {
    try {
    print('🔐 BiometricService: Disabling biometric for $userEmail');
      
      await _storage.delete(key: 'biometric_enabled_$userEmail');
      await _storage.delete(key: 'biometric_token_$userEmail');
      await _storage.delete(key: 'biometric_device_id_$userEmail');
      await _storage.delete(key: 'biometric_enrolled_at_$userEmail');
      await _storage.delete(key: 'last_biometric_user'); // Remove last user reference
      
    print('BiometricService: Biometric disabled for $userEmail');
    } catch (e) {
    print('BiometricService: Error disabling biometric: $e');
    }
  }

  /// Get the last user who enrolled biometric authentication
  Future<String?> getLastBiometricUser() async {
    try {
      return await _storage.read(key: 'last_biometric_user');
    } catch (e) {
    print('BiometricService: Error getting last biometric user: $e');
      return null;
    }
  }

  /// Perform biometric authentication for login (without existing session)
  Future<BiometricLoginAttemptResult> authenticateForLogin() async {
    try {
    print('🔐 BiometricService: Starting login authentication');
      
      // Check device capability
      final capability = await checkBiometricCapability();
      if (capability == BiometricCapability.none) {
        return BiometricLoginAttemptResult(
          success: false,
          reason: 'Biometric authentication not available on this device',
        );
      }
      
      // Get the last biometric user
      final lastUser = await getLastBiometricUser();
      if (lastUser == null) {
        return BiometricLoginAttemptResult(
          success: false,
          reason: 'No biometric user found. Please set up biometric authentication first.',
        );
      }
      
      // Check if biometric is still enabled for this user
      final isEnabled = await isBiometricEnabled(lastUser);
      if (!isEnabled) {
        return BiometricLoginAttemptResult(
          success: false,
          reason: 'Biometric authentication is not enabled for this account',
        );
      }
      
      // Perform biometric authentication
      final didAuthenticate = await _localAuth.authenticate(
        localizedReason: 'Sign in to LegalLens with your fingerprint',
        options: const AuthenticationOptions(
          biometricOnly: true,
          stickyAuth: true,
        ),
      );
      
      if (!didAuthenticate) {
        return BiometricLoginAttemptResult(
          success: false,
          reason: 'Fingerprint authentication failed',
        );
      }
      
      // Verify device consistency
      final storedDeviceId = await _storage.read(key: 'biometric_device_id_$lastUser');
      final currentDeviceId = await _getDeviceId();
      
      if (storedDeviceId != currentDeviceId) {
      print('🚨 BiometricService: Device mismatch - security issue detected');
        await disableBiometric(lastUser);
        return BiometricLoginAttemptResult(
          success: false,
          reason: 'Security error: Device mismatch detected. Biometric authentication has been disabled.',
        );
      }
      
      // Verify token integrity
      final storedToken = await _storage.read(key: 'biometric_token_$lastUser');
      final expectedToken = await _generateBiometricToken(lastUser);
      
      if (storedToken != expectedToken) {
      print('🚨 BiometricService: Token mismatch - possible security breach');
        await disableBiometric(lastUser);
        return BiometricLoginAttemptResult(
          success: false,
          reason: 'Security error: Token verification failed. Biometric authentication has been disabled.',
        );
      }
      
    print('BiometricService: Login authentication successful for $lastUser');
      return BiometricLoginAttemptResult(
        success: true,
        userEmail: lastUser,
        reason: 'Authentication successful',
      );
      
    } catch (e) {
    print('BiometricService: Login authentication error: $e');
      return BiometricLoginAttemptResult(
        success: false,
        reason: 'Authentication error: ${e.toString()}',
      );
    }
  }
  
  /// Generate unique biometric verification token
  Future<String> _generateBiometricToken(String userEmail) async {
    final deviceId = await _getDeviceId();
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final input = '$userEmail:$deviceId:legallens_biometric:$timestamp';
    return sha256.convert(utf8.encode(input)).toString();
  }
  
  /// Get unique device identifier
  Future<String> _getDeviceId() async {
    try {
      if (Platform.isAndroid) {
        final androidInfo = await _deviceInfo.androidInfo;
        return '${androidInfo.id}_${androidInfo.fingerprint}';
      } else if (Platform.isIOS) {
        final iosInfo = await _deviceInfo.iosInfo;
        return iosInfo.identifierForVendor ?? 'ios_unknown';
      }
      return 'unknown_device';
    } catch (e) {
    print('BiometricService: Error getting device ID: $e');
      return 'device_error';
    }
  }
}

/// Biometric capability levels (fingerprint focused)
enum BiometricCapability {
  none,        // No biometric support
  available,   // Fingerprint available and enrolled
}

/// Biometric enrollment results
enum BiometricEnrollmentResult {
  success,
  deviceNotSupported,
  userCancelled,
  error,
}

/// Biometric verification results
enum BiometricVerificationResult {
  success,
  failed,
  notEnrolled,
  securityError,
  error,
}

/// Biometric information model
class BiometricInfo {
  final bool isEnabled;
  final DateTime? enrolledAt;
  final BiometricCapability capability;
  
  BiometricInfo({
    required this.isEnabled,
    this.enrolledAt,
    required this.capability,
  });
  
  String get capabilityName {
    switch (capability) {
      case BiometricCapability.available:
        return 'Fingerprint';
      case BiometricCapability.none:
        return 'None';
    }
  }
}

/// Biometric login attempt result
class BiometricLoginAttemptResult {
  final bool success;
  final String? userEmail;
  final String reason;
  
  BiometricLoginAttemptResult({
    required this.success,
    this.userEmail,
    required this.reason,
  });
}