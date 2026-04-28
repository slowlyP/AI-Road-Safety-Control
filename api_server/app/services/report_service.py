import os
import uuid
import cv2
import logging
import requests
logger = logging.getLogger(__name__)

from datetime import datetime
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Report, ReportFile, Detection, ReportStatusLog
from app.services.yolo_service import detect_image, detect_video



# [기존 추가] 실시간 위험 알림 서비스 import
from app.services.realtime_alert_service import RealtimeAlertService

# [LLM 추가] AI 텍스트 생성 서비스 import
from app.services.llm_service import generate_report_text


LABEL_MAP = {
    0: "bag",
    1: "box",
    2: "rock",
    3: "tire"
}


class ReportService:
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.mp4', '.avi', '.mov'}
    MAX_FILE_SIZE = 50 * 1024 * 1024

    @staticmethod
    def process_report_submission(user_id, form_data, upload_file):
        saved_file_path = None
        try:
            # -------------------------------------------------------
            # [LLM 수정] 사용자가 제목/내용을 비워두는 것을 허용합니다.
            # 빈칸(.strip() == '')이면 처리 로직 하단에서 AI가 채워줍니다.
            # -------------------------------------------------------
            user_title = (form_data.get('title') or '').strip()
            user_content = (form_data.get('content') or '').strip()

            if not upload_file or upload_file.filename == '':
                raise ValueError("첨부된 파일이 없습니다.")

            # -------------------------------------------------------
            # [수정] 원본 파일명은 그대로 보관
            # - 기존: original_name = secure_filename(upload_file.filename)
            # - 문제점:
            #   1) original_name 컬럼에 원본명이 아니라 정제된 이름이 저장됨
            #   2) 한글/특수문자 파일명에서 secure_filename 결과가 비정상적일 수 있음
            # -------------------------------------------------------
            raw_original_name = upload_file.filename

            # -------------------------------------------------------
            # [추가] 안전한 파일명 보조값 생성
            # - 실제 저장 파일명은 uuid로 만들기 때문에 직접 저장용은 아니고
            #   확장자 fallback 확인용으로 사용
            # -------------------------------------------------------
            safe_original_name = secure_filename(raw_original_name)

            # -------------------------------------------------------
            # [수정] 확장자는 원본 파일명 기준으로 먼저 추출
            # - 기존: ext = os.path.splitext(original_name)[1].lower()
            # - 이제는 원본 기준으로 먼저 뽑고,
            #   혹시 없으면 safe_original_name 기준으로 한 번 더 보정
            # -------------------------------------------------------
            ext = os.path.splitext(raw_original_name)[1].lower()

            # -------------------------------------------------------
            # [추가] 확장자 fallback 처리
            # - 원본 파일명에서 확장자가 제대로 안 잡힐 경우 보정
            # -------------------------------------------------------
            if not ext:
                ext = os.path.splitext(safe_original_name)[1].lower()

            # -------------------------------------------------------
            # [추가] 그래도 확장자가 없으면 명확하게 예외 처리
            # -------------------------------------------------------
            if not ext:
                raise ValueError("파일 확장자를 확인할 수 없습니다.")

            if ext not in ReportService.ALLOWED_EXTENSIONS:
                raise ValueError(f"허용되지 않는 파일 형식입니다: {ext}")

            upload_file.seek(0, os.SEEK_END)
            file_size = upload_file.tell()
            upload_file.seek(0)

            if file_size > ReportService.MAX_FILE_SIZE:
                raise ValueError(
                    f"파일 용량은 50MB를 넘을 수 없습니다. "
                    f"(현재: {round(file_size / 1024 / 1024, 2)}MB)"
                )

            inferred_type = '이미지' if ext in {'.jpg', '.jpeg', '.png', '.webp'} else '영상'
            final_report_type = form_data.get('report_type') or inferred_type

            try:
                latitude = float(form_data.get('latitude') or 0.0)
                longitude = float(form_data.get('longitude') or 0.0)
            except (ValueError, TypeError):
                latitude = 0.0
                longitude = 0.0

            # -------------------------------------------------------
            # 기존 Report 생성 로직
            # -------------------------------------------------------
            safe_initial_title = (
                user_title.strip() if user_title and user_title.strip()
                else "도로 낙하물 의심 신고"
            )

            new_report = Report(
                user_id=user_id,
                title=safe_initial_title,  
                content=user_content,
                report_type=final_report_type,
                location_text=form_data.get('location_text') or '위치 정보 없음',
                latitude=latitude,
                longitude=longitude,
                status='접수',
                created_at=datetime.now()
            )
            db.session.add(new_report)
            db.session.flush() # DB ID 발급 완료

            # -------------------------------------------------------
            # 기존 파일 저장 로직
            # - 실제 저장 파일명은 uuid 기반으로 안전하게 생성
            # -------------------------------------------------------
            stored_name = f"{uuid.uuid4().hex}{ext}"
            upload_folder = os.path.join('app', 'static', 'uploads')

            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            file_path = os.path.join(upload_folder, stored_name)
            upload_file.save(file_path)
            saved_file_path = file_path

            # 영상 길이 제한 검사
            if inferred_type == '영상':
                cap = cv2.VideoCapture(file_path)
                if not cap.isOpened():
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    saved_file_path = None
                    raise ValueError("영상 파일을 열 수 없습니다. 손상된 파일인지 확인해주세요.")

                try:
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                finally:
                    cap.release()

                if fps <= 0 or frame_count <= 0:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    saved_file_path = None
                    raise ValueError("영상 메타데이터를 읽을 수 없습니다. 다른 파일로 다시 시도해주세요.")

                duration = frame_count / fps
                if duration > 30:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    saved_file_path = None
                    raise ValueError(
                        f"영상 길이는 30초를 초과할 수 없습니다. "
                        f"(현재: {round(duration, 1)}초)"
                    )

            # -------------------------------------------------------
            # [수정] DB에는 원본 파일명(raw_original_name) 저장
            # - 기존: original_name=original_name (secure_filename 결과값)
            # - 수정: original_name=raw_original_name
            # - 의미:
            #   1) 사용자가 올린 실제 파일명은 original_name에 보관
            #   2) 서버 저장용 안전 파일명은 stored_name으로 별도 관리
            # -------------------------------------------------------
            new_file = ReportFile(
                report_id=new_report.id,
                original_name=raw_original_name,
                stored_name=stored_name,
                file_path=f"static/uploads/{stored_name}",
                file_type=inferred_type,
                file_size=file_size,
                is_active=1,
                uploaded_at=datetime.now()
            )
            db.session.add(new_file)
            db.session.flush()

            # -------------------------------------------------------
            # [기존 추가] commit 이후 소켓 emit에 사용할 결과 저장 변수
            # - 여기서는 alert row 생성 + payload 준비만 하고
            # - 실제 emit은 commit 성공 후에 수행
            # -------------------------------------------------------
            realtime_alert_result = None

            try:
                # 5002번 포트에서 대기 중인 AI 서버 주소
                ai_server_url = "http://localhost:5002/detect" 
                
                # 분석할 파일을 열어서 전송
                with open(file_path, 'rb') as f:
                    files = {'file': (os.path.basename(file_path), f)}
                    # AI 서버에게 POST 요청 발송
                    response = requests.post(ai_server_url, files=files, timeout=30)
                    
                if response.status_code == 200:
                    detections_data = response.json().get('detections', [])
                else:
                    logger.error(f"AI 서버 응답 에러: {response.status_code}")
                    detections_data = []
                    
            except Exception as e:
                logger.error(f"AI 서버 통신 실패: {e}")
                detections_data = []

                old_status = None
                new_status = "접수"
                highest_score = 0
                detected_labels = [] # [LLM 추가] 탐지된 객체 이름을 담을 리스트

                risk_score_map = {
                    "rock": 4,
                    "tire": 3,
                    "box": 2,
                    "bag": 2
                }
                risk_level_names = {
                    4: "긴급",
                    3: "위험",
                    2: "주의",
                    1: "낮음"
                }

                valid_detections = [
                    d for d in (detections_data or [])
                    if d.get('confidence', 0) >= threshold and d.get('class_id') in LABEL_MAP
                ]

                # -------------------------------------------------------
                # [기존 추가] 대표 detection 저장 변수
                # - 여러 detection 중 가장 위험도가 높은 detection 1개를
                #   실시간 알림 대표 detection으로 사용
                # -------------------------------------------------------
                representative_detection = None
                representative_detection_score = 0

                if valid_detections:
                    for d in valid_detections:
                        bbox = d.get('bbox', [0, 0, 0, 0])
                        label = LABEL_MAP[d['class_id']]
                        base_score = risk_score_map.get(label, 1)

                        # LLM에게 전달하기 위해 중복 없이 라벨 수집
                        if label not in detected_labels:
                            detected_labels.append(label)

                        # 면적 가중치
                        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                        if area > (640 * 640 * 0.1):
                            base_score = min(base_score + 1, 4)

                        if base_score > highest_score:
                            highest_score = base_score

                        # -------------------------------------------------------
                        # [기존 수정] Detection 객체를 변수로 만들어 저장
                        # - detection.id 확보가 필요해서 변수화 + flush 처리
                        # -------------------------------------------------------
                        new_detection = Detection(
                            report_id=new_report.id,
                            file_id=new_file.id,
                            detected_label=label,
                            confidence=float(d.get('confidence', 0)),
                            bbox_x1=int(bbox[0]),
                            bbox_y1=int(bbox[1]),
                            bbox_x2=int(bbox[2]),
                            bbox_y2=int(bbox[3]),
                            frame_no=d.get('frame_no'),
                            time_sec=float(d.get('time_sec')) if d.get('time_sec') is not None else None,
                            frame_width=d.get('frame_width'),
                            frame_height=d.get('frame_height'),
                            detected_at=datetime.now(),
                            created_at=datetime.now()
                        )
                        db.session.add(new_detection)

                        # -------------------------------------------------------
                        # [기존 추가] detection.id 확보용 flush
                        # -------------------------------------------------------
                        db.session.flush()

                        # -------------------------------------------------------
                        # [기존 추가] 대표 detection 선정
                        # -------------------------------------------------------
                        if base_score > representative_detection_score:
                            representative_detection_score = base_score
                            representative_detection = new_detection

                    new_report.risk_level = risk_level_names.get(highest_score, "주의")
                    memo = f"AI 분석 결과 {new_report.risk_level} 등급 낙하물 탐지"

                    # -------------------------------------------------------
                    # [기존 추가] 위험 / 긴급일 때만 실시간 알림 생성 준비
                    # - alert row 생성 + payload 준비
                    # - emit은 아직 하지 않음
                    # -------------------------------------------------------
                    if representative_detection and new_report.risk_level in ["위험", "긴급"]:
                        realtime_alert_result = RealtimeAlertService.create_realtime_alert(
                            report=new_report,
                            detection=representative_detection,
                            report_file=new_file
                        )

                else:
                    new_status = "오탐"
                    memo = "AI 분석 결과 낙하물 없음"
                    new_report.risk_level = "낮음"


                # -------------------------------------------------------
                # [LLM 추가] 최종 제목과 내용 결정 (사용자 입력 > AI 생성)
                # -------------------------------------------------------
                # [LLM 개선] User Override + 공백 방어 + 단일 호출 구조
                need_ai = False

                if not user_title or not user_title.strip():
                    need_ai = True

                if not user_content or not user_content.strip():
                    need_ai = True

                if need_ai:
                    # 1. 주소 정보 가져오기 (없으면 기본값 "전방 도로")
                    address = form_data.get('location_text') or "전방 도로"
                    
                    # 2. AI 호출 시 주소(location_address) 인자 추가
                    ai_text = generate_report_text(detected_labels, location_address=address)

                    if not user_title or not user_title.strip():
                        new_report.title = ai_text['title']

                    if not user_content or not user_content.strip():
                        new_report.content = ai_text['content']
                else:
                    new_report.title = user_title.strip()
                    new_report.content = user_content.strip()

                # -------------------------------------------------------
                # 기존 상태 로그 저장 로직
                # -------------------------------------------------------
                
                if old_status != new_status:
                    new_report.status = new_status
                    db.session.add(
                        ReportStatusLog(
                            report_id=new_report.id,
                            old_status=old_status,
                            new_status=new_status,
                            changed_by=user_id,
                            memo=memo,
                            created_at=datetime.now()
                        )
                    )

            except Exception as ai_e:
                # 1. 에러 로그 기록
                logger.error(f"🚨 [ReportService AI Error] {ai_e}")
                
                # 2. 분석 상태를 기본 '접수'로 유지
                new_report.status = "접수"
                
                # 3. [GPT 제안 코드 적용] 사용자가 입력하지 않았다면 기본 문구로 채움
                if not user_title or not user_title.strip():
                    new_report.title = "도로 낙하물 의심 신고 (상세 분석 대기)"
                
                if not user_content or not user_content.strip():
                    new_report.content = "시스템 분석이 지연되어 기본 접수 되었습니다."
                    
                # 4. 에러 상황을 경고 로그로 남김
                logger.warning(f"⚠️ [LLM Fallback 작동] AI 에러로 인해 기본 텍스트가 삽입되었습니다. (user_id: {user_id})")

            # -------------------------------------------------------
            # 기존 DB commit
            # -------------------------------------------------------
            db.session.commit()

            # -------------------------------------------------------
            # [기존 추가] commit 성공 후 emit
            # - DB 저장 성공 이후에만 관리자 화면으로 실시간 알림 전송
            # -------------------------------------------------------
            if realtime_alert_result:
                RealtimeAlertService.emit_realtime_alert(
                    realtime_alert_result["payload"]
                )

            return True

        except ValueError as ve:
            db.session.rollback()
            if saved_file_path and os.path.exists(saved_file_path):
                try:
                    os.remove(saved_file_path)
                except Exception:
                    pass
            raise ve

        except Exception as e:
            db.session.rollback()
            if saved_file_path and os.path.exists(saved_file_path):
                try:
                    os.remove(saved_file_path)
                except Exception:
                    pass
            raise e