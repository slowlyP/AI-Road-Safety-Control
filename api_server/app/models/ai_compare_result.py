from app.extensions import db
from sqlalchemy.sql import func


class AiCompareResult(db.Model):
    __tablename__ = "ai_compare_results"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="비교분석 결과 ID"
    )

    compare_run_id = db.Column(
        db.BigInteger,
        db.ForeignKey("ai_compare_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="비교분석 실행 ID"
    )

    model_name = db.Column(
        db.String(100),
        nullable=False,
        index=True,
        comment="모델명"
    )

    optimizer_name = db.Column(
        db.String(50),
        nullable=True,
        comment="옵티마이저명"
    )

    model_version = db.Column(
        db.String(100),
        nullable=True,
        comment="모델 버전 또는 가중치명"
    )

    total_detections = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="총 탐지 수"
    )

    detected_frame_count = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="탐지가 발생한 프레임 수"
    )

    avg_confidence = db.Column(
        db.Numeric(5, 4),
        nullable=True,
        comment="평균 confidence"
    )

    max_confidence = db.Column(
        db.Numeric(5, 4),
        nullable=True,
        comment="최대 confidence"
    )

    processing_time = db.Column(
        db.Numeric(10, 4),
        nullable=True,
        comment="처리 시간(초)"
    )

    best_frame_no = db.Column(
        db.Integer,
        nullable=True,
        comment="대표 프레임 번호"
    )

    best_time_sec = db.Column(
        db.Numeric(10, 2),
        nullable=True,
        comment="대표 프레임 영상 시간(초)"
    )

    best_detection_count = db.Column(
        db.Integer,
        nullable=True,
        comment="대표 프레임 탐지 객체 수"
    )

    best_avg_confidence = db.Column(
        db.Numeric(5, 4),
        nullable=True,
        comment="대표 프레임 평균 confidence"
    )

    best_max_confidence = db.Column(
        db.Numeric(5, 4),
        nullable=True,
        comment="대표 프레임 최대 confidence"
    )

    result_image_path = db.Column(
        db.String(500),
        nullable=True,
        comment="결과 이미지 경로"
    )

    result_json = db.Column(
        db.JSON,
        nullable=True,
        comment="클래스별 탐지 수, bbox 등 상세 결과 JSON"
    )

    status = db.Column(
        db.Enum("대기", "완료", "실패", name="ai_compare_results_status"),
        nullable=False,
        default="대기",
        server_default="대기",
        comment="모델 결과 상태"
    )

    error_message = db.Column(
        db.String(255),
        nullable=True,
        comment="실패 시 오류 메시지"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.now(),
        comment="생성 시간"
    )

    # 관계 설정
    compare_run = db.relationship(
        "AiCompareRun",
        back_populates="results"
    )

    def __repr__(self):
        return (
            f"<AiCompareResult id={self.id} compare_run_id={self.compare_run_id} "
            f"model_name={self.model_name} status={self.status}>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "compare_run_id": self.compare_run_id,
            "model_name": self.model_name,
            "optimizer_name": self.optimizer_name,
            "model_version": self.model_version,
            "total_detections": self.total_detections,
            "detected_frame_count": self.detected_frame_count,
            "avg_confidence": float(self.avg_confidence) if self.avg_confidence is not None else None,
            "max_confidence": float(self.max_confidence) if self.max_confidence is not None else None,
            "processing_time": float(self.processing_time) if self.processing_time is not None else None,
            "best_frame_no": self.best_frame_no,
            "best_time_sec": float(self.best_time_sec) if self.best_time_sec is not None else None,
            "best_detection_count": self.best_detection_count,
            "best_avg_confidence": float(self.best_avg_confidence) if self.best_avg_confidence is not None else None,
            "best_max_confidence": float(self.best_max_confidence) if self.best_max_confidence is not None else None,
            "result_image_path": self.result_image_path,
            "result_json": self.result_json,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }