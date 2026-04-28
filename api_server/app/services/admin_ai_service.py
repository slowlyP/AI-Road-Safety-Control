from app.repositories.detection_repository import DetectionRepository


class AdminAIService:
    """
    관리자 AI 분석 서비스

    역할
    - AI 탐지 로그 목록 가공
    - AI 탐지 상세 데이터 가공
    - AI 통계 / 차트 데이터 가공
    - AI 요약 대시보드 데이터 생성
    """

    LABEL_NAME_MAP = {
        "box": "박스형",
        "bag": "봉투류",
        "tire": "타이어",
        "rock": "낙석"
    }

    @staticmethod
    def get_detection_list(page=1, per_page=10, label=None, min_conf=None, max_conf=None, status=None):
        """
        AI 탐지 로그 목록 조회
        """
        pagination = DetectionRepository.find_detection_list(
            page=page,
            per_page=per_page,
            label=label,
            min_conf=min_conf,
            max_conf=max_conf,
            status=status
        )

        items = []
        for row in pagination.items:
            items.append({
                "detection_id": row.detection_id,
                "report_id": row.report_id,
                "report_title": row.report_title,
                "detected_label": row.detected_label,
                "detected_label_name": AdminAIService.LABEL_NAME_MAP.get(row.detected_label, row.detected_label or "미분류"),
                "confidence": float(row.confidence) if row.confidence is not None else 0.0,
                "risk_level": row.risk_level,
                "status": row.status,
                "file_type": row.file_type or "-",
                "file_path": row.file_path,
                "detected_at": row.detected_at.strftime("%Y-%m-%d %H:%M") if row.detected_at else "-"
            })

        return {
            "items": items,
            "pagination": pagination
        }

    @staticmethod
    def get_detection_detail(detection_id):
        """
        AI 탐지 상세 조회
        """
        result = DetectionRepository.find_detection_detail(detection_id)

        if not result:
            return None

        detection, report, report_file = result

        return {
            "detection": {
                "id": detection.id,
                "report_id": detection.report_id,
                "file_id": detection.file_id,
                "detected_label": detection.detected_label,
                "detected_label_name": AdminAIService.LABEL_NAME_MAP.get(detection.detected_label, detection.detected_label or "미분류"),
                "confidence": float(detection.confidence) if detection.confidence is not None else 0.0,
                "bbox_x1": detection.bbox_x1,
                "bbox_y1": detection.bbox_y1,
                "bbox_x2": detection.bbox_x2,
                "bbox_y2": detection.bbox_y2,
                "detected_at": detection.detected_at.strftime("%Y-%m-%d %H:%M") if detection.detected_at else "-"
            },
            "report": {
                "id": report.id,
                "title": report.title,
                "content": report.content,
                "report_type": report.report_type,
                "location_text": report.location_text,
                "risk_level": report.risk_level,
                "status": report.status,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M") if report.created_at else "-"
            },
            "file": {
                "id": report_file.id if report_file else None,
                "file_type": report_file.file_type if report_file else None,
                "file_path": report_file.file_path if report_file else None,
                "original_name": report_file.original_name if report_file else None
            } if report_file else None,
            "is_false_positive": report.status == "오탐"
        }

    @staticmethod
    def get_ai_summary(period="30d", file_type="all"):
        """
        상단 KPI 카드용 요약 통계
        """
        total_detections = DetectionRepository.count_all_detections(
            period=period,
            file_type=file_type
        )

        avg_confidence = DetectionRepository.get_average_confidence(
            period=period,
            file_type=file_type
        )

        false_positive_count = DetectionRepository.count_false_positives(
            period=period,
            file_type=file_type
        )

        final_judged_count = DetectionRepository.count_final_judged_reports(
            period=period,
            file_type=file_type
        )

        false_positive_rate = 0.0
        if final_judged_count > 0:
            false_positive_rate = round((false_positive_count / final_judged_count) * 100, 2)

        return {
            "total_detections": total_detections,
            "avg_confidence": round(float(avg_confidence), 2) if avg_confidence is not None else 0.0,
            "false_positive_count": false_positive_count,
            "false_positive_rate": false_positive_rate
        }

    @staticmethod
    def get_file_type_label_statistics(file_type, period="30d"):
        """
        파일 유형별 클래스 통계
        file_type: image / video
        """
        rows = DetectionRepository.get_label_statistics_by_file_type(
            file_type=file_type,
            period=period
        )

        label_order = ["bag", "box", "rock", "tire"]
        count_map = {key: 0 for key in label_order}

        for row in rows:
            if row.detected_label in count_map:
                count_map[row.detected_label] = row.count

        return {
            "labels": [AdminAIService.LABEL_NAME_MAP[key] for key in label_order],
            "counts": [count_map[key] for key in label_order]
        }

    @staticmethod
    def get_monthly_label_statistics(period="30d"):
        """
        월별 클래스 통계
        """
        rows = DetectionRepository.get_monthly_label_statistics(period=period)

        monthly_map = {}

        for row in rows:
            month = str(row.month)
            if month not in monthly_map:
                monthly_map[month] = {
                    "month": month,
                    "bag": 0,
                    "box": 0,
                    "rock": 0,
                    "tire": 0
                }

            if row.detected_label in ["bag", "box", "rock", "tire"]:
                monthly_map[month][row.detected_label] = row.count

        result = list(monthly_map.values())
        result.sort(key=lambda x: x["month"])

        return result

    @staticmethod
    def get_monthly_result_statistics(period="30d"):
        """
        월별 처리완료 / 오탐 추이
        """
        rows = DetectionRepository.get_monthly_result_statistics(period=period)

        result = []
        for row in rows:
            result.append({
                "month": str(row.month),
                "done": row.done_count,
                "false_positive": row.false_positive_count
            })

        return result

    @staticmethod
    def get_confidence_distribution(period="30d", file_type="all"):
        """
        confidence 구간별 분포
        """
        rows = DetectionRepository.get_confidence_distribution(
            period=period,
            file_type=file_type
        )

        range_order = ["0~49", "50~69", "70~84", "85~100"]
        range_map = {key: 0 for key in range_order}

        for row in rows:
            range_map[row.range] = row.count

        return {
            "ranges": list(range_map.keys()),
            "counts": list(range_map.values())
        }

    @staticmethod
    def get_model_metrics():
        """
        모델 성능 지표
        - 현재는 repository에서 최신 1건 조회
        - 없으면 기본값 반환
        """
        metric = DetectionRepository.get_latest_model_metrics()

        if not metric:
            return {
                "accuracy": 0.79,
                "precision": 0.87,
                "recall": 0.75
            }

        return {
            "accuracy": round(float(metric.accuracy), 4) if metric.accuracy is not None else 0.0,
            "precision": round(float(metric.precision), 4) if metric.precision is not None else 0.0,
            "recall": round(float(metric.recall), 4) if metric.recall is not None else 0.0
        }

    @staticmethod
    def get_summary_page_data(period="30d", file_type="all"):
        """
        summary.html 전용 통합 데이터
        """
        summary = AdminAIService.get_ai_summary(
            period=period,
            file_type=file_type
        )

        image_label_stats = AdminAIService.get_file_type_label_statistics(
            file_type="image",
            period=period
        )

        video_label_stats = AdminAIService.get_file_type_label_statistics(
            file_type="video",
            period=period
        )

        monthly_label_stats = AdminAIService.get_monthly_label_statistics(
            period=period
        )

        monthly_result_stats = AdminAIService.get_monthly_result_statistics(
            period=period
        )

        confidence_distribution = AdminAIService.get_confidence_distribution(
            period=period,
            file_type=file_type
        )

        model_metrics = AdminAIService.get_model_metrics()

        return {
            "summary": summary,
            "image_label_stats": image_label_stats,
            "video_label_stats": video_label_stats,
            "monthly_label_stats": monthly_label_stats,
            "monthly_result_stats": monthly_result_stats,
            "confidence_distribution": confidence_distribution,
            "model_metrics": model_metrics
        }