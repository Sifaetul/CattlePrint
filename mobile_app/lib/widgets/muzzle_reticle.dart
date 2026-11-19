import 'package:flutter/material.dart';

class MuzzleReticlePainter extends CustomPainter {
  final double animationValue;

  MuzzleReticlePainter({required this.animationValue});

  @override
  void paint(Canvas canvas, Size size) {
    final bracketPaint = Paint()
      ..color = const Color(0xFF34D399) // Emerald-400
      ..strokeWidth = 3.5
      ..style = PaintingStyle.stroke;

    final dashPaint = Paint()
      ..color = const Color(0x6634D399)
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;

    const cornerLength = 26.0;
    const radius = 16.0;

    final rect = RRect.fromRectAndRadius(
      Rect.fromLTWH(0, 0, size.width, size.height),
      const Radius.circular(radius),
    );

    // Draw dashed/light outline
    canvas.drawRRect(rect, dashPaint);

    // Top-Left Corner
    final pathTL = Path()
      ..moveTo(0, cornerLength)
      ..lineTo(0, radius)
      ..arcToPoint(const Offset(radius, 0), radius: const Radius.circular(radius))
      ..lineTo(cornerLength, 0);
    canvas.drawPath(pathTL, bracketPaint);

    // Top-Right Corner
    final pathTR = Path()
      ..moveTo(size.width - cornerLength, 0)
      ..lineTo(size.width - radius, 0)
      ..arcToPoint(Offset(size.width, radius), radius: const Radius.circular(radius))
      ..lineTo(size.width, cornerLength);
    canvas.drawPath(pathTR, bracketPaint);

    // Bottom-Left Corner
    final pathBL = Path()
      ..moveTo(0, size.height - cornerLength)
      ..lineTo(0, size.height - radius)
      ..arcToPoint(Offset(radius, size.height), radius: const Radius.circular(radius))
      ..lineTo(cornerLength, size.height);
    canvas.drawPath(pathBL, bracketPaint);

    // Bottom-Right Corner
    final pathBR = Path()
      ..moveTo(size.width - cornerLength, size.height)
      ..lineTo(size.width - radius, size.height)
      ..arcToPoint(Offset(size.width, size.height - radius), radius: const Radius.circular(radius))
      ..lineTo(size.width, size.height - cornerLength);
    canvas.drawPath(pathBR, bracketPaint);

    // Animated Green Laser
    final laserY = size.height * animationValue;
    final laserPaint = Paint()
      ..shader = LinearGradient(
        colors: [
          Colors.transparent,
          const Color(0xFF10B981).withOpacity(0.85),
          Colors.transparent,
        ],
      ).createShader(Rect.fromLTWH(0, laserY - 2, size.width, 4));

    canvas.drawRect(Rect.fromLTWH(4, laserY - 1.5, size.width - 8, 3), laserPaint);
  }

  @override
  bool shouldRepaint(covariant MuzzleReticlePainter oldDelegate) =>
      oldDelegate.animationValue != animationValue;
}
