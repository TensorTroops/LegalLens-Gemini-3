import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../services/auth_service.dart';
import '../services/biometric_service.dart';

class AuthProvider with ChangeNotifier {
  final AuthService _authService = AuthService();
  final BiometricService _biometricService = BiometricService();
  
  User? _user;
  bool _isLoading = false;
  String? _errorMessage;
  bool _isBiometricEnabled = false;
  bool _biometricForGCUL = true; // Default to true for enhanced security
  BiometricCapability _biometricCapability = BiometricCapability.none;
  BiometricInfo? _biometricInfo;

  User? get user => _user;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated => _user != null;
  bool get isBiometricEnabled => _isBiometricEnabled;
  bool get biometricForGCUL => _biometricForGCUL;
  BiometricCapability get biometricCapability => _biometricCapability;
  BiometricInfo? get biometricInfo => _biometricInfo;

  AuthProvider() {
    // Listen to auth state changes
    _authService.authStateChanges.listen((User? user) {
      _user = user;
      if (user != null) {
        _initializeBiometric();
      } else {
        _resetBiometricState();
      }
      notifyListeners();
    });
  }

  /// Initialize biometric authentication state
  Future<void> _initializeBiometric() async {
    if (_user?.email == null) return;
    
    try {
      _biometricCapability = await _biometricService.checkBiometricCapability();
      _isBiometricEnabled = await _biometricService.isBiometricEnabled(_user!.email!);
      _biometricInfo = await _biometricService.getBiometricInfo(_user!.email!);
      notifyListeners();
    } catch (e) {
    print('❌ AuthProvider: Error initializing biometric: $e');
    }
  }
  
  /// Reset biometric state on logout
  void _resetBiometricState() {
    _isBiometricEnabled = false;
    _biometricCapability = BiometricCapability.none;
    _biometricInfo = null;
  }

  // Sign in with email and password
  Future<bool> signIn(String email, String password) async {
    try {
      _setLoading(true);
      _clearError();
      
      await _authService.signInWithEmailAndPassword(email, password);
      return true;
    } catch (e) {
      _setError(e.toString());
      return false;
    } finally {
      _setLoading(false);
    }
  }

  /// Sign in with biometric authentication
  Future<BiometricLoginResult> signInWithBiometric() async {
    try {
      _setLoading(true);
      _clearError();
      
      // If no user is logged in, try to authenticate using stored biometric data
      if (_user?.email == null) {
        final result = await _biometricService.authenticateForLogin();
        
        if (!result.success) {
          if (result.reason.contains('No biometric user found') || 
              result.reason.contains('not enabled')) {
            return BiometricLoginResult.notEnrolled;
          } else if (result.reason.contains('Security error')) {
            return BiometricLoginResult.securityError;
          } else if (result.reason.contains('authentication failed') || 
                     result.reason.contains('Fingerprint authentication failed')) {
            return BiometricLoginResult.authenticationFailed;
          } else {
            return BiometricLoginResult.error;
          }
        }
        
        // For demo purposes, since we can't sign in without password,
        // let's show a message that guides user to sign in normally first
        // In a production app, you would implement custom token authentication
        return BiometricLoginResult.noUserSession;
      }
      
      final result = await _biometricService.verifyBiometric(_user!.email!);
      
      switch (result) {
        case BiometricVerificationResult.success:
          // Refresh Firebase token to ensure session validity
          await _user!.reload();
          await _initializeBiometric();
          return BiometricLoginResult.success;
        
        case BiometricVerificationResult.failed:
          return BiometricLoginResult.authenticationFailed;
        
        case BiometricVerificationResult.notEnrolled:
          return BiometricLoginResult.notEnrolled;
        
        case BiometricVerificationResult.securityError:
          await _initializeBiometric(); // Refresh state
          return BiometricLoginResult.securityError;
        
        case BiometricVerificationResult.error:
          return BiometricLoginResult.error;
      }
    } catch (e) {
    print('❌ AuthProvider: Biometric login error: $e');
      return BiometricLoginResult.error;
    } finally {
      _setLoading(false);
    }
  }

  /// Enable biometric authentication
  Future<BiometricEnrollmentResult> enableBiometric() async {
    if (_user?.email == null) return BiometricEnrollmentResult.error;
    
    try {
      _setLoading(true);
      final result = await _biometricService.enrollBiometric(_user!.email!);
      
      if (result == BiometricEnrollmentResult.success) {
        await _initializeBiometric();
      }
      
      return result;
    } catch (e) {
    print('❌ AuthProvider: Enable biometric error: $e');
      return BiometricEnrollmentResult.error;
    } finally {
      _setLoading(false);
    }
  }
  
  /// Disable biometric authentication
  Future<void> disableBiometric() async {
    if (_user?.email == null) return;
    
    try {
      _setLoading(true);
      await _biometricService.disableBiometric(_user!.email!);
      await _initializeBiometric();
    } catch (e) {
    print('❌ AuthProvider: Disable biometric error: $e');
    } finally {
      _setLoading(false);
    }
  }

  /// Verify biometric for GCUL operations
  Future<BiometricVerificationResult> verifyBiometricForGCUL(String operationType) async {
    if (_user?.email == null) return BiometricVerificationResult.error;
    
    return await _biometricService.verifyForGCULOperation(_user!.email!, operationType);
  }

  // Sign up
  Future<bool> signUp(String email, String password, String fullName) async {
    try {
      _setLoading(true);
      _clearError();
      
      await _authService.registerWithEmailAndPassword(email, password, fullName);
      return true;
    } catch (e) {
      _setError(e.toString());
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // Reset password
  Future<bool> resetPassword(String email) async {
    try {
      _setLoading(true);
      _clearError();
      
      await _authService.resetPassword(email);
      return true;
    } catch (e) {
      _setError(e.toString());
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // Sign out
  Future<void> signOut() async {
    try {
      _setLoading(true);
      await _authService.signOut();
      // Reset biometric state after logout
      _resetBiometricState();
    } catch (e) {
      _setError(e.toString());
    } finally {
      _setLoading(false);
    }
  }

  // Get ID token for backend requests
  Future<String?> getIdToken() async {
    return await _authService.getIdToken();
  }

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _setError(String error) {
    _errorMessage = error;
    notifyListeners();
  }

  void _clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  void clearError() {
    _clearError();
  }

  void setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  /// Set biometric requirement for GCUL operations
  void setBiometricForGCUL(bool value) {
    _biometricForGCUL = value;
    notifyListeners();
  }
}

/// Biometric login results
enum BiometricLoginResult {
  success,
  authenticationFailed,
  notEnrolled,
  noUserSession,
  securityError,
  error,
}