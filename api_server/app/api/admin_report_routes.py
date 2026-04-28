"""
관리자 신고 관리 라우트

이 파일은 관리자 신고 관련 요청을 처리한다.

주요 기능
- GET /admin/reports/ : 관리자 신고 목록 페이지
- GET /admin/reports/<report_id> : 관리자 신고 상세 페이지
- POST /admin/reports/<report_id>/status : 관리자 신고 상태 변경
- POST /admin/reports/<report_id>/compare/run : 비교분석 실행
- GET /admin/reports/<report_id>/compare/history : 비교분석 이력 조회
- GET /admin/reports/compare/<compare_run_id> : 비교분석 상세 조회
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session,jsonify

from app.services.admin_report_service import AdminReportService
from app.services.admin_ai_compare_service import AdminAICompareService
from app.repositories.ai_compare_repository import AiCompareRepository


admin_report_bp = Blueprint(
    "admin_report",
    __name__,
    url_prefix="/admin/reports"
)

admin_report_service = AdminReportService()
admin_ai_compare_service = AdminAICompareService()


def _check_admin():
    """
    관리자 접근 체크
    """
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        flash("관리자만 접근할 수 있습니다.", "danger")
        return redirect(url_for("main.index"))

    return None


@admin_report_bp.route("/", methods=["GET"])
def report_list():
    check = _check_admin()
    if check:
        return check

    page = request.args.get("page", 1, type=int)
    keyword = request.args.get("keyword", "", type=str)
    status = request.args.get("status", "", type=str)
    risk_level = request.args.get("risk_level", "", type=str)
    sort = request.args.get("sort", "", type=str)

    result = admin_report_service.get_report_list(
        page=page,
        per_page=10,
        status=status or None,
        risk_level=risk_level or None,
        keyword=keyword or None,
        sort=sort or None
    )

    return render_template(
        "admin/reports/list.html",
        reports=result["reports"],
        pagination=result["pagination"],
        keyword=keyword,
        status=status,
        risk_level=risk_level,
        sort=sort
    )


@admin_report_bp.route("/<int:report_id>", methods=["GET"])
def report_detail(report_id):
    """
    관리자 신고 상세 페이지
    - 신고 기본 정보
    - 첨부 이미지 / 영상
    - AI 분석 결과
    - 상태 변경 이력
    - 비교분석 이력
    """

    check = _check_admin()
    if check:
        return check

    try:
        report_data = admin_report_service.get_report_detail(report_id)
        compare_runs = admin_ai_compare_service.get_compare_runs_by_report(report_id)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("admin_report.report_list"))

    return render_template(
        "admin/reports/detail.html",
        report=report_data["report"],
        files=report_data.get("files", []),
        status_logs=report_data.get("status_logs", []),
        ai_analysis=report_data.get("ai_analysis"),
        compare_runs=compare_runs
    )


@admin_report_bp.route("/<int:report_id>/status", methods=["POST"])
def update_report_status(report_id):
    """
    관리자 신고 상태 변경
    """

    check = _check_admin()
    if check:
        return check

    new_status = request.form.get("status", "").strip()
    memo = request.form.get("memo", "").strip()
    admin_id = session.get("user_id")

    valid_status = ["접수", "확인중", "처리완료", "오탐"]

    if new_status not in valid_status:
        flash("잘못된 상태 값입니다.", "danger")
        return redirect(url_for("admin_report.report_detail", report_id=report_id))

    try:
        updated = admin_report_service.update_report_status(
            report_id=report_id,
            status=new_status,
            changed_by=admin_id,
            memo=memo
        )

        if updated is None:
            flash("기존 상태와 동일합니다.", "warning")
        else:
            flash("신고 상태가 변경되었습니다.", "success")

    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("admin_report.report_detail", report_id=report_id))


@admin_report_bp.route("/<int:report_id>/compare/run", methods=["POST"])
def run_compare_analysis(report_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "로그인 필요"}), 401

    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "권한 없음"}), 403

    admin_id = session.get("user_id")

    try:
        compare_run = admin_ai_compare_service.run_compare_analysis(
            report_id=report_id,
            requested_by=admin_id
        )

        return jsonify({
            "success": True,
            "compare_run_id": compare_run.id,
            "message": "비교분석이 시작되었습니다."
        })
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"비교분석 중 오류가 발생했습니다: {str(e)}"
        }), 500

@admin_report_bp.route("/<int:report_id>/compare/history", methods=["GET"])
def compare_history(report_id):
    """
    특정 신고의 비교분석 이력 조회
    """

    check = _check_admin()
    if check:
        return check

    try:
        report = admin_ai_compare_service.get_report(report_id)
        if not report:
            raise ValueError("신고 정보를 찾을 수 없습니다.")

        compare_runs = admin_ai_compare_service.get_compare_runs_by_report(report_id)

    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("admin_report.report_list"))

    return render_template(
        "admin/reports/compare_history.html",
        report=report,
        compare_runs=compare_runs
    )

@admin_report_bp.route("/compare/<int:compare_run_id>/status", methods=["GET"])
def compare_status(compare_run_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "로그인 필요"}), 401

    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "권한 없음"}), 403

    compare_run = AiCompareRepository.get_run_by_id(compare_run_id)
    if not compare_run:
        return jsonify({"success": False, "message": "run 없음"}), 404

    results = AiCompareRepository.get_results_by_run(compare_run_id) or []

    total_expected = 3
    done_count = sum(1 for r in results if r.status in ["완료", "실패"])

    models = [
        {
            "model_name": r.model_name,
            "status": r.status,
            "error_message": r.error_message
        }
        for r in results
    ]

    return jsonify({
        "success": True,
        "run_status": compare_run.status,
        "total_count": total_expected,
        "done_count": done_count,
        "models": models
    })

@admin_report_bp.route("/compare/<int:compare_run_id>", methods=["GET"])
def compare_detail(compare_run_id):
    """
    비교분석 상세 조회
    """

    check = _check_admin()
    if check:
        return check

    detail = admin_ai_compare_service.get_compare_run_detail(compare_run_id)

    if not detail:
        flash("비교분석 결과를 찾을 수 없습니다.", "danger")
        return redirect(url_for("admin_report.report_list"))

    compare_run = detail["compare_run"]
    results = detail["results"]
    result_dicts = [r.to_dict() for r in results]

    report = admin_ai_compare_service.get_report(compare_run.report_id)

    return render_template(
        "admin/reports/compare_detail.html",
        report=report,
        compare_run=compare_run,
        results=results,
        result_dicts=result_dicts
    )