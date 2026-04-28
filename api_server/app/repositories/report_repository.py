from datetime import datetime
from math import ceil
from sqlalchemy import text
from app.models import Report, ReportFile
from app.extensions import db


class ReportRepository:

    @staticmethod
    def find_my_reports(user_id):  # 내 신고 전체 목록 조회
        return Report.query.filter(
            Report.user_id == user_id,
            Report.deleted_at.is_(None)
        ).order_by(Report.created_at.desc()).all()

    @staticmethod
    def find_my_reports_paginated(user_id, page=1, per_page=5):  # 내 신고 목록 페이징 조회
        query = Report.query.filter(
            Report.user_id == user_id,
            Report.deleted_at.is_(None)
        ).order_by(Report.created_at.desc())

        total_count = query.count()
        reports = query.offset((page - 1) * per_page).limit(per_page).all()
        total_pages = ceil(total_count / per_page) if total_count > 0 else 1

        return reports, total_count, total_pages

    @staticmethod
    def find_my_report_detail(user_id, report_id):  # 내 신고 상세 정보와 활성 파일 조회
        report = Report.query.filter(
            Report.id == report_id,
            Report.user_id == user_id,
            Report.deleted_at.is_(None)
        ).first()

        if not report:
            return None, None

        report_file = ReportFile.query.filter_by(
            report_id=report.id,
            is_active=True
        ).order_by(ReportFile.id.desc()).first()

        return report, report_file

    @staticmethod
    def find_active_file_by_report_id(report_id):  # 신고에 연결된 활성 파일 1개 조회
        return ReportFile.query.filter_by(
            report_id=report_id,
            is_active=True
        ).order_by(ReportFile.id.desc()).first()

    @staticmethod
    def create_report_file(report_id, original_name, stored_name, file_path, file_type, file_size):  # 새 첨부파일 레코드 생성
        report_file = ReportFile(
            report_id=report_id,
            original_name=original_name,
            stored_name=stored_name,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            is_active=True
        )
        db.session.add(report_file)
        return report_file

    @staticmethod
    def deactivate_report_file(report_file):  # 기존 첨부파일 비활성화(소프트 삭제)
        if report_file:
            report_file.is_active = False
            report_file.deleted_at = datetime.now()

    @staticmethod
    def has_detection_by_file_id(file_id):  # 파일이 detections 테이블에서 사용 중인지 확인
        sql = text("""
            SELECT COUNT(*) AS cnt
            FROM detections
            WHERE file_id = :file_id
        """)
        result = db.session.execute(sql, {"file_id": file_id}).scalar()
        return result > 0

    @staticmethod
    def delete_report(report):  # 신고 레코드 소프트 삭제
        if report:
            report.deleted_at = datetime.now()

    @staticmethod
    def commit():  # DB 변경사항 저장
        db.session.commit()

    @staticmethod
    def rollback():  # DB 작업 실패 시 롤백
        db.session.rollback()