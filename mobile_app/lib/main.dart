import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'screens/scanner_screen.dart';
import 'screens/register_screen.dart';
import 'screens/registry_screen.dart';

List<CameraDescription> cameras = [];

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    cameras = await availableCameras();
  } catch (e) {
    debugPrint('Available cameras error: $e');
  }
  runApp(const CattlePrintApp());
}

class CattlePrintApp extends StatelessWidget {
  const CattlePrintApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CattlePrint',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF020617),
        primaryColor: const Color(0xFF10B981),
      ),
      home: const MainNavigationScreen(),
    );
  }
}

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    ScannerScreen(cameras: cameras),
    const RegisterScreen(),
    const RegistryScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (idx) => setState(() => _currentIndex = idx),
        backgroundColor: const Color(0xFF0F172A),
        selectedItemColor: const Color(0xFF34D399),
        unselectedItemColor: Colors.white54,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.qr_code_scanner), label: '1:N Scan'),
          BottomNavigationBarItem(icon: Icon(Icons.add_circle_outline), label: 'Register'),
          BottomNavigationBarItem(icon: Icon(Icons.view_list), label: 'Registry'),
        ],
      ),
    );
  }
}
