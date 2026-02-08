import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../screens/login_screen.dart';
import '../screens/home_screen.dart';

class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<User?>(
      stream: FirebaseAuth.instance.authStateChanges(),
      builder: (context, snapshot) {
        // Debug print
      print('AuthGate - Connection state: ${snapshot.connectionState}');
      print('AuthGate - Has data: ${snapshot.hasData}');
      print('AuthGate - User: ${snapshot.data}');
      print('AuthGate - Error: ${snapshot.error}');

        // Show loading while checking auth state
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            backgroundColor: Color(0xFFF5F5F5),
            body: Center(
              child: CircularProgressIndicator(
                valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF4285F4)),
              ),
            ),
          );
        }

        // Check if user is authenticated
        if (snapshot.hasData && snapshot.data != null) {
          // User is signed in, show home screen
        print('AuthGate - Navigating to HomeScreen');
          return const HomeScreen();
        } else {
          // User is not signed in, show login screen
        print('AuthGate - Navigating to LoginScreen');
          return const LoginScreen();
        }
      },
    );
  }
}