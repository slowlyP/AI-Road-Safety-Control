from flask import Blueprint, session, render_template, redirect, url_for, flash, request
from app.services.report_list_service import ReportService
from app.common.response import success_response, error_response
from app.repositories.user_repository import UserRepository

# 신고 목록 관련 블루프린트
report_list_bp = Blueprint("report_list", __name__, url_prefix="/reports")


@report_list_bp.route("/my-page", methods=["GET"])
def my_reports_page():  # 내 신고 목록 페이지 + 사용자 정보 화면 렌더링
    user_id = session.get("user_id")

    # 로그인 안 된 경우 로그인 페이지로 이동
    if not user_id:
        return redirect(url_for("auth.login"))

    db_user = UserRepository.get_user_by_id(user_id)

    # 템플릿에 전달할 사용자 정보 정리
    user = {
        "name": db_user.name,
        "username": db_user.username,
        "email": db_user.email,
        "role": db_user.role,
        "created_at": db_user.created_at
    }

    return render_template("myreport/my_reports.html", user=user)


@report_list_bp.route("/my", methods=["GET"])
def get_my_reports():  # 내 신고 목록 + 상단 통계 + 오늘 탐지 기록 + 전체 지역 목록 조회 API
    try:
        user_id = session.get("user_id")

        # 로그인 체크
        if not user_id:
            return error_response(
                message="로그인이 필요합니다.",
                status_code=401
            )

        # 내 신고 리스트 페이지 정보
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 5, type=int)

        # 오늘 탐지 기록 페이지 정보
        today_page = request.args.get("today_page", 1, type=int)
        today_per_page = request.args.get("today_per_page", 3, type=int)

        # 필터 정보
        keyword = request.args.get("keyword", "", type=str).strip()
        region = request.args.get("region", "", type=str).strip()
        status = request.args.get("status", "", type=str).strip()
        file_type = request.args.get("file_type", "", type=str).strip()
        sort = request.args.get("sort", "latest", type=str).strip()
        start_date = request.args.get("start_date", "", type=str).strip()
        end_date = request.args.get("end_date", "", type=str).strip()

        # 필터 조건 묶음
        filters = {
            "keyword": keyword,
            "region": region,
            "status": status,
            "file_type": file_type,
            "sort": sort,
            "start_date": start_date,
            "end_date": end_date
        }

        # 내 신고 리스트 조회
        paginated_reports = ReportService.get_my_reports_paginated(
            user_id=user_id,
            page=page,
            per_page=per_page,
            filters=filters
        )

        # 상단 요약 카드 조회
        summary = ReportService.get_my_report_summary(
            user_id=user_id,
            filters=filters
        )

        # 오늘 탐지 기록 조회
        today_detect = ReportService.get_today_detect_paginated(
            user_id=user_id,
            page=today_page,
            per_page=today_per_page,
            filters=filters
        )

        # 전체 내 신고 기준 지역 목록 조회
        # 지역 select 박스에 넣을 전체 필터 값
        available_regions = ReportService.get_my_report_regions(
            user_id=user_id
        )

        # 프론트에서 바로 사용할 응답 데이터
        data = {
            "reports": paginated_reports.get("reports", []),
            "pagination": paginated_reports.get("pagination", {}),
            "summary": summary,
            "today_detect": today_detect,
            "available_regions": available_regions,
            "filters": filters
        }

        return success_response(
            message="내 신고 목록 조회 성공",
            data=data,
            status_code=200
        )

    except Exception as e:
        print("🔥 내 신고 목록 조회 에러:", e)
        return error_response(
            message="내 신고 목록 조회 중 서버 오류가 발생했습니다.",
            errors=str(e),
            status_code=500
        )


@report_list_bp.route("/<int:report_id>/page", methods=["GET"])
def my_report_detail_page(report_id):  # 내 신고 상세 페이지 렌더링
    user_id = session.get("user_id")

    # 로그인 안 된 경우 로그인 페이지로 이동
    if not user_id:
        return redirect(url_for("auth.login"))

    report = ReportService.get_my_report_detail(user_id, report_id)

    # 신고가 없으면 목록 페이지로 이동
    if not report:
        return redirect(url_for("report_list.my_reports_page"))

    return render_template(
        "myreport/my_report_detail.html",
        report=report
    )


@report_list_bp.route("/<int:report_id>/edit", methods=["GET"])
def edit_report_page(report_id):  # 내 신고 수정 페이지 렌더링
    user_id = session.get("user_id")

    # 로그인 안 된 경우 로그인 페이지로 이동
    if not user_id:
        return redirect(url_for("auth.login"))

    report = ReportService.get_my_report_detail(user_id, report_id)

    # 신고가 없으면 목록 페이지로 이동
    if not report:
        return redirect(url_for("report_list.my_reports_page"))

    return render_template(
        "myreport/my_report_edit.html",
        report=report
    )


@report_list_bp.route("/<int:report_id>/update", methods=["POST"])
def update_report(report_id):  # 내 신고 수정 요청 처리
    user_id = session.get("user_id")

    # 로그인 안 된 경우 로그인 페이지로 이동
    if not user_id:
        return redirect(url_for("auth.login"))

    try:
        # 수정 폼 데이터 받기
        title = request.form.get("title")
        location_text = request.form.get("location_text")
        content = request.form.get("content")
        new_file = request.files.get("new_file")
        delete_file = request.form.get("delete_file", "N")

        # 서비스에서 수정 처리
        result = ReportService.update_my_report(
            user_id=user_id,
            report_id=report_id,
            title=title,
            location_text=location_text,
            content=content,
            new_file=new_file,
            delete_file=delete_file
        )

        # 서비스 반환값이 tuple일 수도 있으므로 분기 처리
        if isinstance(result, tuple) and len(result) >= 1:
            success = bool(result[0])
            message = result[1] if len(result) >= 2 else ""
        else:
            success = bool(result)
            message = ""

        # 수정 성공 시 상세 페이지로 이동
        if success:
            flash(message or "신고가 수정되었습니다.", "success")
            return redirect(url_for("report_list.my_report_detail_page", report_id=report_id))

        # 수정 실패 시 수정 페이지로 이동
        flash(message or "수정 중 오류가 발생했습니다.", "error")
        return redirect(url_for("report_list.edit_report_page", report_id=report_id))

    except Exception as e:
        print("수정 오류:", e)
        flash("수정 중 오류가 발생했습니다.", "error")
        return redirect(url_for("report_list.edit_report_page", report_id=report_id))


@report_list_bp.route("/<int:report_id>/delete", methods=["POST"])
def delete_report(report_id):  # 내 신고 삭제 요청 처리
    user_id = session.get("user_id")

    # 로그인 안 된 경우 로그인 페이지로 이동
    if not user_id:
        return redirect(url_for("auth.login"))

    try:
        # 서비스에서 삭제 처리
        result = ReportService.delete_my_report(user_id, report_id)

        if result:
            flash("삭제되었습니다.", "success")
        else:
            flash("삭제할 수 없는 신고입니다.", "error")

    except Exception as e:
        print("삭제 오류:", e)
        flash("삭제 중 오류가 발생했습니다.", "error")

    return redirect(url_for("report_list.my_reports_page"))