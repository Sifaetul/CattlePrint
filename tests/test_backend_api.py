"""
End-to-End Integration Tests for CattlePrint FastAPI Backend.
Tests Farm creation, Cattle registration, Muzzle biometric enrollment,
1:N Genuine identification, and Unknown-Animal rejection.
"""

import io
import uuid
import cv2
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.database import init_db
from ml_engine.datasets.downloader import generate_synthetic_muzzle_sample


@pytest.mark.asyncio
async def test_full_biometric_lifecycle():
    await init_db()

    run_id = uuid.uuid4().hex[:6]
    test_phone = f"017{run_id[:8]}"
    test_tag = f"COW-{run_id.upper()}"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/api/v1/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        # 2. Create a Farm
        farm_payload = {
            "name": f"Bismillah Dairy Farm {run_id}",
            "owner_name": "Al-Hajj Abdul Karim",
            "phone": test_phone,
            "district": "Pabna",
            "upazila": "Chatmohar",
        }
        res_farm = await client.post("/api/v1/farms/", json=farm_payload)
        assert res_farm.status_code == 200
        farm_data = res_farm.json()
        farm_id = farm_data["id"]
        assert farm_data["name"] == farm_payload["name"]

        # 3. Register a Cattle Profile
        cattle_payload = {
            "farm_id": farm_id,
            "tag_number": test_tag,
            "breed": "Pabna Breed",
            "gender": "FEMALE",
            "color": "Greyish White",
            "insurance_policy_no": f"PRANI-INS-{run_id}",
            "status": "ACTIVE",
        }
        res_cattle = await client.post("/api/v1/cattle/", json=cattle_payload)
        assert res_cattle.status_code == 200
        cattle_data = res_cattle.json()
        cattle_id = cattle_data["id"]
        assert cattle_data["tag_number"] == test_tag

        # 4. Generate synthetic sharp muzzle for cattle 42 session 0
        muzzle_img_c42_s0 = generate_synthetic_muzzle_sample(cattle_id=42, session=0, size=(250, 250))
        _, encoded_img_c42_s0 = cv2.imencode(".jpg", muzzle_img_c42_s0)
        img_bytes_c42_s0 = encoded_img_c42_s0.tobytes()

        # Quality check endpoint
        res_qc = await client.post(
            "/api/v1/biometrics/quality-check",
            files={"file": ("muzzle_c42.jpg", io.BytesIO(img_bytes_c42_s0), "image/jpeg")},
        )
        assert res_qc.status_code == 200
        qc_data = res_qc.json()
        assert qc_data["is_valid"] is True

        # 5. Register Muzzle Print for COW-PABNA-001
        res_reg = await client.post(
            "/api/v1/biometrics/register-muzzle",
            data={"cattle_id": cattle_id},
            files={"file": ("muzzle_c42_reg.jpg", io.BytesIO(img_bytes_c42_s0), "image/jpeg")},
        )
        assert res_reg.status_code == 200
        reg_data = res_reg.json()
        assert reg_data["success"] is True
        assert reg_data["cattle_id"] == cattle_id

        # 6. Biometric Identification Test: Probe with SAME cattle (Session 1)
        muzzle_img_c42_s1 = generate_synthetic_muzzle_sample(cattle_id=42, session=1, size=(250, 250))
        _, encoded_img_c42_s1 = cv2.imencode(".jpg", muzzle_img_c42_s1)
        img_bytes_c42_s1 = encoded_img_c42_s1.tobytes()

        res_ident = await client.post(
            "/api/v1/biometrics/identify",
            files={"file": ("probe_c42.jpg", io.BytesIO(img_bytes_c42_s1), "image/jpeg")},
        )
        assert res_ident.status_code == 200
        ident_data = res_ident.json()
        # Same cattle pattern must match
        assert ident_data["status"] == "MATCH_CONFIRMED"
        assert ident_data["matched"] is True
        assert ident_data["cattle"]["id"] == cattle_id
        assert ident_data["cattle"]["tag_number"] == test_tag
        assert ident_data["similarity_score"] >= 0.72

        # 7. Biometric Identification Test: Probe with a completely DIFFERENT UNREGISTERED cattle (cattle_id=999)
        muzzle_img_diff = generate_synthetic_muzzle_sample(cattle_id=999, session=0, size=(250, 250))
        _, encoded_img_diff = cv2.imencode(".jpg", muzzle_img_diff)
        img_bytes_diff = encoded_img_diff.tobytes()

        res_diff = await client.post(
            "/api/v1/biometrics/identify",
            files={"file": ("probe_unknown.jpg", io.BytesIO(img_bytes_diff), "image/jpeg")},
        )
        assert res_diff.status_code == 200
        diff_data = res_diff.json()
        # Different muzzle pattern must be rejected or have low score
        assert diff_data["similarity_score"] < ident_data["similarity_score"]
