import os
import cv2
import uuid
from datetime import datetime
from math import ceil
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Report, ReportFile, Detection, ReportStatusLog
from app.repositories.report_repository import ReportRepository
from app.services.yolo_service import detect_image, detect_video

LABEL_MAP = {0: "bag", 1: "box", 2: "rock", 3: "tire"}


class ReportService:
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".avi", ".mov"}
    MAX_FILE_SIZE = 50 * 1024 * 1024

    TODAY_VISIBLE_RISK_LEVELS = {"긴급", "위험", "주의"}
    TODAY_EXCLUDED_STATUSES = {"처리완료", "처리 완료", "오탐"}

    @staticmethod
    def _normalize_risk_label(risk_level):  # 위험도 텍스트 통일
        risk = (risk_level or "").strip()

        if risk == "고위험":
            return "긴급"
        if risk == "저위험":
            return "낮음"

        return risk

    @staticmethod
    def _serialize_report(report):  # 공통 신고 데이터 직렬화
        report_file = ReportRepository.find_active_file_by_report_id(report.id)
        file_type = "일반"

        if report_file and report_file.file_type:
            file_type = report_file.file_type

        return {
            "id": report.id,
            "title": report.title,
            "content": report.content,
            "report_type": report.report_type,
            "location_text": report.location_text,
            "status": report.status,
            "risk_level": ReportService._normalize_risk_label(getattr(report, "risk_level", None)),
            "created_at": report.created_at.strftime("%Y-%m-%d %H:%M") if report.created_at else "-",
            "file_type": file_type
        }

    @staticmethod
    def _safe_lower(value):  # 문자열 소문자 비교용
        return str(value or "").strip().lower()

    @staticmethod
    def _to_datetime(value):  # created_at 문자열을 datetime으로 변환
        if not value or value == "-":
            return None

        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M")
        except ValueError:
            return None

    @staticmethod
    def _risk_sort_score(risk_level):  # 위험도 정렬 우선순위
        risk = ReportService._normalize_risk_label(risk_level)

        score_map = {
            "긴급": 4,
            "위험": 3,
            "주의": 2,
            "낮음": 1
        }
        return score_map.get(risk, 0)

    @staticmethod
    def _status_sort_score(status):  # 상태 정렬 우선순위
        status = (status or "").strip()

        score_map = {
            "접수": 1,
            "확인중": 2,
            "처리완료": 3,
            "처리 완료": 3,
            "오탐": 4
        }
        return score_map.get(status, 99)

    @staticmethod
    def _normalize_region_name(location_text):  # 주소를 지역 필터용 텍스트로 변환
        if not location_text:
            return ""

        text = str(location_text).strip()

        # 공통 국가명 제거
        text = text.replace("대한민국", "").strip()

        # 특별/광역시 이름 짧게 통일
        text = text.replace("서울특별시", "서울시")
        text = text.replace("부산광역시", "부산시")
        text = text.replace("대구광역시", "대구시")
        text = text.replace("인천광역시", "인천시")
        text = text.replace("광주광역시", "광주시")
        text = text.replace("대전광역시", "대전시")
        text = text.replace("울산광역시", "울산시")
        text = text.replace("세종특별자치시", "세종시")

        # 도 이름 정리
        text = text.replace("강원특별자치도", "강원도")
        text = text.replace("제주특별자치도", "제주도")
        text = text.replace("전북특별자치도", "전라북도")

        # 공백 정리
        parts = [part for part in text.split() if part]
        if not parts:
            return ""

        # 서울시/부산시/대구시처럼 시 이름이 앞에 오는 경우
        if parts[0].endswith("시") and len(parts) >= 2 and (parts[1].endswith("구") or parts[1].endswith("군")):
            return f"{parts[0]} {parts[1]}"

        # 경기도 수원시 팔달구 → 수원시 팔달구
        if parts[0].endswith("도") and len(parts) >= 3 and parts[1].endswith("시") and (parts[2].endswith("구") or parts[2].endswith("군")):
            return f"{parts[1]} {parts[2]}"

        # 경기도 수원시 → 수원시
        if parts[0].endswith("도") and len(parts) >= 2 and parts[1].endswith("시"):
            return parts[1]

        # 서울시 중구처럼 2단계 지역
        if len(parts) >= 2:
            return f"{parts[0]} {parts[1]}"

        return parts[0]

    @staticmethod
    def _apply_report_filters(reports, filters=None):  # 검색어/지역/상태/파일유형/날짜 필터 적용
        if not filters:
            return reports

        keyword = ReportService._safe_lower(filters.get("keyword"))
        region = ReportService._safe_lower(filters.get("region"))
        status = (filters.get("status") or "").strip()
        file_type = (filters.get("file_type") or "").strip()
        start_date = (filters.get("start_date") or "").strip()
        end_date = (filters.get("end_date") or "").strip()

        filtered = []

        for report in reports:
            title = ReportService._safe_lower(report.get("title"))
            content = ReportService._safe_lower(report.get("content"))
            location_text = ReportService._safe_lower(report.get("location_text"))
            normalized_region = ReportService._safe_lower(
                ReportService._normalize_region_name(report.get("location_text"))
            )
            report_status = (report.get("status") or "").strip()
            report_file_type = (report.get("file_type") or "").strip()
            created_at = report.get("created_at") or "-"
            created_date = created_at.split(" ")[0] if created_at != "-" else ""

            # 검색어: 제목 + 내용 + 위치 통합 검색
            if keyword:
                searchable_text = f"{title} {content} {location_text}"
                if keyword not in searchable_text:
                    continue

            # 지역: 정규화된 지역명 기준 우선 비교
            if region:
                if region != normalized_region and region not in location_text:
                    continue

            # 상태 필터
            if status and report_status != status:
                continue

            # 파일 유형 필터
            if file_type and report_file_type != file_type:
                continue

            # 시작일 필터
            if start_date and created_date:
                if created_date < start_date:
                    continue

            # 종료일 필터
            if end_date and created_date:
                if created_date > end_date:
                    continue

            filtered.append(report)

        return filtered

    @staticmethod
    def _apply_report_sort(reports, sort="latest"):  # 정렬 기준 적용
        sort = (sort or "latest").strip()

        if sort == "oldest":
            return sorted(
                reports,
                key=lambda item: ReportService._to_datetime(item.get("created_at")) or datetime.min
            )

        if sort == "risk":
            return sorted(
                reports,
                key=lambda item: (
                    -ReportService._risk_sort_score(item.get("risk_level")),
                    -(ReportService._to_datetime(item.get("created_at")) or datetime.min).timestamp()
                )
            )

        if sort == "status":
            return sorted(
                reports,
                key=lambda item: (
                    ReportService._status_sort_score(item.get("status")),
                    -((ReportService._to_datetime(item.get("created_at")) or datetime.min).timestamp())
                )
            )

        # 기본: 최신순
        return sorted(
            reports,
            key=lambda item: ReportService._to_datetime(item.get("created_at")) or datetime.min,
            reverse=True
        )

    @staticmethod
    def _paginate_items(items, page=1, per_page=5):  # 리스트 페이지네이션 공통 처리
        total_count = len(items)
        total_pages = ceil(total_count / per_page) if total_count > 0 else 1

        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages

        start = (page - 1) * per_page
        end = start + per_page
        paginated_items = items[start:end]

        return {
            "items": paginated_items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_prev": page > 1,
                "has_next": page < total_pages
            }
        }

    @staticmethod
    def get_my_reports(user_id):  # 내 신고 전체 목록 조회
        reports = ReportRepository.find_my_reports(user_id)
        if not reports:
            return []

        serialized_reports = [ReportService._serialize_report(report) for report in reports]
        return ReportService._apply_report_sort(serialized_reports, "latest")

    @staticmethod
    def get_my_report_regions(user_id):  # 내 신고 전체 기준 지역 필터 목록 조회
        reports = ReportRepository.find_my_reports(user_id)
        if not reports:
            return []

        region_set = set()

        for report in reports:
            region_name = ReportService._normalize_region_name(report.location_text)
            if region_name:
                region_set.add(region_name)

        return sorted(region_set)

    @staticmethod
    def get_my_reports_paginated(user_id, page=1, per_page=5, filters=None):  # 내 신고 목록 페이징 조회
        reports = ReportRepository.find_my_reports(user_id)
        if not reports:
            return {
                "reports": [],
                "pagination": {
                    "page": 1,
                    "per_page": per_page,
                    "total_count": 0,
                    "total_pages": 1,
                    "has_prev": False,
                    "has_next": False
                }
            }

        serialized_reports = [ReportService._serialize_report(report) for report in reports]

        # 리스트 영역만 필터 적용
        filtered_reports = ReportService._apply_report_filters(serialized_reports, filters)

        # 정렬 적용
        sort = (filters or {}).get("sort", "latest")
        sorted_reports = ReportService._apply_report_sort(filtered_reports, sort)

        # 페이지네이션 적용
        paginated = ReportService._paginate_items(sorted_reports, page, per_page)

        return {
            "reports": paginated["items"],
            "pagination": paginated["pagination"]
        }

    @staticmethod
    def get_my_report_summary(user_id, filters=None):  # 상단 요약 카드용 전체/상태별 건수 조회
        reports = ReportRepository.find_my_reports(user_id)
        if not reports:
            return {
                "total": 0,
                "received": 0,
                "checking": 0,
                "done": 0,
                "false_count": 0
            }

        serialized_reports = [ReportService._serialize_report(report) for report in reports]

        # 상단 요약 카드는 항상 전체 신고 기준으로 계산
        total = len(serialized_reports)
        received = 0
        checking = 0
        done = 0
        false_count = 0

        for report in serialized_reports:
            status = (report.get("status") or "").strip()

            if status == "접수":
                received += 1
            elif status == "확인중":
                checking += 1
            elif status in ["처리완료", "처리 완료"]:
                done += 1
            elif status == "오탐":
                false_count += 1

        return {
            "total": total,
            "received": received,
            "checking": checking,
            "done": done,
            "false_count": false_count
        }

    @staticmethod
    def get_today_detect_paginated(user_id, page=1, per_page=3, filters=None):  # 오늘 탐지 기록 전용 데이터 조회
        reports = ReportRepository.find_my_reports(user_id)
        serialized_reports = [ReportService._serialize_report(report) for report in reports]

        # 오늘 탐지기록은 상태/검색/파일 필터와 상관없이 항상 전체 신고 기준
        filtered_reports = serialized_reports

        today = datetime.now().strftime("%Y-%m-%d")
        today_detect_items = []

        for report in filtered_reports:
            created_at = report.get("created_at") or "-"
            created_date = created_at.split(" ")[0] if created_at != "-" else ""
            status = (report.get("status") or "").strip()
            normalized_risk = ReportService._normalize_risk_label(report.get("risk_level"))

            # 오늘 등록된 신고만 표시
            if created_date != today:
                continue

            # 처리완료 / 오탐 제외
            if status in ReportService.TODAY_EXCLUDED_STATUSES:
                continue

            # 긴급 / 위험 / 주의만 표시
            if normalized_risk not in ReportService.TODAY_VISIBLE_RISK_LEVELS:
                continue

            today_detect_items.append({
                "id": report.get("id"),
                "title": report.get("title") or "-",
                "location_text": report.get("location_text") or "위치 정보 없음",
                "created_at": report.get("created_at") or "-",
                "risk_level": normalized_risk,
                "status": status
            })

        # 오늘 탐지 기록은 항상 최신순
        today_detect_items = sorted(
            today_detect_items,
            key=lambda item: ReportService._to_datetime(item.get("created_at")) or datetime.min,
            reverse=True
        )

        paginated = ReportService._paginate_items(today_detect_items, page, per_page)

        return {
            "items": paginated["items"],
            "pagination": paginated["pagination"]
        }

    @staticmethod
    def get_my_report_detail(user_id, report_id):  # 내 신고 상세 정보 조회
        report, report_file = ReportRepository.find_my_report_detail(user_id, report_id)
        if not report:
            return None

        file_type = None
        file_url = None
        has_detection = False

        if report_file and report_file.file_path:
            file_type = report_file.file_type
            normalized_path = report_file.file_path.replace("\\", "/")
            file_url = "/" + normalized_path if normalized_path.startswith("static/") else "/static/" + normalized_path
            has_detection = ReportRepository.has_detection_by_file_id(report_file.id)

        return {
            "id": report.id,
            "title": report.title,
            "content": report.content,
            "report_type": report.report_type,
            "location_text": report.location_text,
            "status": report.status,
            "risk_level": ReportService._normalize_risk_label(getattr(report, "risk_level", None)),
            "created_at": report.created_at.strftime("%Y-%m-%d %H:%M") if report.created_at else "-",
            "file_type": file_type,
            "file_url": file_url,
            "has_detection": has_detection
        }

    @staticmethod
    def update_my_report(user_id, report_id, title, location_text, content, new_file, delete_file):  # 내 신고 수정 처리
        try:
            report, report_file = ReportRepository.find_my_report_detail(user_id, report_id)
            if not report:
                return False, "해당 신고 내역을 찾을 수 없습니다."

            old_status = report.status
            report.title = (title or "").strip()
            if not report.title:
                return False, "제목은 필수 입력 사항입니다."

            report.location_text = location_text or "위치 정보 없음"
            report.content = content or ""

            is_file_changed = (new_file is not None and new_file.filename.strip() != "")

            original_name = None
            stored_name = None
            save_path = None
            inferred_type = None
            file_size = None

            # 1. 새 파일 저장 및 검증
            if is_file_changed:
                original_name = secure_filename(new_file.filename)
                ext = os.path.splitext(original_name)[1].lower()

                if ext not in ReportService.ALLOWED_EXTENSIONS:
                    return False, "지원하지 않는 파일 형식입니다."

                new_file.seek(0, os.SEEK_END)
                file_size = new_file.tell()
                new_file.seek(0)

                if file_size > ReportService.MAX_FILE_SIZE:
                    return False, "파일 크기는 50MB 이하만 가능합니다."

                inferred_type = "이미지" if ext in {".jpg", ".jpeg", ".png", ".webp"} else "영상"
                stored_name = f"{uuid.uuid4().hex}{ext}"

                upload_dir = os.path.join("app", "static", "uploads")
                os.makedirs(upload_dir, exist_ok=True)

                save_path = os.path.join(upload_dir, stored_name)
                new_file.save(save_path)
                print(f"[DEBUG] 파일 저장 완료: {save_path}")

                if inferred_type == "영상":
                    cap = cv2.VideoCapture(save_path)
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    duration = frame_count / fps if fps > 0 else 0
                    cap.release()

                    if duration > 30:
                        os.remove(save_path)
                        return False, "영상은 30초 이내만 가능합니다."

            # 2. 기존 분석/파일 데이터 정리
            if delete_file == "Y" or is_file_changed:
                old_detections = Detection.query.filter_by(report_id=report.id).all()
                old_ids = [d.id for d in old_detections]

                if old_ids:
                    from sqlalchemy import text
                    db.session.execute(
                        text("DELETE FROM alerts WHERE detection_id IN :ids"),
                        {"ids": tuple(old_ids)}
                    )

                Detection.query.filter_by(report_id=report.id).delete()
                db.session.flush()

                if report_file:
                    old_path = os.path.join("app", "static", report_file.file_path.replace("static/", ""))
                    if os.path.exists(old_path):
                        os.remove(old_path)

                    ReportRepository.deactivate_report_file(report_file)

            # 3. 새 파일 등록 및 AI 재분석
            if is_file_changed:
                report.report_type = inferred_type
                db_file_path = f"static/uploads/{stored_name}"

                new_file_obj = ReportRepository.create_report_file(
                    report_id=report.id,
                    original_name=original_name,
                    stored_name=stored_name,
                    file_path=db_file_path,
                    file_type=inferred_type,
                    file_size=file_size
                )
                db.session.flush()

                try:
                    print(f"[DEBUG] >>> AI 재분석 진입 완료. 경로: {save_path}")

                    detections = detect_image(save_path) if inferred_type == "이미지" else detect_video(save_path)

                    print(f"[DEBUG] >>> AI 분석 종료. 탐지된 물체 수: {len(detections) if detections else 0}")

                    highest_score = 0
                    risk_map = {"rock": 4, "tire": 3, "box": 2, "bag": 2}
                    risk_names = {4: "긴급", 3: "위험", 2: "주의", 1: "낮음"}

                    if detections and len(detections) > 0:
                        print(f"[DEBUG] 탐지 결과 있음: {len(detections)}개")

                        for d in detections:
                            label = LABEL_MAP.get(d.get("class_id"))
                            if label:
                                highest_score = max(highest_score, risk_map.get(label, 1))
                                db.session.add(Detection(
                                    report_id=report.id,
                                    file_id=new_file_obj.id,
                                    detected_label=label,
                                    confidence=float(d.get("confidence", 0)),
                                    bbox_x1=int(d["bbox"][0]),
                                    bbox_y1=int(d["bbox"][1]),
                                    bbox_x2=int(d["bbox"][2]),
                                    bbox_y2=int(d["bbox"][3]),
                                    created_at=datetime.now()
                                ))

                        report.status = "접수"
                        report.risk_level = risk_names.get(highest_score, "주의")
                    else:
                        print("[DEBUG] 탐지 결과 없음 (오탐)")
                        report.status = "오탐"
                        report.risk_level = "낮음"

                    db.session.add(ReportStatusLog(
                        report_id=report.id,
                        old_status=old_status,
                        new_status=report.status,
                        changed_by=user_id,
                        memo="수정 시 파일 교체로 인한 AI 재분석",
                        created_at=datetime.now()
                    ))

                except Exception as ai_e:
                    print(f"🔥 AI 분석 중 오류 발생: {ai_e}")
                    report.status = "분석실패"

            # 4. 최종 저장
            ReportRepository.commit()
            return True, "수정이 완료되었습니다."

        except Exception as e:
            db.session.rollback()
            print(f"🔥 서버 오류: {e}")
            return False, f"서버 오류: {str(e)}"

    @staticmethod
    def delete_my_report(user_id, report_id):  # 내 신고 삭제 처리
        try:
            report, report_file = ReportRepository.find_my_report_detail(user_id, report_id)

            if not report:
                print("[DELETE] 신고 없음")
                return False

            # 1. Detection 삭제
            detections = Detection.query.filter_by(report_id=report.id).all()
            detection_ids = [d.id for d in detections]

            if detection_ids:
                from sqlalchemy import text
                db.session.execute(
                    text("DELETE FROM alerts WHERE detection_id IN :ids"),
                    {"ids": tuple(detection_ids)}
                )

            Detection.query.filter_by(report_id=report.id).delete()
            db.session.flush()

            # 2. 상태 로그 삭제
            ReportStatusLog.query.filter_by(report_id=report.id).delete()
            db.session.flush()

            # 3. 첨부파일 비활성화 및 실제 파일 삭제
            if report_file:
                full_path = os.path.join(
                    "app",
                    "static",
                    report_file.file_path.replace("static/", "")
                )

                if os.path.exists(full_path):
                    os.remove(full_path)

                ReportRepository.deactivate_report_file(report_file)
                db.session.flush()

            # 4. 신고 소프트 삭제
            ReportRepository.delete_report(report)
            ReportRepository.commit()

            print("[DELETE] 삭제 성공:", report_id)
            return True

        except Exception as e:
            db.session.rollback()
            print("[DELETE] 삭제 오류:", e)
            return False