import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../config.dart';

class ApiService {
  static final String baseUrl = AppConfig.apiBaseUrl;

  /// 1:N Biometric Identification
  static async identifyCattle(File imageFile) async {
    final uri = Uri.parse('$baseUrl/biometrics/identify');
    final request = http.MultipartRequest('POST', uri);

    request.files.add(await http.MultipartFile.fromPath('file', imageFile.path));

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Identification failed: ${response.body}');
    }
  }

  /// Register new cattle profile & muzzle biometric
  static async registerCattle({
    required String farmId,
    required String tagNumber,
    required String breed,
    required String gender,
    required String color,
    required String insurancePolicy,
    required File imageFile,
  }) async {
    // 1. Create Cattle Profile
    final profileUri = Uri.parse('$baseUrl/cattle/');
    final profileRes = await http.post(
      profileUri,
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'farm_id': farmId,
        'tag_number': tagNumber,
        'breed': breed,
        'gender': gender,
        'color': color,
        'insurance_policy_no': insurancePolicy,
        'status': 'ACTIVE',
      }),
    );

    if (profileRes.statusCode != 200) {
      throw Exception('Profile creation failed: ${profileRes.body}');
    }

    final cattleData = json.decode(profileRes.body);
    final cattleId = cattleData['id'];

    // 2. Upload Muzzle Biometrics
    final bioUri = Uri.parse('$baseUrl/biometrics/register-muzzle');
    final bioReq = http.MultipartRequest('POST', bioUri);
    bioReq.fields['cattle_id'] = cattleId;
    bioReq.files.add(await http.MultipartFile.fromPath('file', imageFile.path));

    final bioStream = await bioReq.send();
    final bioRes = await http.Response.fromStream(bioStream);

    if (bioRes.statusCode != 200) {
      throw Exception('Biometric enrollment failed: ${bioRes.body}');
    }

    return json.decode(bioRes.body);
  }

  /// Fetch list of farms
  static Future<List<dynamic>> getFarms() async {
    final uri = Uri.parse('$baseUrl/farms/');
    final res = await http.get(uri);
    if (res.statusCode == 200) {
      return json.decode(res.body);
    }
    return [];
  }

  /// Fetch cattle registry
  static Future<List<dynamic>> getCattleRegistry() async {
    final uri = Uri.parse('$baseUrl/cattle/');
    final res = await http.get(uri);
    if (res.statusCode == 200) {
      return json.decode(res.body);
    }
    return [];
  }
}
