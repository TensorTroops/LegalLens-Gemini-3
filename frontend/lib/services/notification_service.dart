import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:open_file/open_file.dart';
import 'dart:io';

class NotificationService {
  static final FlutterLocalNotificationsPlugin _notifications = 
      FlutterLocalNotificationsPlugin();

  static Future<void> initialize() async {
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    
    const settings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _notifications.initialize(
      settings,
      onDidReceiveNotificationResponse: _onNotificationTapped,
    );

    // Request permissions immediately after initialization
    await requestPermissions();
  }

  /// Handle notification tap - open the PDF file
  static void _onNotificationTapped(NotificationResponse response) async {
  print('🔔 Notification tapped!');
  print('📄 Payload: ${response.payload}');
  print('🆔 Notification ID: ${response.id}');
    
    final filePath = response.payload;
    if (filePath != null && filePath.isNotEmpty) {
    print('📂 Attempting to open file: $filePath');
      final success = await _openPDFFile(filePath);
    print('✅ File open result: $success');
      
      if (!success) {
        // Show a fallback notification if file couldn't be opened
        await showErrorNotification(
          title: 'Could not open PDF',
          message: 'PDF saved but could not be opened automatically. Please check LegalLens folder in file manager.',
        );
      }
    } else {
    print('❌ No file path in notification payload');
    }
  }

  /// Open PDF file using default system app
  static Future<bool> _openPDFFile(String filePath) async {
    try {
    print('🔍 Checking if file exists: $filePath');
      final file = File(filePath);
      final exists = await file.exists();
    print('📁 File exists: $exists');
      
      if (exists) {
      print('🚀 Attempting to open file...');
        
        // Method 1: Try open_file package first (most reliable for mobile)
        try {
        print('🔗 Using open_file package...');
          final result = await OpenFile.open(filePath);
        print('� OpenFile result: ${result.type} - ${result.message}');
          if (result.type == ResultType.done) {
          print('✅ File opened successfully with open_file package');
            return true;
          }
        } catch (e) {
        print('❌ Method 1 (open_file) failed: $e');
        }
        
        // Method 2: Try copying to Downloads folder and opening from there
        if (Platform.isAndroid) {
          try {
          print('🔄 Trying to copy file to Downloads folder...');
            final downloadsDir = Directory('/storage/emulated/0/Download');
            if (await downloadsDir.exists()) {
              final fileName = filePath.split('/').last;
              final newPath = '${downloadsDir.path}/$fileName';
              
              // Copy file to Downloads
              await file.copy(newPath);
            print('📋 File copied to: $newPath');
              
              // Try to open from Downloads
              final result = await OpenFile.open(newPath);
            print('📱 OpenFile (Downloads) result: ${result.type} - ${result.message}');
              if (result.type == ResultType.done) {
              print('✅ File opened successfully from Downloads');
                return true;
              }
            }
          } catch (e) {
          print('❌ Method 2 (copy to Downloads) failed: $e');
          }
        }
        
        // Method 3: Try with file:// URI
        try {
          final uri = Uri.file(filePath);
        print('🔗 File URI: $uri');
          final opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
        print('📱 Method 3 (file URI) result: $opened');
          if (opened) return true;
        } catch (e) {
        print('❌ Method 3 failed: $e');
        }
        
        // Method 4: Try platform default launch
        try {
          final uri = Uri.parse('file://$filePath');
        print('🔗 Direct file URI: $uri');
          final opened = await launchUrl(uri, mode: LaunchMode.platformDefault);
        print('📱 Method 4 (direct URI) result: $opened');
          if (opened) return true;
        } catch (e) {
        print('❌ Method 4 failed: $e');
        }
        
      print('❌ All methods failed to open the file');
        return false;
      } else {
      print('❌ File does not exist at: $filePath');
        return false;
      }
    } catch (e) {
    print('❌ Error opening PDF file: $e');
      return false;
    }
  }

  static Future<void> showDownloadNotification({
    required String fileName,
    required String filePath,
    String? fileSize,
  }) async {
    try {
    print('🔔 Attempting to show download notification for: $fileName');
      
      // Check if we have permission first
      if (Platform.isAndroid) {
        final hasPermission = await Permission.notification.isGranted;
      print('📱 Notification permission granted: $hasPermission');
        
        if (!hasPermission) {
        print('❌ No notification permission, requesting...');
          final granted = await Permission.notification.request();
          if (granted != PermissionStatus.granted) {
          print('❌ Notification permission denied');
            return;
          }
        }
      }

      const androidDetails = AndroidNotificationDetails(
        'download_channel',
        'Downloads',
        channelDescription: 'Notifications for downloaded files',
        importance: Importance.high,
        priority: Priority.high,
        icon: '@mipmap/ic_launcher',
        playSound: true,
        enableVibration: true,
        showWhen: true,
        when: null,
      );

      const iosDetails = DarwinNotificationDetails(
        presentAlert: true,
        presentBadge: true,
        presentSound: true,
      );

      const details = NotificationDetails(
        android: androidDetails,
        iOS: iosDetails,
      );

      String notificationBody = 'PDF "$fileName" saved successfully';
      if (fileSize != null) {
        notificationBody += '\nSize: $fileSize';
      }
      if (Platform.isAndroid) {
        notificationBody += '\nSaved to LegalLens folder';
      } else {
        notificationBody += '\nSaved to Documents';
      }
      notificationBody += '\n👆 Tap to open file';

      final notificationId = DateTime.now().millisecondsSinceEpoch.remainder(100000);
      
    print('🔔 Showing notification with ID: $notificationId');
    print('📄 File path: $filePath');

      await _notifications.show(
        notificationId,
        '📄 Download Complete',
        notificationBody,
        details,
        payload: filePath,
      );
      
    print('✅ Notification shown successfully');

    } catch (e) {
    print('❌ Error showing notification: $e');
      // Don't throw error, just log it since notification is not critical
    }
  }

  static Future<void> showErrorNotification({
    required String title,
    required String message,
  }) async {
    try {
      const androidDetails = AndroidNotificationDetails(
        'error_channel',
        'Error Notifications',
        channelDescription: 'Notifications for errors and failures',
        importance: Importance.high,
        priority: Priority.high,
        icon: '@mipmap/ic_launcher',
        playSound: true,
        enableVibration: true,
      );

      const iosDetails = DarwinNotificationDetails(
        presentAlert: true,
        presentBadge: true,
        presentSound: true,
      );

      const details = NotificationDetails(
        android: androidDetails,
        iOS: iosDetails,
      );

      await _notifications.show(
        DateTime.now().millisecondsSinceEpoch.remainder(100000),
        '❌ $title',
        message,
        details,
      );
    } catch (e) {
    print('Error showing error notification: $e');
    }
  }

  /// Test notification to verify everything works
  static Future<void> testNotification() async {
    try {
    print('🧪 Testing notification system...');
      
      // Check permissions first
      final hasPermission = await requestPermissions();
    print('🔔 Notification permission: $hasPermission');
      
      if (!hasPermission) {
      print('❌ Cannot show test notification - no permission');
        return;
      }

      const androidDetails = AndroidNotificationDetails(
        'test_channel',
        'Test Notifications',
        channelDescription: 'Test notifications to verify the system works',
        importance: Importance.high,
        priority: Priority.high,
        icon: '@mipmap/ic_launcher',
        playSound: true,
        enableVibration: true,
      );

      const iosDetails = DarwinNotificationDetails(
        presentAlert: true,
        presentBadge: true,
        presentSound: true,
      );

      const details = NotificationDetails(
        android: androidDetails,
        iOS: iosDetails,
      );

      await _notifications.show(
        9999,
        '🧪 Test Notification',
        'If you see this, notifications are working correctly!',
        details,
      );
      
    print('✅ Test notification sent');
    } catch (e) {
    print('❌ Test notification failed: $e');
    }
  }
  static Future<bool> requestPermissions() async {
    try {
      if (Platform.isAndroid) {
        // For Android 13+ (API 33+), we need to request POST_NOTIFICATIONS permission
        final status = await Permission.notification.request();
      print('📱 Android notification permission status: $status');
        return status == PermissionStatus.granted;
      } else if (Platform.isIOS) {
        final result = await _notifications
            .resolvePlatformSpecificImplementation<
                IOSFlutterLocalNotificationsPlugin>()
            ?.requestPermissions(
              alert: true,
              badge: true,
              sound: true,
            );
      print('📱 iOS notification permission result: $result');
        return result ?? false;
      }
      return true;
    } catch (e) {
    print('❌ Error requesting notification permissions: $e');
      return false;
    }
  }
}