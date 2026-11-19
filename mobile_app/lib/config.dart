class AppConfig {
  // Update this to your deployed backend IP or domain for production
  // For Android Emulator, use 'http://10.0.2.2:8000/api/v1'
  // For physical phone on same Wi-Fi, use your PC's LAN IP e.g. 'http://192.168.0.105:8000/api/v1'
  static const String apiBaseUrl = 'http://10.0.2.2:8000/api/v1';

  static const double similarityThreshold = 0.72;
}
