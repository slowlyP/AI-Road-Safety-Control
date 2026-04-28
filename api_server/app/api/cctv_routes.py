from flask import Blueprint, jsonify
from app.services.its_service import get_its_cctv

cctv_bp = Blueprint(
    "cctv",
    __name__,
    url_prefix="/cctv"
)

@cctv_bp.route("/api/its")
def cctv_its_api():
    """
    Return ITS Highway CCTV data as JSON for the React frontend
    """
    # its_service.py에서 이미 리스트로 가공된 데이터를 가져옵니다.
    items = get_its_cctv()
    
    # items가 이미 리스트이므로 그대로 응답에 넣어주면 됩니다.
    return jsonify({
        "success": True, 
        "items": items,
        "count": len(items) # 개수 정보도 같이 보내주면 프론트에서 쓰기 편합니다.
    })