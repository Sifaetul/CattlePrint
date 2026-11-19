import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _tagCtrl = TextEditingController();
  final _colorCtrl = TextEditingController();
  final _policyCtrl = TextEditingController();
  final _customBreedCtrl = TextEditingController();

  String? _selectedFarmId;
  String _selectedBreed = 'Red Chittagong';
  bool _isCustomBreed = false;
  String _selectedGender = 'FEMALE';
  File? _selectedImage;
  bool _isLoading = false;
  List<dynamic> _farms = [];

  @override
  void initState() {
    super.initState();
    _loadFarms();
  }

  Future<void> _loadFarms() async {
    try {
      final farms = await ApiService.getFarms();
      setState(() {
        _farms = farms;
        if (farms.isNotEmpty) _selectedFarmId = farms[0]['id'];
      });
    } catch (_) {}
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.camera);
    if (picked != null) {
      setState(() => _selectedImage = File(picked.path));
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedFarmId == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please select a farm.')));
      return;
    }
    if (_selectedImage == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please capture a muzzle photo.')));
      return;
    }

    final finalBreed = _isCustomBreed ? _customBreedCtrl.text.trim() : _selectedBreed;
    if (finalBreed.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please specify a breed name.')));
      return;
    }

    setState(() => _isLoading = true);
    try {
      await ApiService.registerCattle(
        farmId: _selectedFarmId!,
        tagNumber: _tagCtrl.text.trim(),
        breed: finalBreed,
        gender: _selectedGender,
        color: _colorCtrl.text.trim(),
        insurancePolicy: _policyCtrl.text.trim(),
        imageFile: _selectedImage!,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Success! Cattle registered with 512D biometric vector.')),
      );
      Navigator.pop(context);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Registration failed: $e')));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF020617),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('Enroll New Cattle', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Farm Dropdown
              const Text('Select Farm', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.bold)),
              const SizedBox(height: 6),
              DropdownButtonFormField<String>(
                value: _selectedFarmId,
                dropdownColor: const Color(0xFF0F172A),
                style: const TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  filled: true,
                  fillColor: const Color(0xFF1E293B),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                items: _farms.map<DropdownMenuItem<String>>((f) {
                  return DropdownMenuItem(value: f['id'].toString(), child: Text(f['name']));
                }).toList(),
                onChanged: (val) => setState(() => _selectedFarmId = val),
              ),
              const SizedBox(height: 16),

              // Tag Number
              TextFormField(
                controller: _tagCtrl,
                style: const TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  labelText: 'Tag / ID Number *',
                  labelStyle: const TextStyle(color: Colors.white60),
                  filled: true,
                  fillColor: const Color(0xFF1E293B),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                validator: (v) => v == null || v.isEmpty ? 'Required' : null,
              ),
              const SizedBox(height: 16),

              // Breed Selection
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Breed Classification', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.bold)),
                  TextButton(
                    onPressed: () => setState(() => _isCustomBreed = !_isCustomBreed),
                    child: Text(_isCustomBreed ? 'Choose from list' : '+ Custom Breed', style: const TextStyle(color: Color(0xFF10B981), fontSize: 12)),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              if (!_isCustomBreed)
                DropdownButtonFormField<String>(
                  value: _selectedBreed,
                  dropdownColor: const Color(0xFF0F172A),
                  style: const TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    filled: true,
                    fillColor: const Color(0xFF1E293B),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  items: [
                    'Red Chittagong',
                    'Pabna Breed',
                    'Shahiwal',
                    'Holstein Friesian Cross',
                    'Local Deshi',
                    'Munshiganj White',
                    'Brahman Cross',
                  ].map((b) => DropdownMenuItem(value: b, child: Text(b))).toList(),
                  onChanged: (val) => setState(() => _selectedBreed = val!),
                )
              else
                TextFormField(
                  controller: _customBreedCtrl,
                  style: const TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    hintText: 'Type custom breed (e.g. Gir / Jersey / Sahiwal-Cross)',
                    hintStyle: const TextStyle(color: Colors.white38),
                    filled: true,
                    fillColor: const Color(0xFF1E293B),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF10B981))),
                  ),
                  validator: (v) => _isCustomBreed && (v == null || v.isEmpty) ? 'Enter breed name' : null,
                ),
              const SizedBox(height: 16),

              // Photo Picker Box
              GestureDetector(
                onTap: _pickImage,
                child: Container(
                  height: 160,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F172A),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFF334155), width: 2),
                  ),
                  child: _selectedImage != null
                      ? ClipRRect(
                          borderRadius: BorderRadius.circular(14),
                          child: Image.file(_selectedImage!, fit: BoxFit.cover),
                        )
                      : const Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.add_a_photo, color: Color(0xFF10B981), size: 40),
                            SizedBox(height: 8),
                            Text('Capture Muzzle Photograph', style: TextStyle(color: Colors.white70)),
                          ],
                        ),
                ),
              ),
              const SizedBox(height: 24),

              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF059669),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  ),
                  onPressed: _isLoading ? null : _submit,
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text('Save & Enroll Biometrics',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
