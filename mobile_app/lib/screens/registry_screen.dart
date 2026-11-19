import 'package:flutter/material.dart';
import '../services/api_service.dart';

class RegistryScreen extends StatefulWidget {
  const RegistryScreen({super.key});

  @override
  State<RegistryScreen> createState() => _RegistryScreenState();
}

class _RegistryScreenState extends State<RegistryScreen> {
  List<dynamic> _cattleList = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchCattle();
  }

  Future<void> _fetchCattle() async {
    setState(() => _isLoading = true);
    try {
      final list = await ApiService.getCattleRegistry();
      setState(() => _cattleList = list);
    } catch (_) {}
    setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF020617),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('Cattle Registry', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _fetchCattle),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF10B981)))
          : _cattleList.isEmpty
              ? const Center(child: Text('No cattle registered yet.', style: TextStyle(color: Colors.white60)))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _cattleList.length,
                  itemBuilder: (context, idx) {
                    final c = _cattleList[idx];
                    final biometrics = (c['biometrics'] as List?) ?? [];
                    return Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0F172A),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFF1E293B)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(c['tag_number'] ?? 'N/A',
                                  style: const TextStyle(
                                      color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: const Color(0xFF064E3B),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(c['status'] ?? 'ACTIVE',
                                    style: const TextStyle(
                                        color: Color(0xFF34D399), fontSize: 11, fontWeight: FontWeight.bold)),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text('Breed: ${c['breed']}', style: const TextStyle(color: Colors.white70, fontSize: 13)),
                          Text('Gender: ${c['gender']}', style: const TextStyle(color: Colors.white70, fontSize: 13)),
                          Text('Biometrics Enrolled: ${biometrics.length} session(s)',
                              style: const TextStyle(color: Color(0xFF34D399), fontSize: 13, fontWeight: FontWeight.bold)),
                        ],
                      ),
                    );
                  },
                ),
    );
  }
}
