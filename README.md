# 프로젝트 트리 완성
현재 프로젝트 진행하기 좋은 상태로 만들어 뒀습니다. <br>
추가 DB가 필요한 경우 꼭! 말씀해주셔야합니다.

---
!! 주의 <br>
DB를 변경할 경우 뼈대도 변동되어 모두 커밋 후 통합 수정을 하고 나서 각자 작업을 해야합니다.

---
### 1. 프로젝트 전체 구조 요약
```
AI-accident-detection/
├── run.py
├── requirements.txt
├── .env
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   │
│   ├── common/
│   │   ├── __init__.py
│   │   ├── response.py
│   │   ├── exceptions.py
│   │   └── decorators.py
│   │
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── schemas/
│   ├── api/
│   ├── templates/
│   └── static/
│
├── storage/
├── ai/
└── migrations/
```
### 2. 백엔드 계층 역할 매칭
- 계층	폴더	역할
- 공통 처리	app/common	응답 포맷, 예외, 데코레이터
- DB 구조	app/models	테이블을 Python 클래스로 정의
- DB 접근	app/repositories	조회/저장/수정/삭제
- 비즈니스 로직	app/services	중복검사, 해시, 권한 판단
- 입력 검증	app/schemas	요청 JSON 검증
- 라우터	app/api	URL 처리, 템플릿 반환, API 응답
### 3. DB 테이블 ↔ 모델 클래스 매칭
- DB 테이블명	모델 파일	클래스명
- users	user_model.py	User
- role_requests	role_request_model.py	RoleRequest
- reports	report_model.py	Report
- report_files	report_file_model.py	ReportFile
- detections	detection_model.py	Detection
- alerts	alert_model.py	Alert
- report_status_logs	report_status_log_model.py	ReportStatusLog
- admin_logs	admin_log_model.py	AdminLog
### 4. DB 테이블별 속성명 정리
#### 4-1. users
**컬럼명	의미**<br>
- id	회원 PK
- username	로그인 아이디
- email	이메일
- password_hash	해시된 비밀번호
- name	이름
- role	권한 (user, admin)
- created_at	생성일
- updated_at	수정일
- deleted_at	삭제일(소프트 삭제)
#### 4-2. role_requests
**컬럼명	의미**<br>
- id	권한 신청 PK
- user_id	신청한 사용자 ID
- request_reason	신청 사유
- status	상태 (대기, 승인, 거절)
- reviewed_by	검토한 관리자 ID
- reviewed_at	검토 시각
- created_at	생성일
#### 4-3. reports
**컬럼명	의미**<br>
- id	신고 PK
- user_id	신고자 ID
- title	신고 제목
- content	신고 내용
- report_type	신고 방식 (이미지, 영상, 카메라)
- location_text	위치 텍스트
- latitude	위도
- longitude	경도
- risk_level	위험도 (낮음, 주의, 위험, 긴급)
- status	처리 상태 (접수, 확인중, 처리완료, 오탐)
- created_at	생성일
- updated_at	수정일
- deleted_at	삭제일
#### 4-4. report_files
**컬럼명	의미**<br>
- id	파일 PK
- report_id	연결된 신고 ID
- original_name	원본 파일명
-stored_name	저장 파일명
- file_path	저장 경로
- file_type	파일 타입 (이미지, 영상)
- file_size	파일 크기
- is_active	활성 여부
- uploaded_at	업로드일
- updated_at	수정일
- deleted_at	삭제일
#### 4-5. detections
**컬럼명	의미**<br>
- id	탐지 PK
- report_id	신고 ID
- file_id	파일 ID
- detected_label	탐지 라벨
- confidence	신뢰도
- bbox_x1	바운딩 박스 X1
- bbox_y1	바운딩 박스 Y1
- bbox_x2	바운딩 박스 X2
- bbox_y2	바운딩 박스 Y2
- detected_at	탐지 시각
- created_at	생성일
#### 4-6. alerts
**컬럼명	의미**<br>
- id	알림 PK
- report_id	신고 ID
- detection_id	탐지 ID
- alert_level	알림 등급 (낮음, 주의, 위험, 긴급)
- message	알림 메시지
- is_read	읽음 여부
- created_at	생성일
- read_at	읽은 시각
#### 4-7. report_status_logs
**컬럼명	의미**<br>
- id	상태 로그 PK
-report_id	신고 ID
- old_status	이전 상태
- new_status	변경 상태
- changed_by	변경한 사용자 ID
- memo	메모
- created_at	생성일
#### 4-8. admin_logs
**컬럼명	의미**<br>
- id	관리자 로그 PK
- admin_user_id	관리자 ID
- action_type	작업 유형
- target_type	대상 종류
- target_id	대상 ID
- action_detail	작업 상세
- created_at	생성일
### 6. 현재 구현한 주요 모델 클래스와 핵심 필드
**User**<br>
- User.id
- User.username
- User.email
- User.password_hash
- User.name
- User.role
- User.created_at
- User.updated_at
- User.deleted_at
**RoleRequest**<br>
- RoleRequest.id
- RoleRequest.user_id
- RoleRequest.request_reason
- RoleRequest.status
- RoleRequest.reviewed_by
- RoleRequest.reviewed_at
- RoleRequest.created_at
### 7. Repository 매칭
**파일	클래스/역할	주요 메서드**<br>
- user_repository.py	사용자 DB 접근	create_user, get_user_by_id, get_user_by_username, get_user_by_email, get_user_by_login_id, exists_by_username, exists_by_email, update_user, soft_delete_user
role_request_repository.py	권한 신청 DB 접근	create_request, get_requests, get_user_request, update_status
### 8. Service 매칭
auth_service.py

**메서드명	역할**

- signup(data)	회원가입 처리
- login(data)	로그인 처리
- get_user_info(user_id)	사용자 정보 조회
- request_admin_role(user_id, reason)	관리자 권한 신청
- update_profile(user_id, data)	내 정보 수정
- delete_account(user_id, password)	회원 탈퇴
### 8. Schema 매칭
- auth_schema.py
- 스키마명	용도	주요 필드
- SignupSchema	회원가입 검증	username, email, password, name
- LoginSchema	로그인 검증	login_id, password
- 회원가입 요청 필드
```
{
  "username": "doha",
  "email": "doha@test.com",
  "password": "1234",
  "name": "김도하"
}
```
- 로그인 요청 필드
```
{
  "login_id": "doha",
  "password": "1234"
}
```
### 9. Auth 라우터 정리
```
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
```
즉 /auth/... 아래로 회원 관련 기능이 연결됨.

```
URL	메서드	엔드포인트명	역할
/auth/login	GET	auth.login	로그인 페이지
/auth/login	POST	auth.login	로그인 처리
/auth/signup	GET	auth.signup	회원가입 페이지
/auth/signup	POST	auth.signup	회원가입 처리
/auth/logout	GET	auth.logout	로그아웃
/auth/mypage	GET	auth.mypage	마이페이지
/auth/role-request	GET	auth.role_request	권한 신청 페이지
/auth/role-request	POST	auth.role_request	권한 신청 처리
/auth/update-profile	GET/POST	auth.update_profile	내 정보 수정
/auth/delete-account	GET/POST	auth.delete_account	회원 탈퇴
```
### 10. Main 라우터 정리
```
main_bp = Blueprint("main", __name__)
```
- URL	메서드	엔드포인트명	역할
- /	GET	main.index	메인페이지
### 11. 현재 템플릿 파일 매칭
```
템플릿 파일	역할	관련 라우터
templates/base.html	공통 레이아웃	전체 페이지
templates/header.html 또는 layout/header.html	공통 헤더	전체 페이지
templates/footer.html 또는 layout/footer.html	공통 푸터	전체 페이지
templates/main/index.html	메인페이지	main.index
templates/auth/login.html	로그인 페이지	auth.login
templates/auth/signup.html	회원가입 페이지	auth.signup
templates/auth/mypage.html	마이페이지	auth.mypage
templates/auth/role_request.html	권한 신청 페이지	auth.role_request
templates/auth/edit_profile.html	내 정보 수정 페이지	auth.update_profile
templates/auth/delete_account.html	회원 탈퇴 페이지	auth.delete_account
```
### 12. 프론트 필드명 ↔ 백엔드 필드명 매칭
```
로그인
화면 input id/name	JS 변수	백엔드 요청 key
login_id	loginId	login_id
password	password	password
```
```
회원가입
화면 input id/name	JS 변수	백엔드 요청 key
username	username	username
email	email	email
password	password	password
name	name	name
```
```
권한 신청
화면 input id/name	JS 변수	백엔드 요청 key
request_reason	reason	request_reason
```
```
내 정보 수정
화면 input id/name	JS 변수	백엔드 요청 key
email	email	email
name	name	name
```
```
회원 탈퇴
화면 input id/name	JS 변수	백엔드 요청 key
password	password	password
```
### 13. 헤더 메뉴 라우터 매칭
```
메뉴명	템플릿 코드	엔드포인트
소개	url_for('main.index') + #intro	main.index
기능	url_for('main.index') + #feature	main.index
기술	url_for('main.index') + #tech	main.index
알림	url_for('main.index') + #alert	main.index
문의	url_for('main.index') + #contact	main.index
탐지 현황	url_for('detection.status')	예정
신고하기	url_for('report.create')	예정
대시보드	url_for('admin.dashboard')	예정
로그인	url_for('auth.login')	구현
회원가입	url_for('auth.signup')	구현
마이페이지	url_for('auth.mypage')	구현
로그아웃	url_for('auth.logout')	구현
```

### 14. 마이페이지 버튼 매칭
```
버튼명	엔드포인트	구현 상태
내 정보 수정	auth.update_profile	구현 진행
내 신고 목록	report.my_reports	미구현
관리자 권한 신청	auth.role_request	구현 진행
회원 탈퇴	auth.delete_account	구현 진행
```
### 15. 세션 저장값 정리
```
로그인 성공 시 저장:

session["user_id"] = user.id
session["username"] = user.username
session["role"] = user.role

템플릿 공통 주입값:

is_logged_in = "user_id" in session
is_admin = session.get("role") == "admin"

즉 Jinja에서는:

{% if is_logged_in %}
{% if is_admin %}

사용 가능.
```

### 16. 공통 응답 포맷
```
성공 응답
{
  "success": true,
  "message": "요청 성공 메시지",
  "data": {}
}
실패 응답
{
  "success": false,
  "message": "에러 메시지",
  "errors": {}
}
```
### 17. 네이밍 규칙 요약
```
DB/백엔드

테이블명: snake_case 복수형
예: role_requests, report_files

컬럼명: snake_case
예: password_hash, created_at, request_reason

Python

모델 클래스: PascalCase
예: User, RoleRequest

함수명/메서드명: snake_case
예: create_user, request_admin_role

프론트

HTML id/name: snake_case 기준 유지
예: login_id, request_reason

JS 변수: camelCase 사용 가능
예: loginId, messageBox
```

