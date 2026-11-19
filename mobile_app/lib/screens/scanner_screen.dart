import 'dart:io';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';
import '../widgets/muzzle_reticle.dart';

class ScannerScreen extends StatefulWidget {
  final List<CameraDescription> cameras;

  const ScannerScreen({super.key, required this.cameras});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> with SingleTickerProviderStateMixin {
  CameraController? _cameraController;
  late AnimationController _animController;
  bool _isLoading = false;
  int _selectedCameraIdx = 0;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2200),
    )..repeat(reverse: true);

    _initCamera();
  }

  Future<void> _initCamera() async {
    if (widget.cameras.isEmpty) return;
    _cameraController = CameraController(
      widget.cameras[_selectedCameraIdx],
      ResolutionPreset.high,
      enableAudio: false,
    );

    try {
      await _cameraController!.initialize();
      if (mounted) setState(() {});
    } catch (e) {
      debugPrint('Camera init error: $e');
    }
  }

  Future<void> _captureAndScan() async {
    if (_cameraController == null || !_cameraController!.value.isInitialized) return;

    try {
      setState(() => _isLoading = true);
      final xFile = await _cameraController!.takePicture();
      await _processImage(File(xFile.path));
    } catch (e) {
      _showSnackbar('Capture error: $e');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _pickFromGallery() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery);
    if (picked != null) {
      setState(() => _isLoading = true);
      await _processImage(File(picked.path));
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _processImage(File imageFile) async {
    try {
      final result = await ApiService.identifyCattle(imageFile);
      if (!mounted) return;
      _showResultDialog(result);
    } catch (e) {
      _showSnackbar('Identification failed: $e');
    }
  }

  void _showResultDialog(Map<String, dynamic> result) {
    final bool matched = result['matched'] == true;
    final cattle = result['cattle'];
    final double sim = (result['similarity_score'] as num?)?.toDouble() ?? 0.0;
    final int confPercent = (sim * 100).toInt();

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0F172A),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) {
        return Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    matched ? 'MATCH CONFIRMED' : 'UNKNOWN ANIMAL',
                    style: TextStyle(
                      color: matched ? const Color(0xFF34D399) : const Color(0xFFF43F5E),
                      fontWeight: FontWeight.w900,
                      fontSize: 18,
                    ),
                  ),
                  Text(
                    '$confPercent% Confidence',
                    style: const TextStyle(color: Colors.white70, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (matched && cattle != null) ...[
                Text(
                  'Tag: ${cattle['tag_number']}',
                  style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
                ),
                Text('Breed: ${cattle['breed']}', style: const TextStyle(color: Colors.white70)),
                Text('Gender: ${cattle['gender']}', style: const TextStyle(color: Colors.white70)),
                Text('Policy: ${cattle['insurance_policy_no'] ?? 'N/A'}',
                    style: const TextStyle(color: Color(0xFF34D399))),
              ] else ...[
                const Text(
                  'No cattle in the database matched this biometric muzzle pattern above the 72% confirmation threshold.',
                  style: TextStyle(color: Colors.white70),
                ),
              ],
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF059669),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Done', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  void _showSnackbar(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  void dispose() {
    _animController.dispose();
    _cameraController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF020617),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('CattlePrint Scanner', style: TextStyle(fontWeight: FontWeight.w800)),
        centerTitle: true,
      ),
      body: Stack(
        children: [
          if (_cameraController != null && _cameraController!.value.isInitialized)
            SizedBox.expand(child: CameraPreview(_cameraController!))
          else
            const Center(child: CircularProgressIndicator(color: Color(0xFF10B981))),

          // Reticle
          Center(
            child: SizedBox(
              width: MediaQuery.of(context).size.width * 0.78,
              height: MediaQuery.of(context).size.width * 0.78 * 0.75,
              child: AnimatedBuilder(
                animation: _animController,
                builder: (context, _) => CustomPaint(
                  painter: MuzzleReticlePainter(animationValue: _animController.value),
                ),
              ),
            ),
          ),

          // Bottom Controls
          Positioned(
            bottom: 30,
            left: 20,
            right: 20,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                IconButton(
                  icon: const Icon(Icons.photo_library, color: Colors.white, size: 28),
                  onPressed: _isLoading ? null : _pickFromGallery,
                ),
                GestureDetector(
                  onTap: _isLoading ? null : _captureAndScan,
                  child: Container(
                    width: 76,
                    height: 76,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 4),
                      color: const Color(0xFF10B981),
                    ),
                    child: _isLoading
                        ? const CircularProgressIndicator(color: Colors.white)
                        : const Icon(Icons.camera_alt, color: Colors.white, size: 36),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.flip_camera_ios, color: Colors.white, size: 28),
                  onPressed: () {
                    if (widget.cameras.length > 1) {
                      _selectedCameraIdx = (_selectedCameraIdx + 1) % widget.cameras.length;
                      _initCamera();
                    }
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
