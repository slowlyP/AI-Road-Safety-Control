import requests
import urllib3
from flask import current_app

# SSL 경고 숨기기
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_its_cctv():
    url = "https://openapi.its.go.kr:9443/cctvInfo"
    api_key = current_app.config.get("ITS_API_KEY")

    params = {
        "apiKey": api_key,
        "type": "ex",
        "cctvType": "2",
        "minX": 127.0,
        "maxX": 127.5,
        "minY": 37.0,
        "maxY": 37.5,
        "getType": "json"
    }

    try:
        r = requests.get(url, params=params, verify=False, timeout=10)
        json_data = r.json()
        
        # 로그에서 확인된 경로: response -> data
        # 'item'이 아니라 'data'라는 키에 리스트가 들어있습니다.
        items = json_data.get('response', {}).get('data', [])

        # 혹시 모르니 기존에 의심했던 'item' 키도 백업으로 체크
        if not items:
            items = json_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])

        print(f"✅ [성공] {len(items)}개의 CCTV 데이터를 가져왔습니다.")
        
        if items:
            print(f"📍 샘플 CCTV 명칭: {items[0].get('cctvname')}")

        return items

    except Exception as e:
        print(f"!!! 에러 발생: {e}")
        return []